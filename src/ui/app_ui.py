"""
Shiny UI Definition

Complete user interface definition for the Statistics Canada Inflation Analysis app.
Follows the pattern of defining all inputs ONCE with unique IDs.

Four main tabs:
1. Recent Trends (last 12-24 months)
2. Historical Comparison (2008-present)
3. Category Breakdown
4. Custom Analysis
"""

from shiny import ui


def create_header_panel():
    """Create the header panel with refresh button and last updated info."""
    return ui.div(
        ui.row(
            ui.column(
                8,
                ui.h2("Canadian Inflation Analysis"),
                ui.p("Consumer Price Index (CPI) data from Statistics Canada", class_="text-muted"),
            ),
            ui.column(
                4,
                ui.div(
                    ui.input_action_button(
                        "refresh_data",
                        "Refresh Data",
                        class_="btn-primary",
                        icon=ui.tags.i(class_="fa fa-refresh")
                    ),
                    ui.output_ui("last_updated_info"),
                    class_="text-right",
                    style="text-align: right; padding-top: 10px;"
                ),
            ),
        ),
        class_="page-header"
    )


def create_recent_trends_tab():
    """Create the Recent Trends tab UI."""
    return ui.nav_panel(
        "Recent Trends",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Date Range"),
                ui.input_slider(
                    "recent_months",
                    "Months to display:",
                    min=6,
                    max=60,
                    value=24,
                    step=6
                ),
                ui.hr(),
                ui.h4("Categories"),
                ui.input_checkbox_group(
                    "recent_categories",
                    "Select categories:",
                    choices={
                        "All-items": "All-items",
                        "Goods": "Goods",
                        "Services": "Services",
                        "Energy": "Energy",
                        "All-items excluding food and energy": "All-items ex food & energy",
                        "All-items excluding energy": "All-items ex energy",
                        "Clothing and footwear": "Clothing",
                        "Food": "Food",
                        "Gasoline": "Gasoline",
                        "Health and personal care": "Health",
                        "Shelter": "Shelter",
                        "Transportation": "Transportation",
                    },
                    selected=["All-items", "Food", "Shelter"]
                ),
                ui.hr(),
                ui.input_checkbox(
                    "show_target_line",
                    "Show 2% inflation target",
                    value=True
                ),
                width=300
            ),
            ui.h3("Canadian Inflation Dashboard"),

            # Key Metrics Row
            ui.row(
                ui.column(3, ui.output_ui("metric_current_inflation")),
                ui.column(3, ui.output_ui("metric_mom_change")),
                ui.column(3, ui.output_ui("metric_trend_direction")),
                ui.column(3, ui.output_ui("metric_acceleration")),
            ),

            ui.hr(),

            # Main Inflation Chart
            ui.h4("Year-over-Year Inflation Rate"),
            ui.output_ui("recent_yoy_plot"),

            ui.hr(),

            # Two-column layout for additional charts
            ui.row(
                ui.column(
                    6,
                    ui.h4("Inflation Acceleration/Deceleration"),
                    ui.output_ui("inflation_acceleration_plot"),
                ),
                ui.column(
                    6,
                    ui.h4("Rolling Averages (All-items)"),
                    ui.output_ui("rolling_averages_plot"),
                ),
            ),

            ui.hr(),

            # Category Heatmap
            ui.h4("Recent Inflation by Category (Last 12 Months)"),
            ui.output_ui("category_heatmap"),
        )
    )


def create_historical_tab():
    """Create the Historical Comparison tab UI."""
    return ui.nav_panel(
        "Historical Comparison",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Analysis Options"),
                ui.input_checkbox_group(
                    "historical_categories",
                    "Categories:",
                    choices={
                        "All-items": "All-items",
                        "Goods": "Goods",
                        "Services": "Services",
                        "Energy": "Energy",
                        "All-items excluding food and energy": "All-items ex food & energy",
                        "All-items excluding energy": "All-items ex energy",
                        "Food": "Food",
                        "Gasoline": "Gasoline",
                        "Shelter": "Shelter",
                        "Transportation": "Transportation",
                    },
                    selected=["All-items"]
                ),
                ui.input_date_range(
                    "historical_date_range",
                    "Date Range:",
                    start="2008-01-01",
                    end=None,  # Will be set to current date in server
                ),
                width=300
            ),
            ui.h3("Historical Inflation Analysis (2008-Present)"),
            ui.row(
                ui.column(12, ui.output_ui("historical_summary_stats")),
            ),
            ui.hr(),
            ui.h4("Year-over-Year Inflation Rate"),
            ui.output_ui("historical_yoy_plot"),
            ui.hr(),
            ui.h4("Cumulative Inflation Since Start of Period"),
            ui.output_ui("historical_cumulative_plot"),
            ui.hr(),
            ui.h4("CPI Index Over Time"),
            ui.output_ui("historical_cpi_plot"),
        )
    )


