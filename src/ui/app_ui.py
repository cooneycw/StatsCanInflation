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
                ui.h4("Display Options"),
                ui.input_slider(
                    "recent_months",
                    "Number of months to display:",
                    min=6,
                    max=36,
                    value=24,
                    step=6
                ),
                ui.input_checkbox_group(
                    "recent_categories",
                    "Categories to display:",
                    choices={
                        "All-items": "All-items (Overall CPI)",
                        "Food": "Food",
                        "Shelter": "Shelter",
                        "Transportation": "Transportation",
                        "Gasoline": "Gasoline",
                        "Health and personal care": "Health and personal care",
                    },
                    selected=["All-items", "Food", "Shelter", "Transportation"]
                ),
                width=300
            ),
            ui.h3("Recent Inflation Trends"),
            ui.row(
                ui.column(6, ui.output_ui("recent_summary_cards")),
                ui.column(6, ui.output_ui("recent_latest_values")),
            ),
            ui.hr(),
            ui.h4("Year-over-Year Inflation Trends"),
            ui.output_plot("recent_yoy_plot", height="400px"),
            ui.hr(),
            ui.h4("Month-over-Month Changes"),
            ui.output_plot("recent_mom_plot", height="400px"),
            ui.hr(),
            ui.h4("Recent Data Table"),
            ui.output_data_frame("recent_data_table"),
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
                        "All-items": "All-items (Overall CPI)",
                        "Food": "Food",
                        "Shelter": "Shelter",
                        "Transportation": "Transportation",
                        "Gasoline": "Gasoline",
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
            ui.h4("CPI Index Over Time"),
            ui.output_plot("historical_cpi_plot", height="400px"),
            ui.hr(),
            ui.h4("Year-over-Year Inflation Rate"),
            ui.output_plot("historical_yoy_plot", height="400px"),
            ui.hr(),
            ui.h4("Cumulative Inflation Since Start of Period"),
            ui.output_plot("historical_cumulative_plot", height="400px"),
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
            ui.output_plot("breakdown_bar_chart", height="500px"),
            ui.hr(),
            ui.h4("Detailed Category Table"),
            ui.output_data_frame("breakdown_table"),
            ui.hr(),
            ui.h4("Category Trends (Last 12 Months)"),
            ui.output_plot("breakdown_trends_plot", height="400px"),
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
                        "Food": "Food",
                        "Shelter": "Shelter",
                        "Transportation": "Transportation",
                        "Gasoline": "Gasoline",
                        "Health and personal care": "Health",
                        "Recreation, education and reading": "Recreation & Education",
                        "Clothing and footwear": "Clothing",
                        "Household operations, furnishings and equipment": "Household Ops",
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
            ui.output_plot("custom_comparison_plot", height="400px"),
            ui.hr(),
            ui.h4("Statistical Summary"),
            ui.output_ui("custom_stats_summary"),
            ui.hr(),
            ui.h4("Filtered Data"),
            ui.output_data_frame("custom_data_table"),
        )
    )


# Main UI definition
app_ui = ui.page_navbar(
    create_recent_trends_tab(),
    create_historical_tab(),
    create_category_breakdown_tab(),
    create_custom_analysis_tab(),
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
