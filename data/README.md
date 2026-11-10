# Zouk Atlas data

- **`zouk_atlas.db`** (SQLite) is the source of truth. Its schema is in `schema.sql`
  (version in `PRAGMA user_version`).
- **`festivals.json`** and **`festivals.csv`** are exports for reading, diffs and spreadsheets.
  Regenerate them with `python3 -I scripts/atlas.py export` after every change; don't edit them by hand.

## Tables

| Table | One row per | Notes |
|---|---|---|
| `series` | festival series | name, home city/country, style, links, `last_checked` |
| `editions` | series × year | dates, source, `confirmed_by_organizer`, optional city/country if that edition moved, optional `venue_id` |
| `year_status` | series × year | research status (`listed`, `expected`, …) and note; feeds `status_2027` / `note_2027` |
| `venues` | venue | empty for now; link from `editions.venue_id` |
| `hotels` | hotel | empty for now |
| `edition_hotels` | edition × hotel | role (`official`, `partner`, `nearby`), price from (EUR) |

## Editing

Use `scripts/atlas.py` (`show`, `set-edition`, `set-status`, `set-note`, `touch`, `add-series`,
`export`, `counts`). Run `python3 -I scripts/atlas.py --help` for details. For anything else,
`sqlite3 data/zouk_atlas.db` works; keep `PRAGMA foreign_keys = ON`.

Schema changes: edit `schema.sql`, bump `user_version`, and apply the same change to the
existing database with `ALTER TABLE` (keep the steps in the commit message).
