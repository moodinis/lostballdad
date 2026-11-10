# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## What this project is

A CherryPy web application that serves a more robust, dynamic version of the 14U youth baseball tournament finder. It replaces the static GitHub Pages site in the sibling `tourneypage` repo with a server-rendered app backed by the same cloud MySQL database.

The goal is a full-featured app with dynamic filtering, multiple age groups, CRUD admin capabilities, and richer UI — things the static build pipeline approach can't support.

## Tech stack

- **Backend**: CherryPy (Python)
- **Templating**: Jinja2
- **Database**: MySQL at `34.45.11.139`, database `tourneydatabase` (same DB as `tourneypage`)
- **Frontend**: Leaflet.js map, vanilla JS, same design language as `tourneypage`

## Database schema

Two tables in `tourneydatabase`:
- `organizers` — `id`, `name`
- `tournaments` — `name`, `organizer_id`, `city`, `state`, `start_date`, `end_date`, `start_age`, `end_age`, `link`, `lat`, `lng`

DB credentials are in `.env` (not committed). Copy `.env.example` to `.env` and fill in values.

## Project structure

```
tourneysv2/
├── server.py           # CherryPy app entry point — run this to start
├── db.py               # DB connection pool helper
├── requirements.txt
├── .env                # DB credentials (gitignored)
├── .env.example        # Template for credentials
├── tools/
│   ├── geocode.py      # Fill lat/lng for a draft CSV (OpenStreetMap Nominatim)
│   └── import_csv.py   # Insert a CSV of tournaments into the DB
├── templates/
│   ├── base.html       # Base layout with header/nav
│   └── map.html        # Main map view (extends base)
└── static/
    ├── app.css
    ├── app.js
    └── map.js          # Map, clustering and chip filters
```

## Python environment

The project lives on the Ubuntu box at `/home/lenovo-cc/projects/tourneysv2`. Always use the venv at `/home/lenovo-cc/projects/tourneysv2venv`.

```
python3 -m venv /home/lenovo-cc/projects/tourneysv2venv   # first time only
source /home/lenovo-cc/projects/tourneysv2venv/bin/activate
```

## Running the app

```
pip install -r requirements.txt
cp .env.example .env   # then fill in credentials
python server.py
```

App runs at `http://localhost:8080` by default. Local runs connect to Cloud SQL's public IP, so the machine's public IP must be in the instance's authorized networks.

## Adding tournaments in bulk

Tournaments are mostly 2027 season data gathered from organizer sites (USSSA state sites `{st}baseball.usssa.com/events/`, Game 7, PG Nevada/Northwest, Triple Crown, CABA Colorado). Workflow:

1. Build a CSV: `name,organizer,city,state,start_date,end_date,start_age,end_age,link,geo` (`geo` optional; see `tools/geocode.py`).
   - `organizer` must match `organizers.name`. USSSA events directed by "Sports America" or KC Sports (Garrett Fortuna / "KC Sports"/"KCS" names) go under those organizers. Smaller organizers go under `Other` with the real organizer in parentheses in the name, e.g. `Frozen Rope Classic (Game 7)`.
   - Skip softball and events entirely below 12U. If two rows share name + start date, append ` (City)` to both.
   - Replace venue/region labels with a city: Scrap Yard→Conroe TX, MWC→Midwest City OK, Kentuckiana→Louisville area (geo `Louisville, KY`), Greater New Orleans Area→New Orleans area, Eastern Jackson County MO (geo `Blue Springs, MO`), Tri Cities TN (geo `Johnson City, TN`), Sprowls Horizon Park→Pinellas Park FL, Bob Lewis Park NC→Candler NC.
2. `python tools/geocode.py draft.csv` → writes `draft_geo.csv`; review for wrong same-named towns.
3. `python tools/import_csv.py draft_geo.csv` → inserts, skipping name+start_date duplicates.

Fall seasons are hidden on the map (`SHOW_FALL = False` in `server.py`); org chips only show organizers with events in the current view.

## Organizer metadata

These org codes and colors carry over from `tourneypage/build.py` and should stay in sync:

| Code   | Label                 | Color     |
|--------|-----------------------|-----------|
| pg     | Perfect Game          | #1F3A5F   |
| usssa  | USSSA                 | #BC5B39   |
| tc     | Triple Crown Sports   | #2F6F4E   |
| gt     | Gametime Tournaments  | #EAB308   |
| gsc    | Genesis Sports Complex| #EA580C   |
| kcs    | KC Sports             | #7C3AED   |
| sa     | Sports America        | #0891B2   |
| ft     | Five Tool             | #DC2626   |
| swwbc  | Southwest Wood Bat    | #8B5E3C   |
| caba   | CABA                  | #DB2777   |
| other  | Other (catch-all; put the real organizer in the event name) | #6B7280 |

## Adding a new organizer

1. Insert a row into `organizers` in the DB
2. Add the org code + color to `ORG_META` in `server.py`

## Deployment

Deployed to **Google Cloud Run** via GitHub Actions on every push to `main`.

**Live URL:** https://lostballdad-1000715890065.us-central1.run.app

### GCP resources

| Resource | Name / Value |
|---|---|
| Cloud Run service | `lostballdad` (us-central1) |
| Artifact Registry repo | `lostballdad`, image: `us-central1-docker.pkg.dev/lostballdad/lostballdad/app` |
| Cloud SQL instance | `lostballdad` (us-central1-c), connection: `lostballdad:us-central1:lostballdad` |
| Secret Manager secrets | `DB_USER`, `DB_PASSWORD` |
| CI/CD service account | `github-actions@lostballdad.iam.gserviceaccount.com` |
| Cloud Run runtime SA | `1000715890065-compute@developer.gserviceaccount.com` |
| Workload Identity pool | `github-actions-pool` / provider `github-actions-provider` |

### DB connection

`db.py` connects via **Cloud SQL Auth Proxy Unix socket** on Cloud Run (`DB_SOCKET=/cloudsql/lostballdad:us-central1:lostballdad`), and falls back to host/port for local development via `.env`.

### Updating secrets

Never use `echo | gcloud secrets` to set a value — the trailing newline corrupts it. Use `printf '%s' "$VALUE" | gcloud secrets versions add NAME --data-file=-`, or the Secret Manager REST API with explicit base64 encoding.
