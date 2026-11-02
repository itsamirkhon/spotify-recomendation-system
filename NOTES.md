# Holdout

I held out **2 weeks out of about 15 weeks**, counted back from each listener's
own last play. Two weeks balances enough held-out plays per listener for
evaluation against enough earlier training history to build recommendations.
A shorter holdout leaves fewer evaluation examples; a longer holdout consumes
more of the sparse training history.

For each listener, plays at or after `last play - 14 days` are held out;
every earlier play is used for training. Rows are never shuffled. The supplied
file yields 56 training plays and 24 held-out plays. All 19 listeners have
held-out plays; 3 have no earlier training history.

# Key prompt for the Claude Code stage

> In split.py, split each listener's plays by played_at, never by shuffling rows:
> hold out each listener's final 2 weeks of plays, counted back from their own
> last play, and keep every earlier play for training. I chose 2 weeks because
> [This preserves most of the history for training and evaluates recommendations
> on future listening events]. Print the row counts of the training and held-out
> sets, then for five listeners print user_id, latest training played_at and
> earliest held-out played_at side by side. Save everything the script prints
> to output.txt.

# What I checked or changed

- **Source discrepancy:** the brief describes about 2,000 listeners and about
  40,000 play rows over 15 weeks, but the supplied CSV contains **80 rows and
  19 distinct listeners**. The same description promises **user_id 100217 has
  60+ plays across at least 8 tracks**; the supplied file instead has **9 plays
  across 6 distinct tracks** for this listener. Both checks run before scoring
  and their failures are printed in output.txt.
- The stage review confirmed that the supplied file also contains 80 rows and
  19 listeners in its own check, and instructed us to finish the baseline on
  that file with the discrepancies documented. The baseline therefore runs
  on the supplied file by default. Resolving the attachment description with
  its owner is outside this evaluation's scope and does not block submission.
- The dates match 27 May-8 September 2024: 105 calendar days, exactly 15 weeks.
  The log plays 46 of the 60 catalogue tracks, rather than all 60 described;
  output.txt lists the 14 missing IDs. The largest history has 9 plays and the
  median has 3. Ambient has 9 plays across 6 listeners. No supplied catalogue
  tracks are labelled phonk. Genre counts alone do not define listener taste.
- The user confirms downloading the original named CSV directly from Resources
  without intentional sampling. Its 5,836 bytes have SHA-256
  `032f1080f0a8bda633ae4e332e497339157535da3fe2753556f4b87f7f6fd9c8`,
  identical to the renamed script input. This proves local file identity, not
  server-side completeness. No fresh download or data-owner confirmation is
  claimed, and the cause of the description mismatch remains unresolved.
- Traced all 80 rows from the raw CSV through pandas into 56 training plus
  24 held-out rows. No sampling, read limit, or row-dropping filter is used.
- Checked all 19 listeners: no held-out play is at or before that listener's
  last training play. Sixteen have both parts and pass strict ordering; three
  have no training history and are marked N/A. Training and held-out play IDs
  do not overlap. The report also prints five date pairs side by side.
- Ranked tracks using training play-event counts only, breaking ties by track_id
  ascending. Every listener receives the same top 10, including tracks already
  heard during training. No held-out plays contribute to popularity counts.
- Recall@10 uses unique held-out tracks per listener, then averages the fractions.
  Repeats count once. Listeners without held-out plays are skipped, not counted
  as zero; there are 0 such listeners. Recall@10 is **0.315789 (31.58%)**.
- Catalogue coverage is distinct recommended tracks divided by catalogue rows:
  **10 / 60 = 0.166667 (16.67%)**. These scores describe the supplied 19-listener
  dataset, not an evaluation of a verified 2,000-listener log. Later models
  should use the same supplied file and split for a comparable baseline.
- Short histories are at or below the median training play count of 2:
  10 listeners, recall@10 30.00%. Long histories are above 2: 9 listeners,
  recall@10 33.33%. Both groups receive the same global top 10. The recommended
  genres are 5 pop, 4 rock, and 1 ambient, listed per track in output.txt.
- Run `python split.py` to regenerate the full printed report in output.txt.
  Description mismatches are reported but do not stop this supplied-file run.
  Optional `--strict-source` retains fail-on-mismatch checking. Additional
  `--play-log`, `--catalogue`, and `--output` options accept other input paths.
- All 6 regression tests pass (`python -m unittest -v test_split`), covering
  count/breadth boundaries, source screening, cutoff ties, unique-track recall,
  normal scoring with documented mismatches, and optional strict rejection.
  Synthetic fixtures are tests only; no listening records were fabricated.
- Confirmed that committed output.txt exactly matches stdout from the default
  run, including counts, dates, source checks, top 10, metrics, and genres.
