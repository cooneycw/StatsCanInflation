"""
Statistics Canada CPI Data Loader

This module handles downloading and parsing Consumer Price Index (CPI) data
from Statistics Canada Table 18-10-0004-01.
"""

import requests
import pandas as pd
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Statistics Canada Open Data API endpoint
STATSCAN_TABLE_ID = "18100004"
STATSCAN_CSV_URL = f"https://www150.statcan.gc.ca/t1/tbl1/en/dtl!downloadDbLoadingData-nonTraduit.action?pid={STATSCAN_TABLE_ID}01&latestN=0&startDate=&endDate=&csvLocale=en&selectedMembers=%5B%5B%5D%5D"

# Alternative direct download URL (if needed)
STATSCAN_DIRECT_URL = "https://www150.statcan.gc.ca/n1/tbl/csv/18100004-eng.zip"


def download_statscan_cpi_data() -> bytes:
    """
    Download the latest CPI data from Statistics Canada website.

    Returns:
        bytes: Raw CSV data

    Raises:
        requests.RequestException: If download fails
    """
    logger.info("Downloading CPI data from Statistics Canada...")

    try:
        # Try the main data table download endpoint
        response = requests.get(STATSCAN_CSV_URL, timeout=30)
        response.raise_for_status()

        logger.info("Successfully downloaded CPI data")
        return response.content

    except requests.RequestException as e:
        logger.error(f"Failed to download CPI data: {e}")
        raise


def parse_statscan_csv(csv_data: bytes) -> pd.DataFrame:
    """
    Parse Statistics Canada CSV data format.

    The CSV has a unique structure:
    - First ~8 rows: Metadata (table info, release date, geography)
    - Row ~9: Column headers with month/year labels
    - Remaining rows: Product categories with CPI values by month

    Args:
        csv_data: Raw CSV bytes

    Returns:
        pandas DataFrame with parsed CPI data in long format:
            - date: Date column (datetime)
            - category: CPI category name
            - value: CPI value (float, base 2002=100)
    """
    logger.info("Parsing CPI CSV data...")

    # Read CSV, handling UTF-8 BOM
    csv_text = csv_data.decode('utf-8-sig')
    lines = csv_text.strip().split('\n')

    # Find the data table start (after metadata)
    # Look for the row that starts with "Geography"
    header_row = None
    for i, line in enumerate(lines):
        if line.startswith('"Geography"') or line.startswith('Geography'):
            header_row = i
            break

    if header_row is None:
        raise ValueError("Could not find data table header in CSV")

    # Skip the geography row and get to the actual column headers
    # The structure is:
    # - Row N: "Geography","Canada",...
    # - Row N+1: "Products and product groups","January 2008","February 2008",...
    # - Row N+2: ,"2002=100",...  (base year info)
    # - Row N+3 onwards: Data rows

    # Read from the header row onwards
    df = pd.read_csv(
        io.StringIO('\n'.join(lines[header_row:])),
        skiprows=[1, 2],  # Skip geography and base year rows
        low_memory=False
    )

    # First column is "Products and product groups"
    # Rename it to 'category'
    df.columns = ['category'] + list(df.columns[1:])

    # Convert from wide format (months as columns) to long format
    # Melt all date columns into rows
    date_columns = [col for col in df.columns if col != 'category']

    df_long = pd.melt(
        df,
        id_vars=['category'],
        value_vars=date_columns,
        var_name='date',
        value_name='value'
    )

    # Convert date strings like "January 2008" to datetime
    df_long['date'] = pd.to_datetime(df_long['date'], format='%B %Y')

    # Convert value to numeric (handle any empty strings or errors)
    df_long['value'] = pd.to_numeric(df_long['value'], errors='coerce')

    # Remove rows with missing values
    df_long = df_long.dropna()

    # Sort by date and category
    df_long = df_long.sort_values(['category', 'date']).reset_index(drop=True)

    logger.info(f"Parsed {len(df_long)} data points across {df_long['category'].nunique()} categories")

    return df_long


def load_cpi_data() -> pd.DataFrame:
    """
    Main function to download and parse CPI data.

    Returns:
        pandas DataFrame with CPI data

    Raises:
        Exception: If download or parsing fails
    """
    try:
        csv_data = download_statscan_cpi_data()
        df = parse_statscan_csv(csv_data)
        return df
    except Exception as e:
        logger.error(f"Failed to load CPI data: {e}")
        raise


def get_categories(df: pd.DataFrame) -> list:
    """
    Get list of all CPI categories in the data.

    Args:
        df: CPI DataFrame

    Returns:
        List of category names
    """
    return sorted(df['category'].unique().tolist())


def filter_by_category(df: pd.DataFrame, categories: list) -> pd.DataFrame:
    """
    Filter data to specific categories.

    Args:
        df: CPI DataFrame
        categories: List of category names to include

    Returns:
        Filtered DataFrame
    """
    return df[df['category'].isin(categories)].copy()


def filter_by_date_range(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Filter data to a specific date range.

    Args:
        df: CPI DataFrame
        start_date: Start date (YYYY-MM-DD format), None for no limit
        end_date: End date (YYYY-MM-DD format), None for no limit

    Returns:
        Filtered DataFrame
    """
    result = df.copy()

    if start_date:
        start = pd.to_datetime(start_date)
        result = result[result['date'] >= start]

    if end_date:
        end = pd.to_datetime(end_date)
        result = result[result['date'] <= end]

    return result
