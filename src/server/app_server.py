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
import logging
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
)
from ..utils.export import create_excel_report, create_simple_csv_export

logger = logging.getLogger(__name__)


def server(input, output, session):
    """Main server function for the Shiny app."""

    # ===== REACTIVE VALUES =====

    # Store the CPI data
    cpi_data = reactive.Value(None)

    # Track when data was last loaded
    data_load_time = reactive.Value(None)

    # Track if this is the first load
    initial_load_complete = reactive.Value(False)

    # ===== DATA LOADING =====

    @reactive.Effect
    def load_initial_data():
        """Load data on app startup."""
        if not initial_load_complete.get():
            logger.info("Loading initial CPI data...")
            try:
                df = get_cached_or_download(force_refresh=False)
                df = add_all_inflation_metrics(df)
                cpi_data.set(df)
                data_load_time.set(datetime.now())
                initial_load_complete.set(True)
                logger.info(f"Loaded {len(df)} data points")
            except Exception as e:
                logger.error(f"Failed to load initial data: {e}")
                ui.notification_show(
                    f"Error loading data: {str(e)}",
                    type="error",
                    duration=10
                )

    @reactive.Effect
    @reactive.event(input.refresh_data)
    def refresh_data():
        """Refresh data when user clicks refresh button."""
        logger.info("Refreshing CPI data...")
        ui.notification_show("Downloading latest data from Statistics Canada...", duration=3)

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

    @output
    @render.ui
    def recent_summary_cards():
        """Display summary cards for recent trends."""
        df = cpi_data.get()
        if df is None:
            return ui.p("Loading...")

        # Get latest values for All-items
        latest = get_latest_inflation_rate(df, "All-items")

        return ui.div(
            ui.div(
                ui.div("Current Inflation", class_="metric-label"),
                ui.div(format_percentage(latest['yoy_change'], decimals=2), class_="metric-value"),
                ui.div(
                    format_change_with_indicator(latest['mom_change']),
                    " vs last month",
                    class_="metric-change"
                ),
                class_="metric-card"
            ),
        )

    @output
    @render.ui
    def recent_latest_values():
        """Display latest values for selected categories."""
        df = cpi_data.get()
        recent_data = get_recent_data()

        if df is None or recent_data is None:
            return ui.p("Loading...")

        categories = list(input.recent_categories())
        if not categories:
            return None

        cards = []
        for category in categories[:3]:  # Show up to 3 categories
            if category in df['category'].values:
                latest = get_latest_inflation_rate(df, category)
                cards.append(
                    ui.div(
                        ui.div(category, class_="metric-label"),
                        ui.div(
                            format_percentage(latest['yoy_change'], decimals=2),
                            class_="metric-value",
                            style="font-size: 18px;"
                        ),
                        class_="metric-card"
                    )
                )

        return ui.div(*cards)

    @output
    @render.plot
    def recent_yoy_plot():
        """Plot year-over-year inflation trends."""
        recent_data = get_recent_data()
        if recent_data is None or len(recent_data) == 0:
            return None

        fig = px.line(
            recent_data,
            x='date',
            y='yoy_change',
            color='category',
            title='Year-over-Year Inflation Rate (%)',
            labels={'yoy_change': 'YoY Change (%)', 'date': 'Date', 'category': 'Category'}
        )

        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_title="Date",
            yaxis_title="YoY Inflation (%)"
        )

        return fig

    @output
    @render.plot
    def recent_mom_plot():
        """Plot month-over-month changes."""
        recent_data = get_recent_data()
        if recent_data is None or len(recent_data) == 0:
            return None

        fig = px.line(
            recent_data,
            x='date',
            y='mom_change',
            color='category',
            title='Month-over-Month CPI Change (%)',
            labels={'mom_change': 'MoM Change (%)', 'date': 'Date', 'category': 'Category'}
        )

        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_title="Date",
            yaxis_title="MoM Change (%)"
        )

        return fig

    @output
    @render.data_frame
    def recent_data_table():
        """Display recent data in table format."""
        recent_data = get_recent_data()
        if recent_data is None:
            return None

        # Select and format columns
        table_data = recent_data[['date', 'category', 'value', 'mom_change', 'yoy_change']].copy()
        table_data['date'] = table_data['date'].apply(format_date_short)
        table_data.columns = ['Date', 'Category', 'CPI', 'MoM %', 'YoY %']

        return render.DataGrid(table_data, width="100%", height="400px")

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
    @render.plot
    def historical_cpi_plot():
        """Plot historical CPI values."""
        historical_data = get_historical_data()
        if historical_data is None or len(historical_data) == 0:
            return None

        fig = px.line(
            historical_data,
            x='date',
            y='value',
            color='category',
            title='Consumer Price Index (CPI) Over Time (Base 2002=100)',
            labels={'value': 'CPI Value', 'date': 'Date', 'category': 'Category'}
        )

        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        return fig

    @output
    @render.plot
    def historical_yoy_plot():
        """Plot historical year-over-year inflation."""
        historical_data = get_historical_data()
        if historical_data is None or len(historical_data) == 0:
            return None

        fig = px.line(
            historical_data,
            x='date',
            y='yoy_change',
            color='category',
            title='Year-over-Year Inflation Rate (%)',
            labels={'yoy_change': 'YoY Change (%)', 'date': 'Date', 'category': 'Category'}
        )

        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        fig.add_hline(y=2.0, line_dash="dash", line_color="gray", annotation_text="2% Target")

        return fig

    @output
    @render.plot
    def historical_cumulative_plot():
        """Plot cumulative inflation from start of period."""
        historical_data = get_historical_data()
        df = cpi_data.get()

        if historical_data is None or len(historical_data) == 0 or df is None:
            return None

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
            return None

        combined = pd.concat(cumulative_data, ignore_index=True)

        fig = px.line(
            combined,
            x='date',
            y='cumulative_inflation',
            color='category',
            title='Cumulative Inflation from Start of Period (%)',
            labels={'cumulative_inflation': 'Cumulative Inflation (%)', 'date': 'Date', 'category': 'Category'}
        )

        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        return fig

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
    @render.plot
    def breakdown_bar_chart():
        """Display bar chart of category inflation rates."""
        breakdown = get_breakdown_data()
        if breakdown is None or len(breakdown) == 0:
            return None

        fig = px.bar(
            breakdown,
            x='yoy_change',
            y='category',
            orientation='h',
            title='Year-over-Year Inflation by Category (%)',
            labels={'yoy_change': 'YoY Inflation (%)', 'category': 'Category'},
            color='yoy_change',
            color_continuous_scale='RdYlGn_r'
        )

        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=max(400, len(breakdown) * 25)
        )

        return fig

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
    @render.plot
    def breakdown_trends_plot():
        """Plot trends for top categories over last 12 months."""
        df = cpi_data.get()
        breakdown = get_breakdown_data()

        if df is None or breakdown is None or len(breakdown) == 0:
            return None

        # Get top 5 categories from breakdown
        top_categories = breakdown.head(5)['category'].tolist()

        # Get last 12 months of data for these categories
        trends = get_recent_trends(df, months=12, categories=top_categories)

        if len(trends) == 0:
            return None

        fig = px.line(
            trends,
            x='date',
            y='yoy_change',
            color='category',
            title='Inflation Trends - Last 12 Months (Top 5 Categories)',
            labels={'yoy_change': 'YoY Inflation (%)', 'date': 'Date', 'category': 'Category'}
        )

        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        return fig

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
    @render.plot
    def custom_comparison_plot():
        """Plot custom data comparison."""
        custom_data = get_custom_data()
        if custom_data is None or len(custom_data) == 0:
            return None

        fig = px.line(
            custom_data,
            x='date',
            y='yoy_change',
            color='category',
            title='Year-over-Year Inflation Comparison',
            labels={'yoy_change': 'YoY Inflation (%)', 'date': 'Date', 'category': 'Category'}
        )

        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        return fig

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
