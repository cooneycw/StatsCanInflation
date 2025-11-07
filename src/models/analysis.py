"""
Analysis Functions

High-level analysis functions for the four main views of the application:
1. Recent Trends (last 12-24 months)
2. Historical Comparison (2008-present)
3. Category Breakdown
4. Custom Analysis
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from .inflation import add_all_inflation_metrics


def get_recent_trends(
    df: pd.DataFrame,
    months: int = 24,
    categories: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Get recent inflation trends for the last N months.

    Args:
        df: CPI DataFrame
        months: Number of recent months to include (default 24)
        categories: Optional list of categories to include (default: key categories)

    Returns:
        DataFrame with recent data and inflation metrics
    """
    # Ensure we have inflation metrics
    df = add_all_inflation_metrics(df)

    # Calculate cutoff date
    max_date = df['date'].max()
    cutoff_date = max_date - pd.DateOffset(months=months)

    # Filter to recent period
    recent = df[df['date'] >= cutoff_date].copy()

    # Filter to specified categories or defaults
    if categories is None:
        categories = [
            "All-items",
            "Food",
            "Shelter",
            "Transportation",
            "Gasoline",
        ]

    recent = recent[recent['category'].isin(categories)]

    return recent.sort_values(['category', 'date'])


def get_historical_comparison(
    df: pd.DataFrame,
    categories: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Get full historical data for comparison (2008-present).

    Args:
        df: CPI DataFrame
        categories: Optional list of categories (default: key categories)

    Returns:
        DataFrame with historical data and inflation metrics
    """
    # Ensure we have inflation metrics
    df = add_all_inflation_metrics(df)

    # Filter to specified categories or defaults
    if categories is None:
        categories = [
            "All-items",
            "Food",
            "Shelter",
            "Transportation",
        ]

    historical = df[df['category'].isin(categories)].copy()

    return historical.sort_values(['category', 'date'])


def get_category_breakdown(
    df: pd.DataFrame,
    date: Optional[str] = None
) -> pd.DataFrame:
    """
    Get detailed breakdown of inflation by category for a specific date.

    Args:
        df: CPI DataFrame with inflation metrics
        date: Specific date (YYYY-MM-DD), if None uses most recent

    Returns:
        DataFrame with categories and their inflation metrics for the date
    """
    # Ensure we have inflation metrics
    df = add_all_inflation_metrics(df)

    # Get target date
    if date is None:
        target_date = df['date'].max()
    else:
        target_date = pd.to_datetime(date)

    # Get data for that date
    snapshot = df[df['date'] == target_date].copy()

    # Remove rows without YoY data
    snapshot = snapshot[snapshot['yoy_change'].notna()]

    # Sort by YoY change (descending)
    snapshot = snapshot.sort_values('yoy_change', ascending=False)

    return snapshot


def get_category_trends(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Get inflation trends for all major categories over a date range.

    Args:
        df: CPI DataFrame
        start_date: Start date (YYYY-MM-DD), None for all data
        end_date: End date (YYYY-MM-DD), None for all data

    Returns:
        DataFrame with category trends
    """
    # Ensure we have inflation metrics
    df = add_all_inflation_metrics(df)

    # Filter date range
    result = df.copy()
    if start_date:
        result = result[result['date'] >= pd.to_datetime(start_date)]
    if end_date:
        result = result[result['date'] <= pd.to_datetime(end_date)]

    return result.sort_values(['category', 'date'])


def compare_periods(
    df: pd.DataFrame,
    category: str,
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str
) -> dict:
    """
    Compare inflation metrics between two time periods.

    Args:
        df: CPI DataFrame
        category: Category to analyze
        period1_start: Period 1 start date (YYYY-MM-DD)
        period1_end: Period 1 end date (YYYY-MM-DD)
        period2_start: Period 2 start date (YYYY-MM-DD)
        period2_end: Period 2 end date (YYYY-MM-DD)

    Returns:
        Dictionary with comparison metrics for both periods
    """
    # Ensure we have inflation metrics
    df = add_all_inflation_metrics(df)

    # Filter to category
    cat_data = df[df['category'] == category].copy()

    # Get period 1 data
    p1 = cat_data[
        (cat_data['date'] >= pd.to_datetime(period1_start)) &
        (cat_data['date'] <= pd.to_datetime(period1_end))
    ]

    # Get period 2 data
    p2 = cat_data[
        (cat_data['date'] >= pd.to_datetime(period2_start)) &
        (cat_data['date'] <= pd.to_datetime(period2_end))
    ]

    # Calculate summary stats for each period
    def get_stats(data):
        yoy = data['yoy_change'].dropna()
        if len(yoy) == 0:
            return {}
        return {
            'mean_inflation': yoy.mean(),
            'median_inflation': yoy.median(),
            'min_inflation': yoy.min(),
            'max_inflation': yoy.max(),
            'std_inflation': yoy.std(),
        }

    return {
        'category': category,
        'period1': {
            'start': period1_start,
            'end': period1_end,
            **get_stats(p1)
        },
        'period2': {
            'start': period2_start,
            'end': period2_end,
            **get_stats(p2)
        }
    }


def get_top_inflating_categories(
    df: pd.DataFrame,
    date: Optional[str] = None,
    n: int = 10
) -> pd.DataFrame:
    """
    Get the top N categories with highest inflation at a given date.

    Args:
        df: CPI DataFrame
        date: Specific date (YYYY-MM-DD), if None uses most recent
        n: Number of top categories to return

    Returns:
        DataFrame with top inflating categories
    """
    snapshot = get_category_breakdown(df, date)
    return snapshot.head(n)


def get_bottom_inflating_categories(
    df: pd.DataFrame,
    date: Optional[str] = None,
    n: int = 10
) -> pd.DataFrame:
    """
    Get the bottom N categories with lowest inflation at a given date.

    Args:
        df: CPI DataFrame
        date: Specific date (YYYY-MM-DD), if None uses most recent
        n: Number of bottom categories to return

    Returns:
        DataFrame with lowest inflating categories
    """
    snapshot = get_category_breakdown(df, date)
    return snapshot.tail(n)


def calculate_inflation_percentile(
    df: pd.DataFrame,
    category: str,
    date: Optional[str] = None
) -> float:
    """
    Calculate what percentile a category's inflation falls into compared to all categories.

    Args:
        df: CPI DataFrame
        category: Category to check
        date: Specific date (YYYY-MM-DD), if None uses most recent

    Returns:
        Percentile (0-100)
    """
    snapshot = get_category_breakdown(df, date)

    if category not in snapshot['category'].values:
        return np.nan

    cat_inflation = snapshot[snapshot['category'] == category]['yoy_change'].values[0]
    all_inflation = snapshot['yoy_change'].values

    percentile = (all_inflation < cat_inflation).sum() / len(all_inflation) * 100

    return percentile


def get_monthly_summary(
    df: pd.DataFrame,
    year_month: str,
    categories: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Get summary of inflation metrics for a specific month.

    Args:
        df: CPI DataFrame
        year_month: Year and month in format "YYYY-MM"
        categories: Optional list of categories

    Returns:
        DataFrame with monthly summary
    """
    # Ensure we have inflation metrics
    df = add_all_inflation_metrics(df)

    # Parse year_month
    target_date = pd.to_datetime(year_month)

    # Filter to that month
    monthly = df[
        (df['date'].dt.year == target_date.year) &
        (df['date'].dt.month == target_date.month)
    ].copy()

    if categories:
        monthly = monthly[monthly['category'].isin(categories)]

    return monthly.sort_values('yoy_change', ascending=False)


def detect_inflation_trends(
    df: pd.DataFrame,
    category: str = "All-items",
    lookback_months: int = 6
) -> dict:
    """
    Detect if inflation is trending up, down, or stable.

    Args:
        df: CPI DataFrame
        category: Category to analyze
        lookback_months: Number of months to analyze

    Returns:
        Dictionary with trend analysis:
            - trend: 'increasing', 'decreasing', or 'stable'
            - slope: Linear regression slope
            - recent_mean: Mean inflation over lookback period
            - previous_mean: Mean inflation over previous equal period
    """
    # Ensure we have inflation metrics
    df = add_all_inflation_metrics(df)

    # Filter to category
    cat_data = df[df['category'] == category].copy()
    cat_data = cat_data.sort_values('date')

    # Get most recent period
    recent = cat_data.tail(lookback_months)

    # Get previous period for comparison
    previous = cat_data.tail(lookback_months * 2).head(lookback_months)

    if len(recent) < 2 or len(previous) < 2:
        return {'trend': 'insufficient_data'}

    # Calculate means
    recent_mean = recent['yoy_change'].mean()
    previous_mean = previous['yoy_change'].mean()

    # Calculate trend (simple linear regression on recent period)
    from numpy.polynomial import polynomial as P
    x = np.arange(len(recent))
    y = recent['yoy_change'].values

    # Fit linear polynomial
    coeffs = P.polyfit(x, y, 1)
    slope = coeffs[1]

    # Determine trend
    if abs(slope) < 0.05:  # Less than 0.05% change per month
        trend = 'stable'
    elif slope > 0:
        trend = 'increasing'
    else:
        trend = 'decreasing'

    return {
        'trend': trend,
        'slope': slope,
        'recent_mean': recent_mean,
        'previous_mean': previous_mean,
        'change': recent_mean - previous_mean,
    }


def get_volatility_metrics(
    df: pd.DataFrame,
    category: str = "All-items",
    months: int = 24
) -> dict:
    """
    Calculate volatility metrics for inflation.

    Args:
        df: CPI DataFrame
        category: Category to analyze
        months: Number of months to analyze

    Returns:
        Dictionary with volatility metrics:
            - std: Standard deviation of YoY changes
            - range: Max - Min YoY changes
            - cv: Coefficient of variation
    """
    # Ensure we have inflation metrics
    df = add_all_inflation_metrics(df)

    # Filter to category and recent period
    cat_data = df[df['category'] == category].copy()
    cat_data = cat_data.sort_values('date').tail(months)

    yoy = cat_data['yoy_change'].dropna()

    if len(yoy) < 2:
        return {}

    return {
        'std': yoy.std(),
        'range': yoy.max() - yoy.min(),
        'cv': yoy.std() / abs(yoy.mean()) if yoy.mean() != 0 else np.nan,
        'min': yoy.min(),
        'max': yoy.max(),
    }
