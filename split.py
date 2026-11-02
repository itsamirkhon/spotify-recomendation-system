"""Inspect Spotify data and hold out each listener's final two weeks."""

from pathlib import Path

import pandas as pd


def split_plays(play_events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Hold out [last play - 14 days, last play] for each listener."""
    events = play_events.copy()
    events["played_at"] = pd.to_datetime(events["played_at"], errors="raise")
    if events[["user_id", "played_at"]].isna().any().any():
        raise ValueError("Every play must have a user_id and played_at.")

    last_play = events.groupby("user_id")["played_at"].transform("max")
    cutoff = last_play - pd.Timedelta(14, unit="D")
    held_out_mask = events["played_at"] >= cutoff
    training = events.loc[~held_out_mask].sort_values(["user_id", "played_at"])
    held_out = events.loc[held_out_mask].sort_values(["user_id", "played_at"])
    return training, held_out


def listener_recalls(recommended: set, held_out: pd.DataFrame) -> pd.Series:
    """Return recall for each listener with at least one held-out play."""
    relevant = held_out.groupby("user_id")["track_id"].agg(set)
    return relevant.map(lambda tracks: len(recommended & tracks) / len(tracks))


def popularity_baseline(
    training: pd.DataFrame, held_out: pd.DataFrame, track_catalogue: pd.DataFrame
) -> tuple[pd.DataFrame, float, float]:
    """Rank by training play count; evaluate unique held-out tracks per listener."""
    top_tracks = (
        training.groupby("track_id").size().rename("training_plays").reset_index()
        .sort_values(["training_plays", "track_id"], ascending=[False, True])
        .head(10)
        .reset_index(drop=True)
    )
    recommended = set(top_tracks["track_id"])
    catalogue_ids = set(track_catalogue["track_id"].dropna())
    if not recommended <= catalogue_ids:
        raise ValueError("Recommended tracks must exist in the catalogue.")

    # Every listener gets this same list, including tracks heard during training.
    recalls = listener_recalls(recommended, held_out)
    recall_at_10 = float(recalls.mean()) if len(recalls) else 0.0
    coverage = len(recommended) / len(track_catalogue) if len(track_catalogue) else 0.0
    return top_tracks, recall_at_10, coverage


def main() -> None:
    data_dir = Path(__file__).resolve().parent
    play_events = pd.read_csv(
        data_dir / "spotify_play_events_2024-05-27_to_2024-09-08.csv"
    )
    track_catalogue = pd.read_csv(data_dir / "spotify_track_catalogue_2024-09.csv")

    training, held_out = split_plays(play_events)
    listeners_without_holdout = len(
        set(play_events["user_id"]) - set(held_out["user_id"])
    )
    top_tracks, recall_at_10, coverage = popularity_baseline(
        training, held_out, track_catalogue
    )
    top_tracks = top_tracks.merge(
        track_catalogue[["track_id", "track_name", "artist_name"]],
        on="track_id", how="left", validate="one_to_one", sort=False,
    )
    boundaries = pd.concat(
        [
            training.groupby("user_id")["played_at"].max().rename("latest_training_played_at"),
            held_out.groupby("user_id")["played_at"].min().rename("earliest_held_out_played_at"),
        ],
        axis=1,
    ).sort_index()
    both = boundaries.dropna()
    if not (both["latest_training_played_at"] < both["earliest_held_out_played_at"]).all():
        raise ValueError("Training plays must precede held-out plays for every listener.")

    boundaries["check"] = "PASS"
    boundaries.loc[boundaries["latest_training_played_at"].isna(), "check"] = "N/A: no training plays"
    boundaries.loc[boundaries["earliest_held_out_played_at"].isna(), "check"] = "N/A: no held-out plays"
    last_training = held_out["user_id"].map(boundaries["latest_training_played_at"])
    violations = int((held_out["played_at"] <= last_training).sum())
    if violations:
        raise ValueError(f"Found {violations} held-out plays at or before last training play.")

    # Cohorts use only the history available to the model, including zero-play users.
    history_lengths = training.groupby("user_id").size().reindex(boundaries.index, fill_value=0)
    median_history = float(history_lengths.median())
    per_listener = listener_recalls(set(top_tracks["track_id"]), held_out)
    cohort_lines = []
    for label, mask in [("Short", history_lengths <= median_history),
                        ("Long", history_lengths > median_history)]:
        user_ids = history_lengths.index[mask]
        recalls = per_listener.loc[per_listener.index.isin(user_ids)]
        score = f"{recalls.mean():.6f} ({recalls.mean():.2%})" if len(recalls) else "N/A"
        cohort_lines.append(
            f"{label} histories: {len(user_ids)} listeners; {len(recalls)} evaluated; Recall@10: {score}"
        )
    genres = top_tracks[["track_id", "track_name"]].merge(
        track_catalogue[["track_id", "genre"]], on="track_id", validate="one_to_one", sort=False
    )

    report = "\n".join(
        [
            f"Play log rows: {len(play_events)}",
            f"Catalogue rows: {len(track_catalogue)}",
            f"Distinct users in play log: {play_events['user_id'].nunique()}",
            f"Distinct tracks in play log: {play_events['track_id'].nunique()}",
            f"Tracks in catalogue (distinct track_id): {track_catalogue['track_id'].nunique()}",
            "",
            "Holdout: each listener's final 2 weeks, counted back from their own last play.",
            "Reason: This preserves most of the history for training and evaluates "
            "recommendations on future listening events.",
            "Training: played_at < last play - 14 days; held-out: played_at >= cutoff.",
            f"Training rows: {len(training)}",
            f"Held-out rows: {len(held_out)}",
            "",
            "Split boundaries for five listeners (NaT means no training history):",
            boundaries.drop(columns="check").head(5).reset_index().to_string(index=False),
            "",
            "Popularity baseline: same top 10 training tracks for every listener.",
            "Ranked by play-event count; ties broken by track_id ascending.",
            top_tracks.to_string(index=False),
            "",
            "Recall@10: mean per-listener fraction of unique held-out tracks recommended.",
            f"Listeners with no held-out plays: {listeners_without_holdout}",
            "Recall policy: skip listeners with no held-out plays; do not count them as zero.",
            f"Evaluated listeners: {held_out['user_id'].nunique()}",
            f"Recall@10: {recall_at_10:.6f} ({recall_at_10:.2%})",
            "Catalogue coverage: distinct tracks in at least one shortlist / catalogue rows.",
            f"Catalogue coverage: {coverage:.6f} ({coverage:.2%})",
            "",
            "Chronological check for every listener:",
            boundaries.reset_index().to_string(index=False),
            f"PASS: checked all {len(boundaries)} listeners; {len(both)} have both training and held-out plays.",
            f"Held-out plays at or before their listener's last training play: {violations}",
            "N/A rows have no pair of training/held-out boundaries to compare.",
            "",
            f"History cohorts use training play counts; median across all listeners: {median_history:g}.",
            f"Short: <= {median_history:g} training plays; long: > {median_history:g} training plays.",
            "Both cohorts use the same global top 10; listeners without holdout are skipped.",
            *cohort_lines,
            "",
            "Genres of the 10 recommended tracks:",
            genres.to_string(index=False),
        ]
    )
    (data_dir / "output.txt").write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
