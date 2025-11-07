"""
Statistics Canada CPI Data Loader

This module handles downloading and parsing Consumer Price Index (CPI) data
from Statistics Canada Table 18-10-0004-01.
"""

import requests
import pandas as pd
import io
import logging
import zipfile
from typing import Optional

logger = logging.getLogger(__name__)

# Statistics Canada CSV download URL
# This downloads the full table in wide format (months as columns)
STATSCAN_TABLE_ID = "18100004"
STATSCAN_CSV_URL = f"https://www150.statcan.gc.ca/n1/tbl/csv/{STATSCAN_TABLE_ID}-eng.zip"


def download_statscan_cpi_data() -> bytes:
    """
    Download the latest CPI data from Statistics Canada website.

    The data comes as a ZIP file containing a CSV. This function downloads
    the ZIP and extracts the CSV file.

    Returns:
        bytes: Raw CSV data

    Raises:
        requests.RequestException: If download fails
        Exception: If ZIP extraction fails
    """
    logger.info("Downloading CPI data from Statistics Canada...")

    try:
        # Download the ZIP file
        response = requests.get(STATSCAN_CSV_URL, timeout=30)
        response.raise_for_status()

        logger.info("Successfully downloaded ZIP file")

        # Extract CSV from ZIP
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            # Get list of files in ZIP
            file_list = zip_file.namelist()
            logger.info(f"Files in ZIP: {file_list}")

            # Find the CSV file (should be 18100004.csv, not the metadata file)
            csv_filename = None
            for filename in file_list:
                if filename.endswith('.csv') and 'MetaData' not in filename:
                    csv_filename = filename
                    break

            if not csv_filename:
                raise ValueError(f"Could not find CSV file in ZIP. Files: {file_list}")

            # Extract and return CSV content
            csv_data = zip_file.read(csv_filename)
            logger.info(f"Extracted {csv_filename} from ZIP ({len(csv_data)} bytes)")
            return csv_data

    except requests.RequestException as e:
        logger.error(f"Failed to download CPI data: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to extract CSV from ZIP: {e}")
        raise


def parse_statscan_csv(csv_data: bytes) -> pd.DataFrame:
    """
    Parse Statistics Canada CSV data format.

    The CSV is in "long format" with columns:
    - REF_DATE: Date in YYYY-MM format
    - GEO: Geography (we filter to "Canada")
    - Products and product groups: Category name
    - VALUE: CPI value
    - Other metadata columns

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
    df = pd.read_csv(io.BytesIO(csv_data), encoding='utf-8-sig', low_memory=False)

    logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
    logger.info(f"Columns: {df.columns.tolist()}")

    # Filter to Canada only
    df = df[df['GEO'] == 'Canada'].copy()

    # Select and rename relevant columns
    df = df[['REF_DATE', 'Products and product groups', 'VALUE']].copy()
    df.columns = ['date', 'category', 'value']

    # Convert date from YYYY-MM to datetime
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m')

    # Convert value to numeric
    df['value'] = pd.to_numeric(df['value'], errors='coerce')

    # Remove rows with missing values
    df = df.dropna()

    # Filter to only keep base 2002=100 data (remove deprecated indices)
    # Categories ending with "(1992=100)" or other base years should be excluded
    df = df[~df['category'].str.contains(r'\(19\d{2}=100\)', na=False, regex=True)]

    # Sort by category and date
    df = df.sort_values(['category', 'date']).reset_index(drop=True)

    logger.info(f"Parsed {len(df)} data points across {df['category'].nunique()} categories")
    logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")

    return df


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