def create_category_breakdown_tab():
    """Create the Category Breakdown tab UI."""
    return ui.nav_panel(
        "Category Breakdown",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Analysis Options"),
                ui.input_date(
                    "breakdown_date",
                    "Analysis Date:",
                    value=None,  # Will be set to latest date in server
                ),
                ui.input_radio_buttons(
                    "breakdown_sort",
                    "Sort by:",
                    choices={
                        "yoy_desc": "Highest Inflation First",
                        "yoy_asc": "Lowest Inflation First",
                        "category": "Category Name",
                    },
                    selected="yoy_desc"
                ),
                ui.input_slider(
                    "breakdown_top_n",
                    "Number of categories to display:",
                    min=5,
                    max=30,
                    value=15,
                    step=5
                ),
                width=300
            ),
            ui.h3("Inflation by Category"),
            ui.row(
                ui.column(12, ui.output_ui("breakdown_summary")),
            ),
            ui.hr(),
            ui.h4("Category Inflation Rates"),
            ui.output_ui("breakdown_bar_chart"),
            ui.hr(),
            ui.h4("Detailed Category Table"),
            ui.output_data_frame("breakdown_table"),
            ui.hr(),
            ui.h4("Category Trends (Last 12 Months)"),
            ui.output_ui("breakdown_trends_plot"),
        )
    )


def create_custom_analysis_tab():
    """Create the Custom Analysis tab UI."""
    return ui.nav_panel(
        "Custom Analysis",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Custom Filters"),
                ui.input_date_range(
                    "custom_date_range",
                    "Date Range:",
                    start="2020-01-01",
                    end=None,
                ),
                ui.input_checkbox_group(
                    "custom_categories",
                    "Select Categories:",
                    choices={
                        "All-items": "All-items",
                        "Goods": "Goods",
                        "Services": "Services",
                        "Energy": "Energy",
                        "All-items excluding food and energy": "All-items ex food & energy",
                        "All-items excluding energy": "All-items ex energy",
                        "Clothing and footwear": "Clothing",
                        "Food": "Food",
                        "Gasoline": "Gasoline",
                        "Health and personal care": "Health",
                        "Household operations, furnishings and equipment": "Household Ops",
                        "Recreation, education and reading": "Recreation & Education",
                        "Shelter": "Shelter",
                        "Transportation": "Transportation",
                    },
                    selected=["All-items", "Food", "Shelter"]
                ),
                ui.hr(),
                ui.h4("Export Options"),
                ui.download_button("download_excel", "Download Excel Report"),
                ui.download_button("download_csv", "Download CSV Data"),
                width=300
            ),
            ui.h3("Custom Inflation Analysis"),
            ui.row(
                ui.column(12, ui.output_ui("custom_period_summary")),
            ),
            ui.hr(),
            ui.h4("Inflation Comparison"),
            ui.output_ui("custom_comparison_plot"),
            ui.hr(),
            ui.h4("Statistical Summary"),
            ui.output_ui("custom_stats_summary"),
            ui.hr(),
            ui.h4("Filtered Data"),
            ui.output_data_frame("custom_data_table"),
        )
    )


def create_detailed_heatmap_tab():
    """Create the Detailed Heatmap tab."""
    return ui.nav_panel(
        "Detailed Heatmap",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Display Options"),
                ui.input_slider(
                    "heatmap_months",
                    "Months to display:",
                    min=3,
                    max=24,
                    value=12,
                    step=3
                ),
                ui.hr(),
                ui.p("Showing inflation rates for all CPI categories", class_="text-muted", style="font-size: 12px;"),
                width=300
            ),
            ui.h3("Detailed Inflation Heatmap by Category"),
            ui.p("Year-over-year inflation rates for all categories. Color scale centered at 2% (Bank of Canada target)."),
            ui.output_ui("detailed_category_heatmap"),
        )
    )


