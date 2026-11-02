# Holdout

I held out **2 weeks out of about 15 weeks**, counted back from each listener's
own last play. I chose 2 weeks to balance enough held-out plays per listener for
evaluation against enough earlier training history to build recommendations.
Holding out fewer weeks would leave fewer evaluation examples; holding out more
weeks would consume more of the already sparse training history.

The two weeks are counted back from each listener's own last play, not a shared
calendar cutoff. Plays at or after `last play - 14 days` are held out; every
earlier play is training data. Rows are never shuffled.

On the available file, the earlier exploratory run produced 56 training plays
and 24 held-out plays across 19 listeners.
All 19 have held-out plays, but 3 have no training history. Thus, two weeks is a
practical compromise, not a guarantee of many evaluation examples per listener;
these small-sample metrics should be interpreted cautiously.

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

- Current status: **the downloaded file fails the resource-description checks**.
  `python split.py` now writes those checks to output.txt, exits with status 1,
  and does not split or score a mismatched file by default. The previous
  19-listener scores are not an accepted full-data baseline for step 2.
- Compared the file against the description, not just another local copy:
  80 rows versus approximately 40,000, 19 listeners versus 2,000, and only 46
  played catalogue tracks versus the stated coverage of all 60. The report
  lists the 14 missing track IDs. The date range matches 15 weeks. The largest
  observed listener history has 9 plays; median is 3, with 90th/95th/99th
  percentiles 7.4/9/9.
- Checked the specific source promise stated in the review: **user_id 100217
  should have 60+ plays across at least 8 distinct tracks**. In the downloaded
  file this listener exists but has **9 plays across 6 distinct tracks**.
  Both the play-count and distinct-track checks FAIL. They run automatically
  before splitting and do not require CLI flags. This directly contradicts
  a checkable promise about the full log; matching local hashes cannot fix it.
  The previous explanation that no named-listener ID/count criterion was
  supplied was incorrect and has been removed from the reports.
- The user clarified that the description refers to niche tastes such as
  phonk and ambient. The input has 9 ambient plays across 6 listeners and no
  tracks labelled phonk in either the catalogue or the play log. The report
  prints play/listener counts by genre. These counts do not by themselves
  establish taste; the explicit 100217 count/breadth promise is tested above.
- A fresh download from Resources has **not** been performed or independently
  verified. Only the existing Desktop attachment and project copy are available
  here. Checked the available browser tabs: all three are GitHub pages; none is
  the task page or its attachment download control. The available file does not substantiate the described full log,
  but these checks alone cannot identify whether the cause is the attachment,
  download, export, or description. Do not label the discrepancy resolved.
- Added source-screening CLI options. To inspect a freshly downloaded file:
  `python split.py --play-log "/path/to/fresh.csv"`. Optional
  `--expected-user-id ID` and `--min-heavy-listener-plays N` check specific
  source claims when their actual values are known. Approximate 40,000 rows is
  reported, not treated as an exact row-count constraint. Passing the available
  checks is not proof that the download is authentic or complete.
- Sample-only diagnostics require explicit opt-in:
  `python split.py --allow-sample --output sample_output.txt`. The output is
  clearly labelled exploratory; it must not be used as the full-data baseline.
  Committed sample_output.txt preserves the earlier date-pair and metric checks
  under that warning; output.txt remains the default source-validation failure.
- Added regression tests: `python -m unittest -v test_split` (6 passing).
  They cover input rejection, synthetic matching counts, named-user and heavy
  listener checks, cutoff ties, unique-track recall, and the CLI sample opt-in.
  The named listener test checks 9 plays/6 tracks, 60/7, 59/8 and the passing
  boundary of 60/8, so play count and breadth are validated independently.
  Synthetic fixtures are test data only, not replacement listening records.
- The brief describes about 2,000 listeners over about 15 weeks, and the review
  expects about 40,000 play rows. The downloaded CSV actually contains 80 data
  rows and 19 distinct listeners over 27 May-8 September 2024 (105 calendar days,
  exactly 15 weeks).
- Source provenance: the user confirms that the file named
  `Spotify play-event log, 2,000 sampled listeners (27 May to 8 Sep 2024).csv`
  was downloaded directly from the task's Resources attachment, not obtained
  from another source or intentionally sampled. The user reports that the
  resource offers a download without a separate source URL. This provenance is
  the user's confirmation; it has not been independently verified against the
  server-side resource or confirmed by the task author.
- On 2 November 2026, checked the downloaded Desktop file directly using Python's
  CSV reader, independently of split.py: 5,836 bytes, 80 data rows, 19 distinct
  user_id values. Its SHA-256 and the renamed script input's SHA-256 are both
  `032f1080f0a8bda633ae4e332e497339157535da3fe2753556f4b87f7f6fd9c8`.
  This proves those two local files are identical; it does not prove that the
  download contains the complete server-side resource.
- Traced the row counts: 80 in the downloaded CSV, 80 immediately after
  pd.read_csv, and 56 training + 24 held-out = 80 after splitting. split.py has
  no sampling, row limit, or filter that drops play rows. Its head(10) selects
  ranked tracks, and head(5) limits only the displayed listener examples.
- The source-size discrepancy remains unresolved. The reported recall and
  coverage describe the supplied 80-row file only, not a verified 2,000-listener
  dataset. Re-running that file cannot evaluate the advertised full log;
  resolving this requires checking the upstream download or obtaining explicit
  clarification from the task author. No additional plays were fabricated.
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
- Earlier exploratory run: overall recall@10 was 0.315789 (31.58%) and catalogue coverage was
  10 / 60 = 0.166667 (16.67%). Independently recomputed the metrics and checked
  deterministic ties and duplicate handling on small examples.
- Defined short histories as at or below the median training play count of 2,
  and long histories as above it. Short: 10 listeners, recall@10 30.00%; long:
  9 listeners, recall@10 33.33%. Both use the same global top 10.
- Matched all 10 recommendations to catalogue genres: 5 pop, 4 rock, 1 ambient.
- Regenerated output.txt as the failed source-validation report; it no longer
  publishes the exploratory scores as an accepted baseline.
