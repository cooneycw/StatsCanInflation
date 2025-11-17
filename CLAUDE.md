# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project for analyzing Canadian inflation data from Statistics Canada. The project works with Consumer Price Index (CPI) data from Statistics Canada Table 18-10-0004-01 (monthly, not seasonally adjusted).

## Data Structure

The project downloads CPI data from Statistics Canada Table 18-10-0004-01:
- **Source**: https://www150.statcan.gc.ca/n1/tbl/csv/18100004-eng.zip (ZIP file containing CSV)
- **Format**: Long-format CSV with columns: REF_DATE, GEO, Products and product groups, VALUE
- **Base Year**: CPI values are indexed to 2002=100 (older base years filtered out)
- **Coverage**: Data from 1914 to present (184k+ data points across 357 categories)
- **Caching**: Downloaded data cached locally as parquet file in `Data/` (1-day expiry)

## CRITICAL: Category Ordering Convention

**ALL category dropdowns, legends, and tabular views MUST follow this exact ordering:**

**Priority Categories (always first, in this order):**
1. All-items
2. Goods
3. Services
4. Energy
5. All-items excluding food and energy
6. All-items excluding energy

**Remaining Categories:**
- All other categories displayed in alphabetical order after the priority categories

This ordering convention MUST be applied consistently across:
- All dropdown menus/checkbox groups
- All plot legends
- All table displays
- Data exports

Key individual CPI categories in the dataset:
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

4. **Five Analysis Tabs**:
   - **Recent Trends**: Enhanced dashboard with 4 metric cards (Current Inflation, MoM Change, Trend Direction, Momentum), YoY plot with 2% target line, acceleration/deceleration chart, rolling averages, and category heatmap
   - **Historical Comparison**: Long-term trends (2008-present) with CPI index, YoY rates, and cumulative inflation
   - **Category Breakdown**: Detailed analysis by CPI category with sortable bar charts and trend plots
   - **Custom Analysis**: User-selected date ranges and filters with Excel/CSV export
   - **Data Table**: Wide-format view (categories as rows, dates as columns) matching original Stats Can format, with toggleable value types (CPI/YoY/MoM) and CSV download

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
rsconnect deploy shiny . --new --title "stats_can_inflation"

# App is deployed to:
# https://cooneycw.shinyapps.io/stats_can_inflation/

# Note: Requires requirements.txt file (not pip freeze) to avoid SSH git dependencies
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

## Base Effects Analysis

The app includes a sophisticated base effects analysis feature to identify when year-over-year (YoY) inflation changes are driven by what happened 12 months ago rather than current price momentum.

### What Are Base Effects?

Base effects occur when YoY inflation changes significantly, not because current prices are changing, but because an unusual price movement from 12 months ago is "rolling off" the YoY calculation. For example:
- If gasoline spiked 12 months ago, YoY inflation will drop when that spike rolls off, even if current prices are stable
- If prices crashed 12 months ago, YoY inflation will rise when that crash rolls off, even without current price increases

### Calculation Methodology

**This implementation follows the methodology recommended by the European Central Bank, Bank of Canada, and Statistics Canada.**

**Core Metrics** (from `src/models/inflation.py:249-282`):

1. **Annualized Month-over-Month (Annualized MoM)**
   - Formula: `MoM change × 12`
   - Represents current price momentum projected as an annual rate
   - Shows what inflation would be if current MoM trends continued for a year

2. **Base Effect Contribution**
   - Formula: `YoY inflation - Annualized MoM`
   - This measures how much of the YoY rate stems from unusual price movements 12 months ago
   - Positive value: YoY is higher than current momentum suggests (base effect pulling it up)
   - Negative value: YoY is lower than current momentum suggests (base effect pulling it down)
   - Near zero: YoY accurately reflects current price trends (minimal base effects)

**Research Validation**: This methodology is validated in the research paper "Understanding and Predicting Base Effects in Canadian Inflation" (available in the Research tab of the application). The paper analyzes 9 major base effect episodes from 2020-2025 and confirms this approach aligns with central banking best practices.

3. **Momentum Period Options**
   - **Monthly**: Uses single-month MoM (noisy but responsive)
   - **Quarterly**: Uses 3-month rolling average of MoM (default, balances smoothing and responsiveness)
   - **Half-year**: Uses 6-month rolling average of MoM (smoothest, shows underlying trends)

### Projection Features

The analysis includes forward-looking projections (from `src/models/inflation.py:284-351`):

1. **Zero Momentum Projection** (if prices flat)
   - Assumes 0% MoM going forward
   - Shows where YoY would go if prices stopped changing
   - Reveals pure base effect impact

2. **Current Momentum Projection**
   - Uses recent average MoM (3-month or 6-month depending on momentum period selection)
   - Shows expected YoY path if current trends continue
   - Projects 3 months ahead by default

### Implementation Location

- **Calculation**: `src/models/inflation.py` - `calculate_base_effects()`, `project_future_yoy()`
- **Visualization**: `src/server/app_server.py:318-467` - `base_effects_section()`, `base_effects_plot()`
- **UI Toggle**: `src/ui/app_ui.py:99-120` - Checkbox to show/hide, momentum period selector

### Interpretation Guide

When analyzing the base effects chart:
- **Widening gap** between YoY and momentum: Base effects are strengthening
- **Convergence**: YoY inflation is normalizing to match current price trends
- **Projection divergence**: Upcoming base effects will cause significant YoY changes
- **Large base effect contribution** (shaded area): YoY inflation is mechanically driven by the base, not current conditions

## Working with Statistics Canada Data

When processing the CPI CSV files:
1. Skip the first ~8 metadata rows to reach the actual data table
2. The first data row contains month/year column headers (e.g., "January 2008", "February 2008")
3. Subsequent rows contain product categories and their CPI values
4. Handle the UTF-8 BOM character at file start
5. CPI values are float strings that need to be parsed