"""
Unit tests for inflation calculations
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.inflation import (
    calculate_mom_change,
    calculate_yoy_change,
    add_all_inflation_metrics,
    get_latest_inflation_rate,
)
from src.models.analysis import (
    get_recent_trends,
    get_category_breakdown,
)


@pytest.fixture
def sample_cpi_data():
    """Create sample CPI data for testing."""
    dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='MS')
    categories = ['All-items', 'Food', 'Shelter']

    data = []
    for category in categories:
        base_value = 100
        for i, date in enumerate(dates):
            # Simulate CPI growth
            value = base_value * (1 + 0.02) ** (i / 12)  # 2% annual growth
            data.append({
                'date': date,
                'category': category,
                'value': value
            })

    return pd.DataFrame(data)


class TestInflationCalculations:
    """Test inflation calculation functions."""

    def test_mom_calculation(self, sample_cpi_data):
        """Test month-over-month calculation."""
        df = calculate_mom_change(sample_cpi_data)

        # Should have mom_change column
        assert 'mom_change' in df.columns

        # First value for each category should be NaN
        for category in df['category'].unique():
            cat_data = df[df['category'] == category]
            assert pd.isna(cat_data.iloc[0]['mom_change'])

        # MoM changes should be small for steady inflation
        valid_changes = df['mom_change'].dropna()
        assert all(abs(valid_changes) < 5)  # Should be less than 5% per month

    def test_yoy_calculation(self, sample_cpi_data):
        """Test year-over-year calculation."""
        df = calculate_yoy_change(sample_cpi_data)

        # Should have yoy_change column
        assert 'yoy_change' in df.columns

        # First 12 values should be NaN (no YoY comparison)
        for category in df['category'].unique():
            cat_data = df[df['category'] == category].sort_values('date')
            assert all(pd.isna(cat_data.head(12)['yoy_change']))

        # YoY changes should be around 2% (our growth rate)
        valid_changes = df['yoy_change'].dropna()
        mean_yoy = valid_changes.mean()
        assert 1.5 < mean_yoy < 2.5  # Should be close to 2%

    def test_add_all_metrics(self, sample_cpi_data):
        """Test adding all inflation metrics."""
        df = add_all_inflation_metrics(sample_cpi_data)

        # Should have all metric columns
        assert 'mom_change' in df.columns
        assert 'yoy_change' in df.columns
        assert 'yoy_change_rolling_3m' in df.columns
        assert 'yoy_change_rolling_6m' in df.columns
        assert 'yoy_change_rolling_12m' in df.columns

    def test_latest_inflation_rate(self, sample_cpi_data):
        """Test getting latest inflation rate."""
        df = add_all_inflation_metrics(sample_cpi_data)

        latest = get_latest_inflation_rate(df, 'All-items')

        # Should have required keys
        assert 'date' in latest
        assert 'cpi_value' in latest
        assert 'yoy_change' in latest

        # Date should be the most recent with valid YoY data
        assert latest['date'] <= df['date'].max()


class TestAnalysisFunctions:
    """Test analysis functions."""

    def test_recent_trends(self, sample_cpi_data):
        """Test recent trends analysis."""
        df = add_all_inflation_metrics(sample_cpi_data)

        recent = get_recent_trends(df, months=12, categories=['All-items'])

        # Should have 12 months of data
        assert len(recent[recent['category'] == 'All-items']) <= 12

        # Should only have requested category
        assert set(recent['category'].unique()) == {'All-items'}

    def test_category_breakdown(self, sample_cpi_data):
        """Test category breakdown."""
        df = add_all_inflation_metrics(sample_cpi_data)

        breakdown = get_category_breakdown(df)

        # Should have one row per category
        assert len(breakdown) == len(df['category'].unique())

        # Should be sorted by yoy_change
        assert all(breakdown['yoy_change'].iloc[i] >= breakdown['yoy_change'].iloc[i+1]
                  for i in range(len(breakdown)-1))


class TestDataValidation:
    """Test data validation and edge cases."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame(columns=['date', 'category', 'value'])

        result = calculate_mom_change(df)
        assert len(result) == 0

    def test_single_category(self, sample_cpi_data):
        """Test with single category."""
        single_cat = sample_cpi_data[sample_cpi_data['category'] == 'All-items'].copy()

        df = add_all_inflation_metrics(single_cat)

        assert 'yoy_change' in df.columns
        assert len(df) > 0

    def test_missing_values(self, sample_cpi_data):
        """Test handling of missing values."""
        # Introduce some missing values
        df = sample_cpi_data.copy()
        df.loc[5:10, 'value'] = np.nan

        result = calculate_yoy_change(df)

        # Should handle NaN gracefully
        assert 'yoy_change' in result.columns
