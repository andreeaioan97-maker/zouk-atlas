# Monthly 2027 check

Instructions for the scheduled Orca automation (Claude). Goal: keep
the festival database (`data/zouk_atlas.db`) current with newly announced 2027 European
zouk festival dates.

1. `git checkout main` and `git pull --ff-only`. Work and commit on `main`
   (the old `data/2027-festival-list` branch is no longer used). Never force-push.
2. Run `python3 -I scripts/check_2027.py --out reports/raw/$(date +%Y-%m)`.
   It takes about 20 minutes and drives Orca's browser slowly. Don't interrupt it.
   - Exit code 2 means a login is missing. Write `reports/$(date +%Y-%m).md` saying
     which login, so the user knows to log in again in this workspace's Orca browser tab.
     Commit that, push it (step 7) and stop. Skip step 8.
3. Read `reports/raw/<month>/report.md`. For each lead:
   - **Instagram**: record a 2027 edition only when the organizer states the dates
     (bio, caption, or flyer). If a date is only on a flyer image, open the post and
     screenshot it to read it. Watch for typos: a post published in 2026 that says
     "2027" for an event the bio dates to 2026 is not a 2027 announcement.
   - **DJ Mesmes "NEW?" items**: add only festivals, marathons, congresses and
     dance holidays. Skip workshops, bootcamps, teacher trainings and weekenders
     with named teachers (same rule as the base list). Skip events outside Europe.
     Open the event's Facebook link to confirm the dates before adding it.
4. Update the database `data/zouk_atlas.db` with `scripts/atlas.py` (never edit
   `data/festivals.json` or `.csv` by hand; they are exports and get overwritten):
   - new 2027 dates: `python3 -I scripts/atlas.py set-edition ID 2027 --start YYYY-MM-DD --end YYYY-MM-DD --source URL --confirmed`
     (`--confirmed` only when the organizer states them; this also sets the 2027 status to "listed")
   - notes: `python3 -I scripts/atlas.py set-note ID 2027 "TEXT"`
   - other status changes: `python3 -I scripts/atlas.py set-status ID 2027 "STATUS" [--note "TEXT"]`
   - new series: `python3 -I scripts/atlas.py add-series --id ID --name ... --city ... --country ... --style bz|bz+lambada|lambada|mixed|bachazouk [--website/--instagram/--facebook-page/--facebook-event URL]`
   - set `last_checked` to today on every series you checked (the IDs in `reports/raw/<month>/instagram.json`):
     `python3 -I scripts/atlas.py touch ID [ID ...]`
   - `python3 -I scripts/atlas.py show ID` prints a record; `python3 -I scripts/atlas.py counts` prints the status counts.
   Then run `python3 -I scripts/atlas.py export` to regenerate `data/festivals.json` and `data/festivals.csv`.
5. Write `reports/<YYYY-MM>.md`: new 2027 dates (festival, dates, source), new series,
   things that look off, and the status counts. Keep it short.
6. Commit `data/zouk_atlas.db`, the exported `data/festivals.json` and `.csv`, and the monthly report (not `reports/raw/` or `build/`) on
   `main` with a message like
   "Monthly 2027 check YYYY-MM: N new dates".
7. `git push origin main` to the public GitHub repo
   (github.com/andreeaioan97-maker/zouk-atlas). If the push fails, say so in the
   monthly report's summary and leave the commit local; don't force-push.
8. Rebuild the festival page and republish it to its existing link:
   - `python3 -I scripts/build_page.py scripts/page/template.html build/zouk-atlas-2027.html`
     (reads the database; `build/` is git-ignored).
   - With the Artifact tool, `read` https://claude.ai/artifact/RiAw2WGzCqCquHdqMCGE8X first,
     then `publish` `build/zouk-atlas-2027.html` with `url` set to that link. Never publish
     without `url`, which would create a second page. If publishing fails, say so in
     the monthly report summary.
   - Change the page's design only in `scripts/page/template.html`, never in `build/`.

Privacy: in the Facebook tab, read only the main column and never chats or
notifications. Never like, follow, comment or message anything.
