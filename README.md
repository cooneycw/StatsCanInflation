# Statistics Canada Inflation Analysis

An interactive Shiny application for analyzing Canadian inflation trends using Statistics Canada Consumer Price Index (CPI) data.

## Overview

This application provides comprehensive analysis of Canadian inflation data from Statistics Canada Table 18-10-0004-01 (Consumer Price Index, monthly, not seasonally adjusted). The tool enables users to:

- Track recent inflation trends (last 12-24 months)
- Compare current inflation to historical periods (2008-present)
- Analyze inflation by category (Food, Shelter, Transportation, etc.)
- Create custom date range comparisons
- Export analysis results to Excel

## Features

### Four Analysis Views

1. **Recent Trends**: Month-over-month and year-over-year inflation changes for the most recent 12-24 months
2. **Historical Comparison**: Long-term inflation trends from 2008 to present
3. **Category Breakdown**: Detailed analysis by CPI categories (Food, Shelter, Transportation, Gasoline, Health, etc.)
4. **Custom Analysis**: User-defined date ranges and category filters for tailored analysis

### Data Management

- **Automatic Caching**: Downloaded data is cached locally to minimize API calls
- **Manual Refresh**: Update button to fetch the latest data from Statistics Canada
- **Data Export**: Download analysis results as formatted Excel workbooks

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Conda (for environment management)
- uv (for package installation)

### Installation

1. Clone the repository:
```bash
git clone git@github.com:cooneycw/StatsCanInflation.git
cd StatsCanInflation
```

2. Create and activate conda environment:
```bash
conda env create -f environment.yml
conda activate StatsCanInflation
```

3. Install dependencies with uv:
```bash
uv pip install -e .
```

4. Run the application:
```bash
python main.py
```

5. Open your browser to: http://127.0.0.1:8000

## Data Source

This application uses Consumer Price Index (CPI) data from Statistics Canada:
- **Table**: 18-10-0004-01
- **Description**: Consumer Price Index, monthly, not seasonally adjusted
- **Base Year**: 2002=100
- **Coverage**: January 2008 to present
- **Geography**: Canada (national level)

### CPI Categories Analyzed

- All-items (overall CPI)
- Food
- Shelter
- Transportation
- Gasoline
- Health and personal care
- Recreation, education and reading
- Clothing and footwear
- Household operations, furnishings and equipment

## Development

### Project Structure

The project follows the src/ format with clear separation of concerns:

- `src/ui/`: User interface definition
- `src/server/`: Server logic and reactive patterns
- `src/data/`: Data loading and caching
- `src/models/`: Inflation calculations and analysis
- `src/utils/`: Export and formatting utilities
- `tests/`: Unit tests

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/ tests/
```

## Deployment

The application is deployed to shinyapps.io:

**Live App**: https://cooneycw.shinyapps.io/stats_can_inflation/

To deploy updates:
```bash
rsconnect deploy shiny . --entrypoint main:app --title stats_can_inflation
```

## License

This project analyzes publicly available data from Statistics Canada.

## Author

Created by cooneycw
