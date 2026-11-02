"""Regression checks using synthetic data, never replacement source data."""

import contextlib
import io
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from split import check_source, main, popularity_baseline, split_plays


class SplitTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = pd.DataFrame({
            "track_id": [f"t{i}" for i in range(60)],
            "track_name": [f"Track {i}" for i in range(60)],
            "artist_name": ["Test artist"] * 60,
            "genre": ["ambient"] * 60,
        })
        self.small = pd.DataFrame({
            "user_id": [1, 1, 1, 2],
            "track_id": ["t0", "t1", "t0", "t2"],
            "played_at": ["2024-05-27", "2024-08-25", "2024-09-08", "2024-09-08"],
        })

    def test_source_screen_rejects_small_file(self):
        lines, passed = check_source(self.small, self.catalogue, [], None)
        self.assertFalse(passed)
        self.assertIn("FAIL: 2,000 distinct listeners", lines)
        self.assertIn("FAIL: All 60 catalogue tracks appear in the play log", lines)

    def test_screen_accepts_matching_counts_but_does_not_authenticate_source(self):
        # Synthetic fixture tests the gate; it is not the missing full log.
        full = pd.DataFrame({
            "user_id": [i % 2000 for i in range(40000)],
            "track_id": [f"t{i % 60}" for i in range(40000)],
            "played_at": ["2024-05-27"] * 39999 + ["2024-09-08"],
        })
        lines, passed = check_source(full, self.catalogue, ["0"], 20)
        self.assertTrue(passed)
        self.assertTrue(any("do not independently authenticate" in line for line in lines))
        _, passed = check_source(full, self.catalogue, ["absent-user"], 21)
        self.assertFalse(passed)

    def test_cutoff_ties_and_listener_without_training(self):
        train, held = split_plays(self.small)
        self.assertEqual(train.index.tolist(), [0])
        self.assertEqual(set(held.index), {1, 2, 3})
        self.assertEqual(len(train) + len(held), len(self.small))

    def test_recall_uses_unique_tracks_and_skips_missing_holdout(self):
        train = pd.DataFrame({"user_id": [1, 2], "track_id": ["t0", "t0"]})
        held = pd.DataFrame({"user_id": [1, 1, 1], "track_id": ["t0", "t0", "t1"]})
        top, recall, coverage = popularity_baseline(train, held, self.catalogue)
        self.assertEqual(top["track_id"].tolist(), ["t0"])
        self.assertEqual(recall, 0.5)
        self.assertEqual(coverage, 1 / 60)

    def test_cli_blocks_metrics_and_requires_explicit_sample_override(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            events, catalogue, output = root / "events.csv", root / "catalogue.csv", root / "output.txt"
            self.small.to_csv(events, index=False)
            self.catalogue.to_csv(catalogue, index=False)
            args = ["--play-log", str(events), "--catalogue", str(catalogue), "--output", str(output)]
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                status = main(args)
            self.assertEqual(status, 1)
            self.assertEqual(output.read_text(), captured.getvalue())
            self.assertIn("Recall@10: NOT COMPUTED", captured.getvalue())
            with contextlib.redirect_stdout(io.StringIO()):
                status = main(args + ["--allow-sample"])
            self.assertEqual(status, 0)
            self.assertIn("EXPLORATORY SAMPLE ONLY", output.read_text())
            self.assertIn("Split boundaries for five listeners", output.read_text())


if __name__ == "__main__":
    unittest.main()
