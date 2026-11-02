# Holdout

I held out 2 of about 15 weeks because this balances having enough future plays
per listener to evaluate recommendations against retaining enough earlier history
to train the model. A shorter holdout would give fewer evaluation examples; a
longer holdout would remove more of the already sparse training history.

The two weeks are counted back from each listener's own last play, not a shared
calendar cutoff. Plays at or after `last play - 14 days` are held out; every
earlier play is training data. Rows are never shuffled.

This produces 56 training plays and 24 held-out plays across 19 listeners.
All 19 have held-out plays, but 3 have no training history. Thus, two weeks is a
practical compromise, not a guarantee of many evaluation examples per listener;
these small-sample metrics should be interpreted cautiously.

# Key prompt

> Split each listener's plays by played_at, never by shuffling rows: hold out
> each listener's final 2 weeks, counted back from their own last play, and keep
> every earlier play for training. Count plays per track_id using training plays
> only, take the 10 most-played tracks, and give that same list to every listener.
> Print recall@10 averaged across listeners, the number of listeners without
> held-out plays and their evaluation policy, and catalogue coverage. Check
> chronological separation for every listener, compare recall for short and long
> training histories, list the top-10 genres, and save the full output to output.txt.

# What I checked or changed

- The brief describes about 2,000 listeners over about 15 weeks, but the supplied source CSV contains 80 play rows and 19 distinct listeners across those 15 weeks; its hash matches the script input, and split.py drops no play rows (56 training + 24 held-out = 80).
- Loaded both CSVs into pandas and confirmed the actual data contains 80 play
  events, 19 listeners, 46 played tracks, and 60 catalogue tracks.
- Used separate chronological cutoffs per listener. Checked every listener,
  not just the five printed examples: 16 have both sides of the split and pass
  strict ordering; 3 have no training history and are marked N/A. No held-out
  play is at or before that listener's last training play.
- Verified zero overlapping training/held-out play IDs and zero training plays
  inside their own listener's held-out window. The popularity ranking uses only
  the 56 training events. Ties are broken by track_id ascending. Every listener
  receives the same list, including any tracks already heard in training.
- Calculated recall from unique held-out tracks per listener, then averaged
  those fractions. Duplicate held-out plays count once. Listeners without
  held-out plays are skipped rather than assigned zero; the current count is 0.
- Verified overall recall@10 is 0.315789 (31.58%) and catalogue coverage is
  10 / 60 = 0.166667 (16.67%). Independently recomputed the metrics and checked
  deterministic ties and duplicate handling on small examples.
- Defined short histories as at or below the median training play count of 2,
  and long histories as above it. Short: 10 listeners, recall@10 30.00%; long:
  9 listeners, recall@10 33.33%. Both use the same global top 10.
- Matched all 10 recommendations to catalogue genres: 5 pop, 4 rock, 1 ambient.
- Confirmed output.txt exactly matches the report printed by split.py.
