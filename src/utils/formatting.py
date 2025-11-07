"""
Formatting Utilities

Functions for formatting numbers, dates, and percentages for display.
"""

import pandas as pd
from typing import Optional, Union


def format_percentage(
    value: Union[float, pd.Series],
    decimals: int = 2,
    include_sign: bool = False
) -> Union[str, pd.Series]:
    """
    Format a percentage value for display.

    Args:
        value: Numeric value or Series to format
        decimals: Number of decimal places
        include_sign: Whether to include + sign for positive values

    Returns:
        Formatted string or Series
    """
    if pd.isna(value).any() if isinstance(value, pd.Series) else pd.isna(value):
        if isinstance(value, pd.Series):
            return value.apply(lambda x: "N/A" if pd.isna(x) else _format_single_pct(x, decimals, include_sign))
        else:
            return "N/A"

    if isinstance(value, pd.Series):
        return value.apply(lambda x: _format_single_pct(x, decimals, include_sign))
    else:
        return _format_single_pct(value, decimals, include_sign)


def _format_single_pct(value: float, decimals: int, include_sign: bool) -> str:
    """Helper function to format a single percentage value."""
    if pd.isna(value):
        return "N/A"

    formatted = f"{value:.{decimals}f}%"

    if include_sign and value > 0:
        formatted = "+" + formatted

    return formatted


def format_cpi_value(
    value: Union[float, pd.Series],
    decimals: int = 1
) -> Union[str, pd.Series]:
    """
    Format a CPI value for display.

    Args:
        value: CPI value or Series to format
        decimals: Number of decimal places

    Returns:
        Formatted string or Series
    """
    if isinstance(value, pd.Series):
        return value.apply(lambda x: f"{x:.{decimals}f}" if not pd.isna(x) else "N/A")
    else:
        return f"{value:.{decimals}f}" if not pd.isna(value) else "N/A"


def format_date(
    date: Union[pd.Timestamp, str],
    format: str = "%B %Y"
) -> str:
    """
    Format a date for display.

    Args:
        date: Date to format
        format: strftime format string (default: "Month Year")

    Returns:
        Formatted date string
    """
    if isinstance(date, str):
        date = pd.to_datetime(date)

    return date.strftime(format)


def format_date_short(date: Union[pd.Timestamp, str]) -> str:
    """
    Format a date in short format (MMM YYYY).

    Args:
        date: Date to format

    Returns:
        Formatted date string (e.g., "Jan 2024")
    """
    return format_date(date, "%b %Y")


def format_date_range(
    start_date: Union[pd.Timestamp, str],
    end_date: Union[pd.Timestamp, str]
) -> str:
    """
    Format a date range for display.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        Formatted date range string (e.g., "January 2023 - December 2024")
    """
    start_str = format_date(start_date)
    end_str = format_date(end_date)
    return f"{start_str} - {end_str}"


def create_sparkline_text(values: list, width: int = 10) -> str:
    """
    Create a simple text-based sparkline from values.

    Args:
        values: List of numeric values
        width: Number of characters for the sparkline

    Returns:
        Text sparkline using block characters
    """
    if not values or len(values) == 0:
        return ""

    # Remove NaN values
    clean_values = [v for v in values if not pd.isna(v)]

    if len(clean_values) == 0:
        return ""

    # Normalize values to 0-1 range
    min_val = min(clean_values)
    max_val = max(clean_values)

    if max_val == min_val:
        return "▄" * width

    normalized = [(v - min_val) / (max_val - min_val) for v in clean_values[-width:]]

    # Convert to block characters
    blocks = " ▁▂▃▄▅▆▇█"
    sparkline = ''.join([blocks[int(v * (len(blocks) - 1))] for v in normalized])

    return sparkline


def format_trend_indicator(value: float, threshold: float = 0.0) -> str:
    """
    Create a trend indicator (↑, ↓, or →).

    Args:
        value: Numeric value to assess trend
        threshold: Threshold for considering stable (default 0)

    Returns:
        Trend indicator character
    """
    if pd.isna(value):
        return "?"

    if abs(value) <= abs(threshold):
        return "→"
    elif value > threshold:
        return "↑"
    else:
        return "↓"


def format_change_with_indicator(
    value: float,
    decimals: int = 2,
    threshold: float = 0.0
) -> str:
    """
    Format a change value with trend indicator.

    Args:
        value: Change value
        decimals: Number of decimal places
        threshold: Threshold for stable trend

    Returns:
        Formatted string with indicator (e.g., "↑ +2.5%")
    """
    if pd.isna(value):
        return "N/A"

    indicator = format_trend_indicator(value, threshold)
    formatted_value = format_percentage(value, decimals, include_sign=True)

    return f"{indicator} {formatted_value}"


def format_large_number(
    value: Union[int, float],
    decimals: int = 1
) -> str:
    """
    Format large numbers with K, M, B suffixes.

    Args:
        value: Number to format
        decimals: Number of decimal places

    Returns:
        Formatted string (e.g., "1.5M")
    """
    if pd.isna(value):
        return "N/A"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000:.{decimals}f}B"
    elif abs_value >= 1_000_000:
        return f"{sign}{abs_value / 1_000_000:.{decimals}f}M"
    elif abs_value >= 1_000:
        return f"{sign}{abs_value / 1_000:.{decimals}f}K"
    else:
        return f"{sign}{abs_value:.{decimals}f}"


def colorize_percentage(value: float, reverse: bool = False) -> str:
    """
    Return a CSS color class based on percentage value.

    Args:
        value: Percentage value
        reverse: If True, positive is red (bad), negative is green (good)

    Returns:
        CSS color class name
    """
    if pd.isna(value):
        return "neutral"

    if value > 0:
        return "negative" if reverse else "positive"
    elif value < 0:
        return "positive" if reverse else "negative"
    else:
        return "neutral"


def format_summary_stats(stats: dict) -> str:
    """
    Format summary statistics dictionary as readable text.

    Args:
        stats: Dictionary with statistics (mean, min, max, etc.)

    Returns:
        Formatted multi-line string
    """
    lines = []

    if 'mean_yoy' in stats:
        lines.append(f"Mean: {format_percentage(stats['mean_yoy'], include_sign=True)}")
    if 'median_yoy' in stats:
        lines.append(f"Median: {format_percentage(stats['median_yoy'], include_sign=True)}")
    if 'min_yoy' in stats:
        lines.append(f"Min: {format_percentage(stats['min_yoy'], include_sign=True)}")
    if 'max_yoy' in stats:
        lines.append(f"Max: {format_percentage(stats['max_yoy'], include_sign=True)}")
    if 'std_yoy' in stats:
        lines.append(f"Std Dev: {format_percentage(stats['std_yoy'])}")

    return "\n".join(lines)


def create_formatted_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a formatted copy of DataFrame suitable for display.

    Formats common columns like:
    - date → formatted date string
    - value → CPI value with 1 decimal
    - *_change → percentage with 2 decimals
    - category → title case

    Args:
        df: DataFrame to format

    Returns:
        Formatted DataFrame copy
    """
    result = df.copy()

    # Format date column if present
    if 'date' in result.columns:
        result['date'] = result['date'].apply(format_date_short)

    # Format CPI value if present
    if 'value' in result.columns:
        result['value'] = format_cpi_value(result['value'])

    # Format percentage change columns
    for col in result.columns:
        if col.endswith('_change') or col.startswith('yoy') or col.startswith('mom'):
            result[col] = format_percentage(result[col], include_sign=True)

    # Format category names (title case)
    if 'category' in result.columns:
        result['category'] = result['category'].str.title()

    return result