def create_data_table_tab():
    """Create the Data Table tab with wide-format view."""
    return ui.nav_panel(
        "Data Table",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Table Options"),
                ui.input_radio_buttons(
                    "table_value_type",
                    "Show values as:",
                    choices={
                        "cpi": "CPI Index Values",
                        "yoy": "Year-over-Year %",
                        "mom": "Month-over-Month %"
                    },
                    selected="yoy"
                ),
                ui.hr(),
                ui.h4("Date Range"),
                ui.input_select(
                    "table_date_from",
                    "From:",
                    choices=["2025-01"],  # Will be populated by server
                    selected="2025-01"
                ),
                ui.input_select(
                    "table_date_to",
                    "To:",
                    choices=["2025-01"],  # Will be populated by server
                    selected="2025-01"
                ),
                ui.hr(),
                ui.h4("Category Focus"),
                ui.input_select(
                    "table_focus_filter",
                    "Filter categories by letter:",
                    choices={
                        "all": "All Categories",
                        "a-c": "A-C",
                        "d-f": "D-F",
                        "g-i": "G-I",
                        "j-l": "J-L",
                        "m-o": "M-O",
                        "p-r": "P-R",
                        "s-t": "S-T",
                        "u-z": "U-Z"
                    },
                    selected="all"
                ),
                ui.input_action_button(
                    "reset_table_focus",
                    "Reset Filter",
                    class_="btn-secondary btn-sm",
                    style="width: 100%; margin-top: 10px;"
                ),
                ui.hr(),
                ui.download_button("download_table_csv", "Download as CSV"),
                width=300
            ),
            ui.h3("CPI Data Table (Wide Format)"),
            ui.p("Categories as rows, dates as columns - matches original Statistics Canada format"),
            ui.p("Priority categories (All-items, Goods, Services, Energy, etc.) are listed first, followed by other categories alphabetically."),
            ui.output_data_frame("wide_format_table"),
        )
    )


# Main UI definition
app_ui = ui.page_navbar(
    create_recent_trends_tab(),
    create_historical_tab(),
    create_detailed_heatmap_tab(),
    # create_category_breakdown_tab(),  # Removed - replaced by detailed heatmap
    # create_custom_analysis_tab(),  # Removed from UI but backend functions remain
    create_data_table_tab(),
    title="Statistics Canada Inflation Analysis",
    id="main_navbar",
    fillable=True,
    header=ui.div(
        create_header_panel(),
        ui.tags.style("""
            .page-header {
                padding: 20px;
                margin-bottom: 20px;
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }
            .metric-card {
                padding: 15px;
                margin-bottom: 15px;
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .metric-value {
                font-size: 24px;
                font-weight: bold;
                color: #212529;
            }
            .metric-label {
                font-size: 14px;
                color: #6c757d;
                margin-bottom: 5px;
            }
            .metric-change {
                font-size: 16px;
                margin-top: 5px;
            }
            .positive {
                color: #dc3545;
            }
            .negative {
                color: #28a745;
            }
            .neutral {
                color: #6c757d;
            }
            .summary-stat {
                padding: 10px;
                margin: 5px;
                background-color: #f8f9fa;
                border-radius: 3px;
            }
            h3 {
                color: #212529;
                margin-bottom: 20px;
            }
            h4 {
                color: #495057;
                margin-top: 20px;
                margin-bottom: 15px;
            }
            .btn-primary {
                background-color: #0d6efd;
                border-color: #0d6efd;
            }
            .text-right {
                text-align: right;
            }
        """)
    ),
    footer=ui.div(
        ui.hr(),
        ui.p(
            "Data Source: Statistics Canada Table 18-10-0004-01 | ",
            "Consumer Price Index (CPI), monthly, not seasonally adjusted",
            class_="text-muted text-center",
            style="padding: 20px;"
        ),
    )
)
