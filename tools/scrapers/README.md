# Tournament scrapers

One-off scripts used to bulk-load the 2027 season (Nov 2026). They are not a polished pipeline:
dates, months and some file names are hard-coded, so read a script before rerunning it.
Run everything from this directory with the project venv; working files (`*.csv`, `*.html`,
`*.json`, cookie jars) are gitignored.

General flow for every source (see CLAUDE.md "Adding tournaments in bulk"):

1. scrape → `<src>_raw.*`
2. build → `<src>_draft.csv` (or `<src>_draft_geo.csv` when the source gives lat/lng)
3. `python ../geocode.py <src>_draft.csv` → review `_geo.csv` for wrong same-named towns / county centroids
4. `python ../import_csv.py <src>_draft_geo.csv` (skips name + start_date duplicates)

## Ground rules learned the hard way

- Use plain requests (curl's default UA or the scripts' existing UA). **Do not** spoof browser
  user agents or retry around 403s; if a site blocks automated fetches, skip it.
- Don't call undocumented internal APIs (e.g. search.perfectgame.org's `/api/...`); use the
  site's public pages / its own forms.
- Nominatim often returns the county centroid for small towns (Marion IL/AR, Shawnee KS, Ozark MO,
  Monroe GA, Seward NE, Burleson TX, SLO, Santa Cruz, Riverside) or a same-named town in another
  state (Canton MI → MS, Shelby MI). Always eyeball the geocode output.
- Names that collide case-insensitively on the same date are treated as duplicates by the DB; add ` (City)`.

## Sources

| Source | Scripts | Notes |
|---|---|---|
| USSSA (all state sites) | `usssa.py` → `build_draft.py` → `usssa_fix.py` | `{st}baseball.usssa.com/events/?paged=N`. Edit target months in `usssa.py`. `build_draft.py` holds the label→city map, `fix_caps()`, and Sports America / KC Sports detection; `usssa_fix.py` adds more label fixes and known-bad pins. `build_draft.py` is also imported by other builders for `fix_caps`. |
| Game 7 | `g7.py` → `g7_build.py` | Listing with `from`/`to` date filter. Edit the dates in `g7.py` and the month check in `g7_build.py`. Organizer Other, ` (Game 7)` suffix. |
| GMB / AAYBA | `gmb_parse.py` → `gmb_build.py` | Save `https://playgmb.com/tournaments/` as `gmb.html` first. Card dates are trusted over URL slugs. |
| PBR (13 regional labels) | `pbr_all.py` → `pbr_build.py` | Playbook365 platform: listing page + `/refresh-csrf` token + POST `ajax-events`, plain curl with a cookie jar. Uses PBR's venue lat/lng. |
| Prospect Select | `ps_all.py` → `ps_build.py` | Same Playbook365 flow. `ps_all.py <base_url> <out.json>` works for any Playbook365 site. |
| Prospect Wire | `pw_all.py` → `pw_build.py` | Playbook365 (`play.prospectwire.com`). Skips HS Varsity. |
| Five Tool | `ps_all.py https://events.fivetool.org ft_raw.json` → `ft_build.py` | Organizer Five Tool. Matches existing DB rows by state + date and prints them (update their links rather than inserting). Skips camps/combines. |
| NCS | `ncs_scrape.py` → `ncs_build.py` → `ncs_fix.py` | `playncs.com/baseball/Events?from=..&to=..`. `ncs_fix.py` cleans names/cities. |
| Grand Slam Sports Tournaments | `gs_scrape.py` → `gs_build.py` | `grandslamtournaments.com` (same platform as NCS/Game 7, different card markup). Mostly MS/GA/AR/IN. |
| Triple Crown | fetch, then `tc_parse.py` | Fetch `https://components.triplecrownsports.com/Components/GetFilteredEventSchedule/?sportID=1&state=XX` for each state into `<dir>/tcapi_XX.html`, then `python tc_parse.py <dir>`. Ages come from each event page; the 2027 import CSV was hand-built from them. |
| Ballparks of America | fetch, then `boa_build.py` | Calendar is JS-rendered; `https://www.ballparksofamerica.com/tournaments-hub.md` (via their `llms.txt`) lists `/event-NNNNN` links. Save each as `boa_ev_NNNNN.html`. Pinned at 1000 Pat Nash Dr. |
| Perfect Game | `pg/pg_by_state.py` → `pg/pg_build.py` | Submits perfectgame.org/Schedule's own filter form (year, month, state, "Baseball Tournament") once per state × month (~330 requests, ~20 min). Results over 300 division rows need paging, which does not work via plain form posts, so **TX and GA only get the first page** in busy months. `pg_build.py` dedupes against the DB by `gid` and state+date+name, cleans free-text locations, skips leagues/<12U/test events. `pg_sched.py` and `pg_all.py` hold the shared form/parse helpers (`pg_all.py` run directly does the nationwide pass that hits the paging limit). |

## Not scrapable (as of Nov 2026)

- PG Northwest (washingtonbaseballtournaments.com), Game Day USA, BaseballConnected, infosports: 403.
- search.perfectgame.org: only via internal API (blocked by permission policy).
- Exposure Events: results are rendered client-side.
