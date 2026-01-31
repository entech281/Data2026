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
└── pyproject.toml             # Project dependencies and configuration
```
