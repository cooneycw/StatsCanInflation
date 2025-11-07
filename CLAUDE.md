# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project for analyzing Canadian inflation data from Statistics Canada. The project works with Consumer Price Index (CPI) data from Statistics Canada Table 18-10-0004-01 (monthly, not seasonally adjusted).

## Data Structure

The project uses Statistics Canada CSV data located in `Data/`:
- **Format**: CSV files with metadata header rows followed by time series data
- **Structure**: First ~8 rows contain metadata (table info, release date, geography), followed by product categories as rows and monthly time periods as columns
- **Base Year**: CPI values are indexed to 2002=100
- **Current Data**: `Data/1810000401-eng.csv` contains CPI data from January 2008 through September 2025

Key CPI categories in the dataset:
- All-items (overall CPI)
- Food
- Shelter
- Transportation
- Gasoline
- Health and personal care
- Recreation, education and reading
- Clothing and footwear
- Household operations, furnishings and equipment

## Architecture

This is a Python Shiny application following the src/ format structure:

```
StatsCanInflation/
├── main.py                      # Single entry point (dev & production)
├── pyproject.toml              # Dependencies (uv-compatible)
├── environment.yml             # Conda environment reference
├── src/
│   ├── ui/
│   │   └── app_ui.py          # Complete UI definition (4 tabs)
│   ├── server/
│   │   └── app_server.py      # Server logic and reactive patterns
│   ├── data/
│   │   ├── loader.py          # Stats Can data fetcher
│   │   └── cache.py           # Local caching mechanism
│   ├── models/
│   │   ├── inflation.py       # Inflation calculations (YoY, MoM)
│   │   └── analysis.py        # Analysis logic
│   └── utils/
│       ├── export.py          # Excel export functionality
│       └── formatting.py      # Number/date formatting
├── tests/                      # Unit tests
└── Data/                       # Cached data files (gitignored)
```

### Key Architectural Decisions

1. **Single Entry Point**: `main.py` serves as both development and production entry point
   - For local dev: `python main.py` runs on http://127.0.0.1:8000
   - For deployment: rsconnect uses `main:app`

2. **Data Management Strategy**: Hybrid approach
   - Local caching in `Data/` directory (gitignored)
   - Manual refresh button to fetch latest data from Stats Can website
   - Cache validation based on file age

3. **Shiny Architecture Pattern** (following Price_Opt best practices):
   - `app_ui.py`: Single file with ALL UI definition
   - `app_server.py`: Single file with ALL server logic
   - Global parameter consistency: Each input defined ONCE with unique ID
   - Reactive pattern: Value → Calc → Effect → Output

4. **Four Analysis Tabs**:
   - Recent Trends: Last 12-24 months, MoM and YoY changes
   - Historical Comparison: Long-term trends (2008-present)
   - Category Breakdown: Detailed analysis by CPI category
   - Custom Analysis: User-selected date ranges and filters

## Development Commands

### Environment Setup

```bash
# Create conda environment
conda env create -f environment.yml
conda activate StatsCanInflation

# Install dependencies with uv
uv pip install -e .
uv pip install -e ".[dev]"  # Include development dependencies

# Or install with regular pip
pip install -e .
```

### Running the Application

```bash
# Run the Shiny app locally
python main.py

# App will be available at: http://127.0.0.1:8000
```

### Development Tools

```bash
# Run tests
pytest

# Format code
black src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/
```

### Deployment

```bash
# Deploy to shinyapps.io
rsconnect deploy shiny . --entrypoint main:app --title stats_can_inflation

# App will be deployed to:
# https://cooneycw.shinyapps.io/stats_can_inflation/
```

### Git Workflow

```bash
# Remote is configured for SSH
git remote -v
# origin  git@github.com:cooneycw/StatsCanInflation.git

# Standard workflow
git add .
git commit -m "description"
git push origin main
```

## Working with Statistics Canada Data

When processing the CPI CSV files:
1. Skip the first ~8 metadata rows to reach the actual data table
2. The first data row contains month/year column headers (e.g., "January 2008", "February 2008")
3. Subsequent rows contain product categories and their CPI values
4. Handle the UTF-8 BOM character at file start
5. CPI values are float strings that need to be parsed