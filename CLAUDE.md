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
├── templates/
│   ├── base.html       # Base layout with header/nav
│   └── map.html        # Main map view (extends base)
└── static/
    ├── app.css
    └── app.js
```

## Running the app

```
pip install -r requirements.txt
cp .env.example .env   # then fill in credentials
python server.py
```

App runs at `http://localhost:8080` by default.

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

## Adding a new organizer

1. Insert a row into `organizers` in the DB
2. Add the org code + color to `ORG_META` in `server.py`

## Deployment

TBD — app is not yet deployed. Target is a VPS or cloud run instance (not GitHub Pages, since this requires a live Python process).
