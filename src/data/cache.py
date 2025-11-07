"""
Data Caching Mechanism

This module handles caching CPI data locally to minimize API calls to Statistics Canada.
Cached data is stored in the Data/ directory and validated based on file age.
"""

import pandas as pd
import os
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_DIR = Path(__file__).parent.parent.parent / "Data"
CACHE_FILE = CACHE_DIR / "cpi_data_cache.parquet"
CACHE_MAX_AGE_DAYS = 1  # Refresh if older than 1 day


def ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def is_cache_valid() -> bool:
    """
    Check if cached data exists and is recent enough.

    Returns:
        True if cache exists and is valid (not too old), False otherwise
    """
    if not CACHE_FILE.exists():
        logger.info("No cache file found")
        return False

    # Check file age
    file_mtime = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
    age = datetime.now() - file_mtime

    if age > timedelta(days=CACHE_MAX_AGE_DAYS):
        logger.info(f"Cache is {age.days} days old, exceeds max age of {CACHE_MAX_AGE_DAYS} days")
        return False

    logger.info(f"Cache is valid (age: {age.days} days, {age.seconds // 3600} hours)")
    return True


def save_to_cache(df: pd.DataFrame):
    """
    Save DataFrame to cache.

    Args:
        df: CPI DataFrame to cache
    """
    ensure_cache_dir()

    try:
        # Save as parquet for efficient storage and fast loading
        df.to_parquet(CACHE_FILE, index=False)
        logger.info(f"Saved {len(df)} rows to cache: {CACHE_FILE}")
    except Exception as e:
        logger.error(f"Failed to save cache: {e}")
        # Don't raise - caching failure shouldn't break the app


def load_from_cache() -> pd.DataFrame:
    """
    Load DataFrame from cache.

    Returns:
        Cached CPI DataFrame

    Raises:
        FileNotFoundError: If cache file doesn't exist
        Exception: If loading fails
    """
    if not CACHE_FILE.exists():
        raise FileNotFoundError(f"Cache file not found: {CACHE_FILE}")

    try:
        df = pd.read_parquet(CACHE_FILE)
        logger.info(f"Loaded {len(df)} rows from cache")
        return df
    except Exception as e:
        logger.error(f"Failed to load cache: {e}")
        raise


def get_cache_info() -> dict:
    """
    Get information about the cached data.

    Returns:
        Dictionary with cache information:
            - exists: bool
            - path: str
            - size_mb: float (if exists)
            - last_modified: datetime (if exists)
            - age_hours: float (if exists)
    """
    info = {
        "exists": CACHE_FILE.exists(),
        "path": str(CACHE_FILE),
    }

    if info["exists"]:
        stat = CACHE_FILE.stat()
        info["size_mb"] = stat.st_size / (1024 * 1024)
        info["last_modified"] = datetime.fromtimestamp(stat.st_mtime)
        info["age_hours"] = (datetime.now() - info["last_modified"]).total_seconds() / 3600

    return info


def clear_cache():
    """
    Delete the cache file.
    """
    if CACHE_FILE.exists():
        try:
            CACHE_FILE.unlink()
            logger.info(f"Cache cleared: {CACHE_FILE}")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    else:
        logger.info("No cache to clear")


def get_cached_or_download(force_refresh: bool = False) -> pd.DataFrame:
    """
    Get CPI data from cache or download if cache is invalid/missing.

    This is the main function to use for loading data. It handles the caching
    logic automatically.

    Args:
        force_refresh: If True, bypass cache and download fresh data

    Returns:
        CPI DataFrame
    """
    from .loader import load_cpi_data

    if force_refresh:
        logger.info("Force refresh requested, downloading fresh data")
        df = load_cpi_data()
        save_to_cache(df)
        return df

    if is_cache_valid():
        try:
            logger.info("Loading data from cache")
            return load_from_cache()
        except Exception as e:
            logger.warning(f"Cache load failed, downloading fresh data: {e}")

    # Cache invalid or load failed, download fresh data
    logger.info("Downloading fresh CPI data")
    df = load_cpi_data()
    save_to_cache(df)
    return df
