"""
Inflation Calculations

This module provides functions to calculate various inflation metrics from CPI data:
- Month-over-month (MoM) changes
- Year-over-year (YoY) changes
- Rolling averages
- Annualized rates
"""

import pandas as pd
import numpy as np
from typing import Optional, List


def calculate_mom_change(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate month-over-month (MoM) percentage change.

    Args:
        df: CPI DataFrame with columns ['date', 'category', 'value']

    Returns:
        DataFrame with additional 'mom_change' column (percentage)
    """
    result = df.copy()

    # Sort by category and date to ensure proper ordering
    result = result.sort_values(['category', 'date'])

    # Calculate percentage change within each category
    result['mom_change'] = result.groupby('category')['value'].pct_change() * 100

    return result


def calculate_yoy_change(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate year-over-year (YoY) percentage change.

    Args:
        df: CPI DataFrame with columns ['date', 'category', 'value']

    Returns:
        DataFrame with additional 'yoy_change' column (percentage)
    """
    result = df.copy()

    # Sort by category and date
    result = result.sort_values(['category', 'date'])

    # Calculate YoY change (12 months ago)
    result['yoy_change'] = result.groupby('category')['value'].pct_change(periods=12) * 100

    return result


def calculate_rolling_average(
    df: pd.DataFrame,
    column: str = 'yoy_change',
    window: int = 3
) -> pd.DataFrame:
    """
    Calculate rolling average of a metric.

    Args:
        df: DataFrame with inflation metrics
        column: Column name to calculate rolling average for
        window: Number of periods for rolling window

    Returns:
        DataFrame with additional column for rolling average
    """
    result = df.copy()

    result[f'{column}_rolling_{window}m'] = (
        result.groupby('category')[column]
        .transform(lambda x: x.rolling(window=window, min_periods=1).mean())
    )

    return result


def calculate_annualized_rate(df: pd.DataFrame, months: int = 12) -> pd.DataFrame:
    """
    Calculate annualized inflation rate over a specified period.

    Args:
        df: CPI DataFrame with columns ['date', 'category', 'value']
        months: Number of months to annualize over

    Returns:
        DataFrame with additional 'annualized_rate' column
    """
    result = df.copy()
    result = result.sort_values(['category', 'date'])

    # Calculate percentage change over specified months
    result[f'annualized_{months}m'] = (
        result.groupby('category')['value']
        .pct_change(periods=months) * 100
    )

    return result


def add_all_inflation_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all common inflation metrics to the DataFrame.

    This convenience function adds:
    - Month-over-month (MoM) change
    - Year-over-year (YoY) change
    - 3-month rolling average of YoY
    - 6-month rolling average of YoY
    - 12-month rolling average of YoY

    Args:
        df: CPI DataFrame with columns ['date', 'category', 'value']

    Returns:
        DataFrame with all inflation metrics
    """
    result = df.copy()

    # Calculate basic changes
    result = calculate_mom_change(result)
    result = calculate_yoy_change(result)

    # Calculate rolling averages
    result = calculate_rolling_average(result, 'yoy_change', window=3)
    result = calculate_rolling_average(result, 'yoy_change', window=6)
    result = calculate_rolling_average(result, 'yoy_change', window=12)

    return result


def get_latest_inflation_rate(
    df: pd.DataFrame,
    category: str = "All-items"
) -> dict:
    """
    Get the most recent inflation metrics for a category.

    Args:
        df: CPI DataFrame with inflation metrics
        category: Category name to query

    Returns:
        Dictionary with:
            - date: Latest date
            - cpi_value: Latest CPI value
            - mom_change: Latest month-over-month change
            - yoy_change: Latest year-over-year change
    """
    # Ensure we have the metrics
    if 'yoy_change' not in df.columns:
        df = add_all_inflation_metrics(df)

    # Filter to category and get most recent non-null row
    cat_data = df[df['category'] == category].copy()
    cat_data = cat_data.sort_values('date', ascending=False)

    # Get latest row with valid YoY data
    latest = cat_data[cat_data['yoy_change'].notna()].iloc[0]

    return {
        'date': latest['date'],
        'cpi_value': latest['value'],
        'mom_change': latest.get('mom_change'),
        'yoy_change': latest.get('yoy_change'),
    }


def compare_categories(
    df: pd.DataFrame,
    categories: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Compare inflation rates across multiple categories.

    Args:
        df: CPI DataFrame with inflation metrics
        categories: List of category names to compare
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)

    Returns:
        DataFrame with categories and their inflation metrics
    """
    # Ensure we have the metrics
    if 'yoy_change' not in df.columns:
        df = add_all_inflation_metrics(df)

    # Filter to specified categories
    result = df[df['category'].isin(categories)].copy()

    # Apply date filters if provided
    if start_date:
        result = result[result['date'] >= pd.to_datetime(start_date)]
    if end_date:
        result = result[result['date'] <= pd.to_datetime(end_date)]

    return result


def calculate_cumulative_inflation(
    df: pd.DataFrame,
    category: str = "All-items",
    start_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate cumulative inflation from a starting point.

    Args:
        df: CPI DataFrame
        category: Category to calculate for
        start_date: Starting date for cumulative calculation (YYYY-MM-DD)
                   If None, uses first date in data

    Returns:
        DataFrame with cumulative inflation column
    """
    cat_data = df[df['category'] == category].copy()
    cat_data = cat_data.sort_values('date')

    if start_date:
        start = pd.to_datetime(start_date)
        cat_data = cat_data[cat_data['date'] >= start]

    if len(cat_data) == 0:
        return cat_data

    # Get baseline CPI value
    baseline_cpi = cat_data.iloc[0]['value']

    # Calculate cumulative percentage change from baseline
    cat_data['cumulative_inflation'] = ((cat_data['value'] / baseline_cpi) - 1) * 100

    return cat_data


def get_inflation_summary_stats(
    df: pd.DataFrame,
    category: str = "All-items",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> dict:
    """
    Calculate summary statistics for inflation over a period.

    Args:
        df: CPI DataFrame with inflation metrics
        category: Category to analyze
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)

    Returns:
        Dictionary with summary statistics:
            - mean_yoy: Average year-over-year inflation
            - median_yoy: Median year-over-year inflation
            - std_yoy: Standard deviation of YoY inflation
            - min_yoy: Minimum YoY inflation
            - max_yoy: Maximum YoY inflation
            - current_yoy: Most recent YoY inflation
    """
    # Ensure we have the metrics
    if 'yoy_change' not in df.columns:
        df = add_all_inflation_metrics(df)

    # Filter data
    data = df[df['category'] == category].copy()

    if start_date:
        data = data[data['date'] >= pd.to_datetime(start_date)]
    if end_date:
        data = data[data['date'] <= pd.to_datetime(end_date)]

    # Remove NaN values
    yoy_data = data['yoy_change'].dropna()

    if len(yoy_data) == 0:
        return {}

    return {
        'mean_yoy': yoy_data.mean(),
        'median_yoy': yoy_data.median(),
        'std_yoy': yoy_data.std(),
        'min_yoy': yoy_data.min(),
        'max_yoy': yoy_data.max(),
        'current_yoy': yoy_data.iloc[-1] if len(yoy_data) > 0 else None,
        'count': len(yoy_data),
    }
