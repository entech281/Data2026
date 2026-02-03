# FRC Data 281

This application uses streamlit and motherduck to manage FRC scouting data.

## Running the App

### 1. Set up Python + virtual environment
Use your python IDE to create Python virtual environment

### 2. Install the package in editable mode 

From the repo root:

```commandline
pip install -e .
```

### 3. Set up Streamlit secrets file

The credentials needed to connect to motherduck and TBA must not be stored in files 
that are checked into git.
   
When the application runs in production, the secrets are set up
in streamlit console. When running locally, you
need to create directory ".streamlit" in the repo root and put a 
file called secrets.toml in it. The file looks like this:

```text
[motherduck]
token='big long token an admin will give you'

```
### 4. Run the streamlit app

The application can be run in multiple ways:

**Recommended: Using the Python module entry point**
```commandline
frc-scouting
```

**Alternative: Direct streamlit command**
```commandline
streamlit run frc_data_281/app/Home.py
```

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
│   │   ├── connection.py      # MotherDuck/DuckDB connection management
│   │   ├── schema.py          # Database schema definitions
│   │   └── cached_queries.py  # Cached query functions for performance
│   ├── analysis/              # Data analysis modules
│   │   ├── opr.py             # OPR (Offensive Power Rating) calculations
│   │   ├── numerizer.py       # Dataset numeric transformation utilities
│   │   └── dataset_tools.py   # Data manipulation and analysis helpers
│   ├── jobs/                  # Background job scheduling
│   │   └── scheduler.py       # Scheduled tasks (TBA sync, etc.)
│   └── utils/                 # Utility functions
│       └── helpers.py         # General helper functions
├── tests/                     # Test suite
├── example_pages/             # Example Streamlit pages for reference
├── utilities/                 # Development utilities and scripts
├── data/                      # Local data storage
├── static/                    # Static assets (images, etc.)
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
- Breaks down performance into granular metrics (coral scoring, reef scoring, auto points, etc.)
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
