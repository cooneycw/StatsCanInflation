"""
Shiny Server Logic

Complete server-side logic for the Statistics Canada Inflation Analysis app.
Handles data loading, reactive calculations, and all output rendering.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from shiny import render, reactive, ui
from htmltools import HTML
import logging
import io
from datetime import datetime

from ..data.cache import get_cached_or_download, get_cache_info
from ..models.inflation import (
    add_all_inflation_metrics,
    get_latest_inflation_rate,
    get_inflation_summary_stats,
)
from ..models.analysis import (
    get_recent_trends,
    get_historical_comparison,
    get_category_breakdown,
    get_category_trends,
)
from ..utils.formatting import (
    format_percentage,
    format_date,
    format_date_short,
    format_change_with_indicator,
    sort_categories,
)
from ..utils.export import create_excel_report, create_simple_csv_export

logger = logging.getLogger(__name__)


def server(input, output, session):
    """Main server function for the Shiny app."""

    # ===== INITIAL DATA LOADING =====
    # Load data eagerly when session starts to ensure charts display immediately
    logger.info("Loading initial CPI data...")
    try:
        initial_df = get_cached_or_download(force_refresh=False)
        initial_df = add_all_inflation_metrics(initial_df)
        logger.info(f"Loaded {len(initial_df)} data points")
    except Exception as e:
        logger.error(f"Failed to load initial data: {e}")
        initial_df = None

    # ===== REACTIVE VALUES =====

    # Store the CPI data
    cpi_data = reactive.Value(initial_df)

    # Track when data was last loaded
    data_load_time = reactive.Value(datetime.now() if initial_df is not None else None)

    # ===== DATA LOADING =====

    @reactive.Effect
    @reactive.event(input.load_cached_data)
    def load_cached_data():
        """Load data from cache when user clicks Load Cached Data button."""
        logger.info("Loading CPI data from cache...")
        ui.notification_show(
            "Loading cached data...",
            duration=2,
            type="message"
        )

        try:
            df = get_cached_or_download(force_refresh=False)
            df = add_all_inflation_metrics(df)
            cpi_data.set(df)
            data_load_time.set(datetime.now())
            ui.notification_show("Data loaded successfully!", type="message", duration=3)
            logger.info("Data load complete")
        except Exception as e:
            logger.error(f"Data load failed: {e}")
            ui.notification_show(
                f"Failed to load data: {str(e)}",
                type="error",
                duration=10
            )

    @reactive.Effect
    @reactive.event(input.refresh_data)
    def refresh_data():
        """Refresh data when user clicks refresh button."""
        logger.info("Refreshing CPI data...")
        ui.notification_show(
            "Downloading latest data from Statistics Canada... (This may take 30-60 seconds)",
            duration=5,
            type="message"
        )

        try:
            df = get_cached_or_download(force_refresh=True)
            df = add_all_inflation_metrics(df)
            cpi_data.set(df)
            data_load_time.set(datetime.now())
            ui.notification_show("Data refreshed successfully!", type="message", duration=3)
            logger.info("Data refresh complete")
        except Exception as e:
            logger.error(f"Data refresh failed: {e}")
            ui.notification_show(
                f"Failed to refresh data: {str(e)}",
                type="error",
                duration=10
            )

    # ===== HEADER OUTPUTS =====

    @output
    @render.ui
    def last_updated_info():
        """Display last updated timestamp and cache info."""
        df = cpi_data.get()
        if df is None:
            return ui.p("Loading data...", class_="text-muted")

        cache_info = get_cache_info()
        load_time = data_load_time.get()

        if load_time:
            load_time_str = load_time.strftime("%Y-%m-%d %H:%M")
        else:
            load_time_str = "Unknown"

        latest_data_date = df['date'].max().strftime("%B %Y")

        return ui.div(
            ui.p(f"Latest data: {latest_data_date}", class_="text-muted", style="margin: 0;"),
            ui.p(f"Loaded: {load_time_str}", class_="text-muted", style="margin: 0;"),
        )

    # ===== RECENT TRENDS TAB =====

    @reactive.Calc
    def get_recent_data():
        """Get recent trends data based on user selections."""
        df = cpi_data.get()
        if df is None:
            return None

        months = input.recent_months()
        categories = list(input.recent_categories())

        if not categories:
            categories = ["All-items"]

        return get_recent_trends(df, months=months, categories=categories)

    # ===== NEW ENHANCED METRIC CARDS =====

    @output
    @render.ui
    def metric_current_inflation():
        """Display current inflation rate metric."""
        df = cpi_data.get()
        if df is None:
            return ui.p("Loading...")

        latest = get_latest_inflation_rate(df, "All-items")

        return ui.div(
            ui.div("Current Inflation (YoY)", class_="metric-label"),
            ui.div(format_percentage(latest['yoy_change'], decimals=1), class_="metric-value"),
            ui.div(format_date(latest['date']), class_="metric-change", style="font-size: 11px;"),
            class_="metric-card"
        )

    @output
    @render.ui
    def metric_mom_change():
        """Display month-over-month change."""
        df = cpi_data.get()
        if df is None:
            return ui.p("Loading...")

        latest = get_latest_inflation_rate(df, "All-items")

        color = "positive" if latest['mom_change'] > 0 else "negative" if latest['mom_change'] < 0 else "neutral"

        return ui.div(
            ui.div("Last Month Change", class_="metric-label"),
            ui.div(
                format_change_with_indicator(latest['mom_change']),
                class_=f"metric-value {color}",
                style="font-size: 20px;"
            ),
            ui.div("Month-over-Month", class_="metric-change", style="font-size: 11px;"),
            class_="metric-card"
        )

    @output
    @render.ui
    def metric_trend_direction():
        """Display trend direction (3-month average)."""
        df = cpi_data.get()
        if df is None:
            return ui.p("Loading...")

        # Get All-items data
        all_items = df[df['category'] == 'All-items'].sort_values('date').tail(4)

        if len(all_items) < 4:
            return ui.div("Insufficient data", class_="metric-card")

        # Calculate trend (3-month average vs previous period)
        recent_avg = all_items.tail(3)['yoy_change'].mean()
        previous_avg = all_items.head(3)['yoy_change'].mean()
        trend = recent_avg - previous_avg

        trend_text = "Rising" if trend > 0.1 else "Falling" if trend < -0.1 else "Stable"
        color = "positive" if trend > 0.1 else "negative" if trend < -0.1 else "neutral"
        arrow = "↑" if trend > 0.1 else "↓" if trend < -0.1 else "→"

        return ui.div(
            ui.div("3-Month Trend", class_="metric-label"),
            ui.div(f"{arrow} {trend_text}", class_=f"metric-value {color}", style="font-size: 20px;"),
            ui.div(format_percentage(trend, decimals=2, include_sign=True), class_="metric-change"),
            class_="metric-card"
        )

    @output
    @render.ui
    def metric_acceleration():
        """Display inflation acceleration/deceleration."""
        df = cpi_data.get()
        if df is None:
            return ui.p("Loading...")

        # Get All-items recent data
        all_items = df[df['category'] == 'All-items'].sort_values('date').tail(3)

        if len(all_items) < 3:
            return ui.div("Insufficient data", class_="metric-card")

        # Calculate acceleration (change in YoY rate)
        current_yoy = all_items.iloc[-1]['yoy_change']
        previous_yoy = all_items.iloc[-2]['yoy_change']
        acceleration = current_yoy - previous_yoy

        accel_text = "Accelerating" if acceleration > 0.1 else "Decelerating" if acceleration < -0.1 else "Steady"
        color = "positive" if acceleration < -0.1 else "negative" if acceleration > 0.1 else "neutral"

        return ui.div(
            ui.div("Inflation Momentum", class_="metric-label"),
            ui.div(accel_text, class_=f"metric-value {color}", style="font-size: 18px;"),
            ui.div(
                format_percentage(acceleration, decimals=2, include_sign=True) + " vs prev month",
                class_="metric-change"
            ),
            class_="metric-card"
        )

    @output
    @render.ui
    def recent_yoy_plot():
        """Plot year-over-year inflation trends with enhanced features."""
        recent_data = get_recent_data()
        if recent_data is None or len(recent_data) == 0:
            return ui.p("No data available")

        # Get sorted category order for legend
        categories = recent_data['category'].unique().tolist()
        sorted_cats = sort_categories(categories)

        fig = px.line(
            recent_data,
            x='date',
            y='yoy_change',
            color='category',
            labels={'yoy_change': 'YoY Inflation (%)', 'date': 'Date', 'category': 'Category'},
            category_orders={'category': sorted_cats}
        )

        # Add 2% inflation target line if requested
        if input.show_target_line():
            fig.add_hline(
                y=2.0,
                line_dash="dash",
                line_color="gray",
                annotation_text="Bank of Canada 2% Target",
                annotation_position="right"
            )

        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_title="",
            yaxis_title="Year-over-Year Inflation (%)",
            height=450,
            margin=dict(t=20, b=40)
        )

        # Configure plotly to avoid WebGL rendering issues
        config = {
            'responsive': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }

        return HTML(fig.to_html(include_plotlyjs='cdn', config=config))

    @output
    @render.ui
    def inflation_acceleration_plot():
        """Plot inflation acceleration/deceleration (change in YoY rate)."""
        recent_data = get_recent_data()
        if recent_data is None or len(recent_data) == 0:
            return ui.p("No data available")

        # Calculate acceleration for each category
        accel_data = []
        for category in recent_data['category'].unique():
            cat_data = recent_data[recent_data['category'] == category].sort_values('date')
            cat_data = cat_data.copy()
            cat_data['acceleration'] = cat_data['yoy_change'].diff()
            accel_data.append(cat_data)

        accel_df = pd.concat(accel_data, ignore_index=True)

        fig = go.Figure()

        for category in accel_df['category'].unique():
            cat_data = accel_df[accel_df['category'] == category]

            # Create bar chart with conditional coloring
            colors = ['red' if x > 0 else 'green' for x in cat_data['acceleration']]

            fig.add_trace(go.Bar(
                x=cat_data['date'],
                y=cat_data['acceleration'],
                name=category,
                marker_color=colors if category == 'All-items' else None,
                opacity=0.7
            ))

        fig.update_layout(
            yaxis_title="Change in YoY Inflation (percentage points)",
            xaxis_title="",
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=350,
            margin=dict(t=20, b=40),
            showlegend=len(accel_df['category'].unique()) > 1
        )

        fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)

        config = {
            'responsive': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }

        return HTML(fig.to_html(include_plotlyjs='cdn', config=config))

    @output
    @render.ui
    def rolling_averages_plot():
        """Plot rolling averages for All-items inflation."""
        df = cpi_data.get()
        if df is None:
            return ui.p("Loading...")

        # Get All-items data for the recent period
        months = input.recent_months()
        all_items = df[df['category'] == 'All-items'].copy()
        all_items = all_items.sort_values('date')

        # Get recent data
        cutoff_date = all_items['date'].max() - pd.DateOffset(months=months)
        all_items = all_items[all_items['date'] >= cutoff_date]

        fig = go.Figure()

        # Add YoY line
        fig.add_trace(go.Scatter(
            x=all_items['date'],
            y=all_items['yoy_change'],
            name='YoY (Monthly)',
            line=dict(color='lightgray', width=1),
            opacity=0.5
        ))

        # Add rolling averages
        fig.add_trace(go.Scatter(
            x=all_items['date'],
            y=all_items['yoy_change_rolling_3m'],
            name='3-Month Average',
            line=dict(color='blue', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=all_items['date'],
            y=all_items['yoy_change_rolling_6m'],
            name='6-Month Average',
            line=dict(color='orange', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=all_items['date'],
            y=all_items['yoy_change_rolling_12m'],
            name='12-Month Average',
            line=dict(color='red', width=2, dash='dash')
        ))

        fig.update_layout(
            yaxis_title="Inflation Rate (%)",
            xaxis_title="",
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=350,
            margin=dict(t=20, b=40)
        )

        config = {
            'responsive': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }

        return HTML(fig.to_html(include_plotlyjs='cdn', config=config))

    @output
    @render.ui
    def category_heatmap():
        """Create heatmap of recent inflation by key categories."""
        df = cpi_data.get()
        if df is None:
            return ui.p("Loading...")

        # Get last 12 months of data for key categories only
        max_date = df['date'].max()
        cutoff_date = max_date - pd.DateOffset(months=12)

        # Define key categories: grouped + specific
        key_categories = [
            "All-items",
            "Goods",
            "Services",
            "Energy",
            "All-items excluding food and energy",
            "All-items excluding energy",
            "Food",
            "Shelter",
            "Household operations, furnishings and equipment",
            "Clothing and footwear",
            "Transportation",
            "Gasoline",
            "Health and personal care",
            "Recreation, education and reading",
            "Alcoholic beverages, tobacco products and recreational cannabis"
        ]

        # Sort categories using our standard ordering
        sorted_categories = sort_categories(key_categories)

        recent = df[
            (df['date'] >= cutoff_date) &
            (df['category'].isin(sorted_categories))
        ].copy()

        # Pivot to wide format for heatmap
        heatmap_data = recent.pivot(index='category', columns='date', values='yoy_change')

        # Reorder rows by sorted categories (reversed for bottom-to-top display)
        heatmap_data = heatmap_data.reindex(sorted_categories[::-1])

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=[d.strftime('%b %Y') for d in heatmap_data.columns],
            y=heatmap_data.index,
            colorscale='RdYlGn_r',
            zmid=2.0,  # Center at 2% target
            colorbar=dict(title="YoY %"),
            hovertemplate='%{y}<br>%{x}<br>%{z:.1f}%<extra></extra>'
        ))

        # Calculate height based on number of categories (at least 20px per category)
        height = max(400, len(sorted_categories) * 20)

        fig.update_layout(
            xaxis_title="",
            yaxis_title="",
            height=height,
            margin=dict(t=10, b=40, l=250, r=40)
        )

        config = {
            'responsive': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }

        return HTML(fig.to_html(include_plotlyjs='cdn', config=config))

    # ===== HISTORICAL TAB =====

    @reactive.Calc
    def get_historical_data():
        """Get historical data based on user selections."""
        df = cpi_data.get()
        if df is None:
            return None

        categories = list(input.historical_categories())
        if not categories:
            categories = ["All-items"]

        date_range = input.historical_date_range()
        start_date = date_range[0].strftime("%Y-%m-%d") if date_range else None
        end_date = date_range[1].strftime("%Y-%m-%d") if date_range else None

        result = get_historical_comparison(df, categories=categories)

        if start_date:
            result = result[result['date'] >= pd.to_datetime(start_date)]
        if end_date:
            result = result[result['date'] <= pd.to_datetime(end_date)]

        return result

    @output
    @render.ui
    def historical_summary_stats():
        """Display summary statistics for historical period."""
        historical_data = get_historical_data()
        if historical_data is None or len(historical_data) == 0:
            return ui.p("No data available")

        categories = list(input.historical_categories())
        if not categories:
            return None

        date_range = input.historical_date_range()
        start_date = date_range[0].strftime("%Y-%m-%d") if date_range else None
        end_date = date_range[1].strftime("%Y-%m-%d") if date_range else None

        stats_cards = []
        for category in categories:
            stats = get_inflation_summary_stats(
                cpi_data.get(),
                category=category,
                start_date=start_date,
                end_date=end_date
            )

            if stats:
                stats_cards.append(
                    ui.div(
                        ui.strong(category),
                        ui.br(),
                        f"Mean: {format_percentage(stats.get('mean_yoy', 0))}",
                        ui.br(),
                        f"Range: {format_percentage(stats.get('min_yoy', 0))} to {format_percentage(stats.get('max_yoy', 0))}",
                        class_="summary-stat"
                    )
                )

        return ui.div(*stats_cards, style="display: flex; flex-wrap: wrap;")

    @output
    @render.ui
    def historical_cpi_plot():
        """Plot historical CPI values."""
        historical_data = get_historical_data()
        if historical_data is None or len(historical_data) == 0:
            return ui.p("No data available")

        # Get sorted category order for legend
        categories = historical_data['category'].unique().tolist()
        sorted_cats = sort_categories(categories)

        fig = px.line(
            historical_data,
            x='date',
            y='value',
            color='category',
            title='Consumer Price Index (CPI) Over Time (Base 2002=100)',
            labels={'value': 'CPI Value', 'date': 'Date', 'category': 'Category'},
            category_orders={'category': sorted_cats}
        )

        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        config = {
            'responsive': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }

        return HTML(fig.to_html(include_plotlyjs='cdn', config=config))

    @output
    @render.ui
    def historical_yoy_plot():
        """Plot historical year-over-year inflation."""
        historical_data = get_historical_data()
        if historical_data is None or len(historical_data) == 0:
            return ui.p("No data available")

        # Get sorted category order for legend
        categories = historical_data['category'].unique().tolist()
        sorted_cats = sort_categories(categories)

        fig = px.line(
            historical_data,
            x='date',
            y='yoy_change',
            color='category',
            title='Year-over-Year Inflation Rate (%)',
            labels={'yoy_change': 'YoY Change (%)', 'date': 'Date', 'category': 'Category'},
            category_orders={'category': sorted_cats}
        )

        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        fig.add_hline(y=2.0, line_dash="dash", line_color="gray", annotation_text="2% Target")

        return HTML(fig.to_html(include_plotlyjs='cdn', config={'responsive': True}))

    @output
    @render.ui
    def historical_cumulative_plot():
        """Plot cumulative inflation from start of period."""
        historical_data = get_historical_data()
        df = cpi_data.get()

        if historical_data is None or len(historical_data) == 0 or df is None:
            return ui.p("No data available")

        date_range = input.historical_date_range()
        start_date = date_range[0].strftime("%Y-%m-%d") if date_range else None

        categories = list(input.historical_categories())

        # Calculate cumulative inflation for each category
        cumulative_data = []
        for category in categories:
            from ..models.inflation import calculate_cumulative_inflation
            cat_cumulative = calculate_cumulative_inflation(df, category, start_date)
            cumulative_data.append(cat_cumulative)

        if not cumulative_data:
            return ui.p("No data available")

        combined = pd.concat(cumulative_data, ignore_index=True)

        # Get sorted category order for legend
        categories_in_data = combined['category'].unique().tolist()
        sorted_cats = sort_categories(categories_in_data)

        fig = px.line(
            combined,
            x='date',
            y='cumulative_inflation',
            color='category',
            title='Cumulative Inflation from Start of Period (%)',
            labels={'cumulative_inflation': 'Cumulative Inflation (%)', 'date': 'Date', 'category': 'Category'},
            category_orders={'category': sorted_cats}
        )

        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        config = {
            'responsive': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }

        return HTML(fig.to_html(include_plotlyjs='cdn', config=config))

    # ===== DETAILED HEATMAP TAB =====

    @output
    @render.ui
    def detailed_category_heatmap():
        """Create detailed heatmap of recent inflation by ALL categories."""
        df = cpi_data.get()
        if df is None:
            return ui.p("Loading...")

        # Get months from input
        months = input.heatmap_months()
        max_date = df['date'].max()
        cutoff_date = max_date - pd.DateOffset(months=months)

        # Get all unique categories
        all_categories = df['category'].unique().tolist()

        # Sort categories using our standard ordering
        sorted_categories = sort_categories(all_categories)

        # Filter data
        recent = df[
            (df['date'] >= cutoff_date) &
            (df['category'].isin(sorted_categories))
        ].copy()

        # Pivot to wide format for heatmap
        heatmap_data = recent.pivot(index='category', columns='date', values='yoy_change')

        # Reorder rows by sorted categories (reversed for bottom-to-top display)
        heatmap_data = heatmap_data.reindex(sorted_categories[::-1])

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=[d.strftime('%b %Y') for d in heatmap_data.columns],
            y=heatmap_data.index,
            colorscale='RdYlGn_r',
            zmid=2.0,  # Center at 2% target
            colorbar=dict(title="YoY %"),
            hovertemplate='%{y}<br>%{x}<br>%{z:.1f}%<extra></extra>'
        ))

        # Calculate height based on number of categories (at least 20px per category)
        height = max(600, len(sorted_categories) * 20)

        fig.update_layout(
            xaxis_title="",
            yaxis_title="",
            height=height,
            margin=dict(t=10, b=40, l=250, r=40)
        )

        config = {
            'responsive': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }

        return HTML(fig.to_html(include_plotlyjs='cdn', config=config))

    # ===== CATEGORY BREAKDOWN TAB =====

    @reactive.Calc
    def get_breakdown_data():
        """Get category breakdown data."""
        df = cpi_data.get()
        if df is None:
            return None

        breakdown_date = input.breakdown_date()
        date_str = breakdown_date.strftime("%Y-%m-%d") if breakdown_date else None

        breakdown = get_category_breakdown(df, date=date_str)

        # Apply sorting
        sort_by = input.breakdown_sort()
        if sort_by == "yoy_desc":
            breakdown = breakdown.sort_values('yoy_change', ascending=False)
        elif sort_by == "yoy_asc":
            breakdown = breakdown.sort_values('yoy_change', ascending=True)
        elif sort_by == "category":
            breakdown = breakdown.sort_values('category')

        # Limit to top N
        top_n = input.breakdown_top_n()
        breakdown = breakdown.head(top_n)

        return breakdown

    @output
    @render.ui
    def breakdown_summary():
        """Display breakdown summary."""
        df = cpi_data.get()
        if df is None:
            return ui.p("Loading...")

        breakdown_date = input.breakdown_date()
        date_str = format_date(breakdown_date) if breakdown_date else format_date(df['date'].max())

        return ui.div(
            ui.h5(f"Inflation Breakdown for {date_str}"),
            class_="summary-stat"
        )

    @output
    @render.ui
    def breakdown_bar_chart():
        """Display bar chart of category inflation rates."""
        breakdown = get_breakdown_data()
        if breakdown is None or len(breakdown) == 0:
            return ui.p("No data available")

        # Determine y-axis ordering based on sort selection
        sort_by = input.breakdown_sort()
        if sort_by == "category":
            # Use custom category ordering
            categories_in_data = breakdown['category'].tolist()
            sorted_cats = sort_categories(categories_in_data)
            # Reverse for better display (top to bottom)
            sorted_cats_reversed = list(reversed(sorted_cats))
        else:
            sorted_cats_reversed = None

        fig = px.bar(
            breakdown,
            x='yoy_change',
            y='category',
            orientation='h',
            title='Year-over-Year Inflation by Category (%)',
            labels={'yoy_change': 'YoY Inflation (%)', 'category': 'Category'},
            color='yoy_change',
            color_continuous_scale='RdYlGn_r',
            category_orders={'category': sorted_cats_reversed} if sorted_cats_reversed else None
        )

        if not sorted_cats_reversed:
            # For value-based sorting, keep the original behavior
            fig.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=max(400, len(breakdown) * 25)
            )
        else:
            fig.update_layout(
                height=max(400, len(breakdown) * 25)
            )

        config = {
            'responsive': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }

        return HTML(fig.to_html(include_plotlyjs='cdn', config=config))

    @output
    @render.data_frame
    def breakdown_table():
        """Display detailed breakdown table."""
        breakdown = get_breakdown_data()
        if breakdown is None:
            return None

        table_data = breakdown[['category', 'value', 'yoy_change']].copy()
        table_data.columns = ['Category', 'Current CPI', 'YoY Inflation (%)']

        return render.DataGrid(table_data, width="100%", height="400px")

    @output
    @render.ui
    def breakdown_trends_plot():
        """Plot trends for top categories over last 12 months."""
        df = cpi_data.get()
        breakdown = get_breakdown_data()

        if df is None or breakdown is None or len(breakdown) == 0:
            return ui.p("No data available")

        # Get top 5 categories from breakdown
        top_categories = breakdown.head(5)['category'].tolist()

        # Get last 12 months of data for these categories
        trends = get_recent_trends(df, months=12, categories=top_categories)

        if len(trends) == 0:
            return ui.p("No data available")

        # Get sorted category order for legend
        categories_in_data = trends['category'].unique().tolist()
        sorted_cats = sort_categories(categories_in_data)

        fig = px.line(
            trends,
            x='date',
            y='yoy_change',
            color='category',
            title='Inflation Trends - Last 12 Months (Top 5 Categories)',
            labels={'yoy_change': 'YoY Inflation (%)', 'date': 'Date', 'category': 'Category'},
            category_orders={'category': sorted_cats}
        )

        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        config = {
            'responsive': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }

        return HTML(fig.to_html(include_plotlyjs='cdn', config=config))

    # ===== CUSTOM ANALYSIS TAB =====

    @reactive.Calc
    def get_custom_data():
        """Get custom filtered data."""
        df = cpi_data.get()
        if df is None:
            return None

        categories = list(input.custom_categories())
        if not categories:
            categories = ["All-items"]

        date_range = input.custom_date_range()
        start_date = date_range[0].strftime("%Y-%m-%d") if date_range else None
        end_date = date_range[1].strftime("%Y-%m-%d") if date_range else None

        result = get_category_trends(df, start_date=start_date, end_date=end_date)
        result = result[result['category'].isin(categories)]

        return result

    @output
    @render.ui
    def custom_period_summary():
        """Display summary for custom period."""
        custom_data = get_custom_data()
        if custom_data is None or len(custom_data) == 0:
            return ui.p("No data available for selected filters")

        date_range = input.custom_date_range()
        start = format_date_short(date_range[0]) if date_range else "Start"
        end = format_date_short(date_range[1]) if date_range else "End"

        return ui.div(
            ui.h5(f"Analysis Period: {start} to {end}"),
            ui.p(f"Data points: {len(custom_data):,}"),
            class_="summary-stat"
        )

    @output
    @render.ui
    def custom_comparison_plot():
        """Plot custom data comparison."""
        custom_data = get_custom_data()
        if custom_data is None or len(custom_data) == 0:
            return ui.p("No data available")

        # Get sorted category order for legend
        categories_in_data = custom_data['category'].unique().tolist()
        sorted_cats = sort_categories(categories_in_data)

        fig = px.line(
            custom_data,
            x='date',
            y='yoy_change',
            color='category',
            title='Year-over-Year Inflation Comparison',
            labels={'yoy_change': 'YoY Inflation (%)', 'date': 'Date', 'category': 'Category'},
            category_orders={'category': sorted_cats}
        )

        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        config = {
            'responsive': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }

        return HTML(fig.to_html(include_plotlyjs='cdn', config=config))

    @output
    @render.ui
    def custom_stats_summary():
        """Display statistical summary for custom period."""
        df = cpi_data.get()
        custom_data = get_custom_data()

        if df is None or custom_data is None or len(custom_data) == 0:
            return ui.p("No data available")

        categories = list(input.custom_categories())
        date_range = input.custom_date_range()
        start_date = date_range[0].strftime("%Y-%m-%d") if date_range else None
        end_date = date_range[1].strftime("%Y-%m-%d") if date_range else None

        stats_cards = []
        for category in categories:
            stats = get_inflation_summary_stats(df, category, start_date, end_date)

            if stats and stats.get('count', 0) > 0:
                stats_cards.append(
                    ui.div(
                        ui.strong(category),
                        ui.br(),
                        f"Mean: {format_percentage(stats.get('mean_yoy', 0))}",
                        ui.br(),
                        f"Median: {format_percentage(stats.get('median_yoy', 0))}",
                        ui.br(),
                        f"Std Dev: {format_percentage(stats.get('std_yoy', 0))}",
                        ui.br(),
                        f"Range: {format_percentage(stats.get('min_yoy', 0))} to {format_percentage(stats.get('max_yoy', 0))}",
                        class_="summary-stat"
                    )
                )

        if not stats_cards:
            return ui.p("No statistics available")

        return ui.div(*stats_cards, style="display: flex; flex-wrap: wrap;")

    @output
    @render.data_frame
    def custom_data_table():
        """Display custom filtered data table."""
        custom_data = get_custom_data()
        if custom_data is None:
            return None

        table_data = custom_data[['date', 'category', 'value', 'yoy_change']].copy()
        table_data['date'] = table_data['date'].apply(format_date_short)
        table_data.columns = ['Date', 'Category', 'CPI', 'YoY %']

        return render.DataGrid(table_data, width="100%", height="400px")

    # ===== DOWNLOAD HANDLERS =====

    @output
    @render.download(filename="inflation_analysis.xlsx")
    def download_excel():
        """Generate Excel report for download."""
        df = cpi_data.get()
        if df is None:
            return None

        categories = list(input.custom_categories())
        date_range = input.custom_date_range()
        start_date = date_range[0].strftime("%Y-%m-%d") if date_range else None
        end_date = date_range[1].strftime("%Y-%m-%d") if date_range else None

        excel_file = create_excel_report(
            df,
            categories=categories if categories else None,
            start_date=start_date,
            end_date=end_date
        )

        return excel_file

    @output
    @render.download(filename="inflation_data.csv")
    def download_csv():
        """Generate CSV data for download."""
        df = cpi_data.get()
        if df is None:
            return ""

        categories = list(input.custom_categories())
        date_range = input.custom_date_range()
        start_date = date_range[0].strftime("%Y-%m-%d") if date_range else None
        end_date = date_range[1].strftime("%Y-%m-%d") if date_range else None

        csv_data = create_simple_csv_export(
            df,
            categories=categories if categories else None,
            start_date=start_date,
            end_date=end_date
        )

        return csv_data

    # ===== DATA TABLE TAB =====

    @reactive.Effect
    @reactive.event(input.reset_table_focus)
    def reset_table_focus():
        """Reset the table focus filter to show all categories."""
        ui.update_select("table_focus_filter", selected="all")

    @reactive.Effect
    def populate_table_date_dropdowns():
        """Populate date dropdowns with available dates in yyyy-mm format."""
        df = cpi_data.get()
        if df is None:
            return

        # Get unique dates and format as yyyy-mm
        unique_dates = sorted(df['date'].unique(), reverse=True)
        date_choices = [d.strftime('%Y-%m') for d in unique_dates]

        # Update dropdown choices
        ui.update_select(
            "table_date_from",
            choices=date_choices,
            selected="2025-01" if "2025-01" in date_choices else date_choices[-1]
        )
        ui.update_select(
            "table_date_to",
            choices=date_choices,
            selected=date_choices[0]  # Latest date
        )

    @reactive.Calc
    def get_table_data():
        """Get data formatted for wide-format table display."""
        df = cpi_data.get()
        if df is None:
            return None

        # Apply date range filter using yyyy-mm selections
        date_from = input.table_date_from()
        date_to = input.table_date_to()

        if date_from and date_to:
            # Convert yyyy-mm to datetime for filtering
            start_date = pd.to_datetime(date_from + "-01")
            end_date = pd.to_datetime(date_to + "-01")

            # Filter data
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

        # Select value column based on type
        value_type = input.table_value_type()
        if value_type == "cpi":
            value_col = 'value'
        elif value_type == "yoy":
            value_col = 'yoy_change'
        else:  # mom
            value_col = 'mom_change'

        # Pivot to wide format: categories as rows, dates as columns
        wide_df = df.pivot(index='category', columns='date', values=value_col)

        # Format column names as YYYY-MM
        wide_df.columns = [col.strftime('%Y-%m') for col in wide_df.columns]

        # Reset index to make category a column
        wide_df = wide_df.reset_index()

        # Apply category ordering - priority categories first, then alphabetical
        categories = wide_df['category'].tolist()
        sorted_categories = sort_categories(categories)

        # Create a categorical type with the sorted order
        wide_df['category'] = pd.Categorical(
            wide_df['category'],
            categories=sorted_categories,
            ordered=True
        )

        # Sort by category using the custom ordering
        wide_df = wide_df.sort_values('category').reset_index(drop=True)

        # Apply letter range filter
        focus_filter = input.table_focus_filter()
        if focus_filter and focus_filter != "all":
            from ..utils.formatting import PRIORITY_CATEGORIES

            # Define letter ranges
            letter_ranges = {
                "a-c": ("A", "C"),
                "d-f": ("D", "F"),
                "g-i": ("G", "I"),
                "j-l": ("J", "L"),
                "m-o": ("M", "O"),
                "p-r": ("P", "R"),
                "s-t": ("S", "T"),
                "u-z": ("U", "Z")
            }

            if focus_filter in letter_ranges:
                start_letter, end_letter = letter_ranges[focus_filter]

                # Filter function to check if category is in range
                def in_letter_range(category):
                    # Always include priority categories
                    if category in PRIORITY_CATEGORIES:
                        return True
                    # Check if first letter is in range
                    first_letter = category[0].upper()
                    return start_letter <= first_letter <= end_letter

                # Apply filter
                wide_df = wide_df[wide_df['category'].apply(in_letter_range)].reset_index(drop=True)

        return wide_df

    @output
    @render.ui
    def wide_format_table():
        """Display data in wide format (categories as rows, dates as columns)."""
        table_data = get_table_data()
        if table_data is None or len(table_data) == 0:
            return ui.p("No data available")

        # Round numeric columns to 1 decimal place for better readability
        numeric_cols = table_data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            table_data[col] = table_data[col].round(1)

        # Build HTML table with right-aligned numeric columns
        from ..utils.formatting import PRIORITY_CATEGORIES

        # Create header row
        header_cells = []
        for col in table_data.columns:
            if col == 'category':
                header_cells.append(f'<th style="text-align: left; position: sticky; left: 0; background-color: #f8f9fa; z-index: 10; padding: 8px; border-bottom: 2px solid #dee2e6;">{col}</th>')
            else:
                # Right-align date headers
                header_cells.append(f'<th style="text-align: right; padding: 8px; border-bottom: 2px solid #dee2e6; white-space: nowrap;">{col}</th>')

        header_html = f'<tr>{"".join(header_cells)}</tr>'

        # Create data rows
        rows_html = []
        for idx, row in table_data.iterrows():
            category = row['category']

            # Determine row background color
            if category in PRIORITY_CATEGORIES:
                bg_color = "#e3f2fd"  # Light blue for priority categories
            else:
                # Alternating colors for non-priority
                non_priority_idx = idx - len([c for c in table_data['category'][:idx] if c in PRIORITY_CATEGORIES])
                bg_color = "#f5f5f5" if non_priority_idx % 2 == 0 else "#ffffff"

            cells = []
            for col in table_data.columns:
                value = row[col]
                if col == 'category':
                    # Category column - left-aligned, sticky
                    cells.append(f'<td style="text-align: left; position: sticky; left: 0; background-color: {bg_color}; z-index: 5; padding: 8px; border-bottom: 1px solid #dee2e6; font-weight: 500;">{value}</td>')
                else:
                    # Numeric columns - right-aligned
                    display_value = f"{value:.1f}" if pd.notna(value) else ""
                    cells.append(f'<td style="text-align: right; padding: 8px; border-bottom: 1px solid #dee2e6;">{display_value}</td>')

            rows_html.append(f'<tr style="background-color: {bg_color};">{"".join(cells)}</tr>')

        table_html = f'''
        <div style="width: 100%; height: 600px; overflow: auto; border: 1px solid #dee2e6; border-radius: 4px;">
            <table style="width: 100%; border-collapse: collapse; font-family: monospace; font-size: 13px;">
                <thead style="position: sticky; top: 0; background-color: #f8f9fa; z-index: 10;">
                    {header_html}
                </thead>
                <tbody>
                    {"".join(rows_html)}
                </tbody>
            </table>
        </div>
        '''

        return HTML(table_html)

    @output
    @render.download(filename="cpi_table_data.csv")
    def download_table_csv():
        """Download wide-format table as CSV."""
        table_data = get_table_data()
        if table_data is None:
            return ""

        # Convert to CSV
        csv_buffer = io.StringIO()
        table_data.to_csv(csv_buffer, index=False)

        return csv_buffer.getvalue()
