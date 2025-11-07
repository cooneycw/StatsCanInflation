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
    - Base effect metrics (annualized MoM, base effect contribution)

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

    # Calculate base effects
    result = calculate_base_effects(result)

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


def calculate_base_effects(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate base effect metrics to identify when Y oY changes are driven by
    what happened 12 months ago rather than current price momentum.

    Base effects occur when:
    - A large price change from 12 months ago "rolls off" the YoY calculation
    - YoY inflation changes dramatically, but MoM momentum is stable

    Args:
        df: CPI DataFrame with mom_change and yoy_change columns

    Returns:
        DataFrame with additional columns:
            - annualized_mom: MoM change * 12 (shows current momentum as annual rate)
            - base_effect_contribution: Difference between YoY and annualized MoM
            - value_12m_ago: CPI value from 12 months ago (for reference)
    """
    result = df.copy()
    result = result.sort_values(['category', 'date'])

    # Annualize the month-over-month change (current momentum)
    result['annualized_mom'] = result['mom_change'] * 12

    # Base effect contribution: how much of YoY is due to base vs current momentum
    # Positive = YoY higher than current momentum suggests (base pulling it up)
    # Negative = YoY lower than current momentum suggests (base pulling it down)
    result['base_effect_contribution'] = result['yoy_change'] - result['annualized_mom']

    # Get CPI value from 12 months ago for reference
    result['value_12m_ago'] = result.groupby('category')['value'].shift(12)

    return result


def project_future_yoy(
    df: pd.DataFrame,
    category: str = "All-items",
    months_ahead: int = 3,
    mom_assumption: str = "recent_average"
) -> pd.DataFrame:
    """
    Project future year-over-year inflation rates based on different MoM assumptions.

    This helps identify upcoming base effects: if current prices stay stable,
    will YoY inflation jump or drop due to what's rolling off from 12 months ago?

    Args:
        df: CPI DataFrame with all inflation metrics
        category: Category to project
        months_ahead: Number of months to project forward
        mom_assumption: How to project MoM changes:
            - "zero": Assume 0% MoM (flat prices)
            - "recent_average": Use average of last 3 months
            - "current": Use most recent month's MoM

    Returns:
        DataFrame with projected dates and YoY values
    """
    cat_data = df[df['category'] == category].copy()
    cat_data = cat_data.sort_values('date')

    # Get the most recent data point
    latest = cat_data.iloc[-1]
    latest_date = latest['date']
    latest_value = latest['value']

    # Determine MoM assumption
    if mom_assumption == "zero":
        mom_rate = 0.0
    elif mom_assumption == "current":
        mom_rate = latest.get('mom_change', 0) / 100
    else:  # recent_average
        recent_mom = cat_data.tail(3)['mom_change'].mean() / 100
        mom_rate = recent_mom

    # Project future values
    projections = []
    current_value = latest_value

    for i in range(1, months_ahead + 1):
        # Project CPI value
        current_value = current_value * (1 + mom_rate)
        future_date = latest_date + pd.DateOffset(months=i)

        # Get value from 12 months before this future date
        lookback_date = future_date - pd.DateOffset(months=12)
        value_12m_ago_row = cat_data[cat_data['date'] == lookback_date]

        if len(value_12m_ago_row) > 0:
            value_12m_ago = value_12m_ago_row.iloc[0]['value']
            projected_yoy = ((current_value / value_12m_ago) - 1) * 100

            projections.append({
                'date': future_date,
                'category': category,
                'value': current_value,
                'yoy_change': projected_yoy,
                'is_projection': True,
                'assumption': mom_assumption
            })

    return pd.DataFrame(projections)


def identify_base_effect_periods(
    df: pd.DataFrame,
    category: str = "All-items",
    yoy_threshold: float = 0.5,
    mom_threshold: float = 0.2
) -> pd.DataFrame:
    """
    Identify periods where base effects are significant.

    A base effect period is when:
    - YoY inflation changes by more than yoy_threshold
    - BUT MoM inflation is within mom_threshold (stable)

    Args:
        df: CPI DataFrame with inflation metrics
        category: Category to analyze
        yoy_threshold: Minimum YoY change to consider significant (percentage points)
        mom_threshold: Maximum MoM to consider "stable" (percentage points)

    Returns:
        DataFrame with periods flagged as base effect driven
    """
    cat_data = df[df['category'] == category].copy()
    cat_data = cat_data.sort_values('date')

    # Calculate change in YoY (how much did YoY move this month?)
    cat_data['yoy_change_delta'] = cat_data['yoy_change'].diff()

    # Flag base effect periods
    cat_data['is_base_effect'] = (
        (abs(cat_data['yoy_change_delta']) > yoy_threshold) &
        (abs(cat_data['mom_change']) < mom_threshold)
    )

    return cat_data[cat_data['is_base_effect']]


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
