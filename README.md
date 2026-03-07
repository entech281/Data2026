# FRC Data 281

This application uses Streamlit and a local DuckDB database to manage FRC scouting data.

## Setup on a New Machine

### 1. Prerequisites

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager).

Clone the repo and check out the active branch:

```commandline
git clone <repo-url>
cd Data2026
git checkout 2026-season-migration
```

### 2. Install dependencies

```commandline
uv sync
```

This creates `.venv/` and installs all packages from `uv.lock`.

### 3. Set up Streamlit secrets

The TBA API key must not be stored in files that are checked into git.

Create `.streamlit/secrets.toml` in the repo root:

```toml
[tba]
auth_key = "your-tba-api-key-here"

[cache]
cache_path = "."
enabled = "False"
```

Get a free TBA API key at [thebluealliance.com/account](https://www.thebluealliance.com/account).

> **Note:** A `[motherduck]` token is no longer required. The app now uses a local DuckDB file at `data/frc2026.duckdb`.

### 4. Initialize & sync the database

The database file doesn't exist yet on a fresh checkout — the pipeline creates it automatically:

```commandline
uv run python -m frc_data_281.the_blue_alliance.pipeline
```

This will:
- Create `data/frc2026.duckdb`
- Populate `tba.teams`, `tba.matches`, `tba.event_rankings`, and `tba.oprs` for all configured events

The scouting schema (`scouting.tags`, `scouting.pit`, etc.) is created automatically the first time the Streamlit app starts.

### 5. Run the app

```commandline
uv run frc-scouting
```

Or alternatively:

```commandline
streamlit run frc_data_281/app/Home.py
```

### Re-syncing data

To pull the latest match data from TBA:

- Click **"Refresh Data from TBA"** on the Data Refresh page in the app, or
- Run directly: `uv run python -m frc_data_281.the_blue_alliance.pipeline`

The pipeline uses merge disposition — re-running is always safe and won't duplicate records.

---

## Project Structure

```
Data2026/
├── frc_data_281/              # Main application package
│   ├── __main__.py            # Entry point for running the app (frc-scouting)
│   ├── app/                   # Streamlit web application
│   │   ├── Home.py            # Landing page for the Streamlit app
│   │   ├── run.py             # Helper module to run app programmatically
│   │   ├── components/        # Reusable UI components (event selector, team stats, styling)
│   │   └── pages/             # Streamlit pages (match scouting, team analysis, data entry, etc.)
│   ├── the_blue_alliance/     # The Blue Alliance API integration
│   │   ├── client.py          # API client for fetching FRC data
│   │   └── pipeline.py        # Data pipeline for syncing TBA data to database
│   ├── db/                    # Database layer
│   │   ├── connection.py      # DuckDB connection management (local file)
│   │   ├── schema.py          # Database schema definitions
│   │   └── cached_queries.py  # Cached query functions for performance
│   ├── analysis/              # Data analysis modules
│   │   ├── opr.py             # OPR (Offensive Power Rating) calculations
│   │   ├── season_specific/   # Season-specific analysis logic
│   │   │   ├── season_2025.py # 2025 game: Reefscape (coral/reef/barge)
│   │   │   └── season_2026.py # 2026 game: Hub scoring, Tower, Energized/Supercharged/Traversal RPs
│   │   ├── numerizer.py       # Dataset numeric transformation utilities
│   │   └── dataset_tools.py   # Data manipulation and analysis helpers
│   ├── jobs/                  # Background job scheduling
│   │   └── scheduler.py       # Scheduled tasks (TBA sync, etc.)
│   └── utils/                 # Utility functions
│       └── helpers.py         # General helper functions
├── tests/                     # Test suite
├── example_pages/             # Example Streamlit pages for reference
├── utilities/                 # Development utilities and scripts
├── data/                      # Local data storage (frc2026.duckdb — not committed to git)
└── pyproject.toml             # Project dependencies and configuration
```

## Glossary of Terms

### FRC Scouting Metrics

**OPR (Offensive Power Rating)**
- A statistical measure of how many points a team contributes to their alliance's score
- Calculated using linear regression on match data to isolate individual team contributions
- Higher OPR indicates stronger offensive performance

**DPR (Defensive Power Rating)**
- A measure of how many points a team prevents the opposing alliance from scoring
- Calculated similarly to OPR but focused on defensive impact
- Higher DPR indicates stronger defensive capabilities

**CCWM (Calculated Contribution to Winning Margin)**
- A measure of a team's contribution to their alliance's margin of victory
- Provided by The Blue Alliance API as a standard FRC metric
- Accounts for both offensive and defensive contributions

**CCM (Component Contribution Metrics)**
- Extended analysis that applies OPR-style calculations to individual game components
- Breaks down performance into granular metrics (hub scoring, tower points, auto points, etc.)
- Provides detailed insights into team strengths and weaknesses across all game elements

**Z-Score (Standard Score)**
- A statistical measure indicating how many standard deviations a value is from the mean
- Formula: `z = (value - mean) / standard_deviation`
- Allows comparison of different metrics on the same scale:
  - `z = 0`: Average performance
  - `z > 0`: Above average (z = 1 means one standard deviation above)
  - `z < 0`: Below average (z = -1 means one standard deviation below)
  - `|z| > 2`: Statistically significant outlier
- Used throughout the app to normalize and compare team performance across different metrics
