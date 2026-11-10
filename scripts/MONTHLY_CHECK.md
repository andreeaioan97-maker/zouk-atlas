# Monthly 2027 check

Instructions for the scheduled Orca automation (Claude). Goal: keep
`data/festivals.json` / `.csv` current with newly announced 2027 European
zouk festival dates.

1. `git checkout data/2027-festival-list` and `git pull --ff-only` (stay on this branch; never touch `main`,
   never merge it into `main`, never force-push).
2. Run `python3 -I scripts/check_2027.py --out reports/raw/$(date +%Y-%m)`.
   It takes about 20 minutes and drives Orca's browser slowly. Don't interrupt it.
   - Exit code 2 means a login is missing. Write `reports/$(date +%Y-%m).md` saying
     which login, so the user knows to log in again in this workspace's Orca browser tab.
     Commit that, push it (step 7) and stop.
3. Read `reports/raw/<month>/report.md`. For each lead:
   - **Instagram**: record a 2027 edition only when the organizer states the dates
     (bio, caption, or flyer). If a date is only on a flyer image, open the post and
     screenshot it to read it. Watch for typos: a post published in 2026 that says
     "2027" for an event the bio dates to 2026 is not a 2027 announcement.
   - **DJ Mesmes "NEW?" items**: add only festivals, marathons, congresses and
     dance holidays. Skip workshops, bootcamps, teacher trainings and weekenders
     with named teachers (same rule as the base list). Skip events outside Europe.
     Open the event's Facebook link to confirm the dates before adding it.
4. Update `data/festivals.json` in the existing schema:
   - `editions["2027"] = {start, end, source, confirmed_by_organizer}`
   - `status_2027 = "listed"`
   - update `note_2027`
   - set `last_checked` to today on every record you checked
   - give new series the same fields as existing ones
   Then run `python3 scripts/to_csv.py data/festivals.json data/festivals.csv`.
5. Write `reports/<YYYY-MM>.md`: new 2027 dates (festival, dates, source), new series,
   things that look off, and the status counts. Keep it short.
6. Commit the data and the monthly report (not `reports/raw/`) on
   `data/2027-festival-list` with a message like
   "Monthly 2027 check YYYY-MM: N new dates".
7. `git push origin data/2027-festival-list` to the private GitHub repo
   (github.com/andreeaioan97-maker/zouk-atlas). If the push fails, say so in the
   monthly report's summary and leave the commit local; don't force-push.

Privacy: in the Facebook tab, read only the main column and never chats or
notifications. Never like, follow, comment or message anything.
