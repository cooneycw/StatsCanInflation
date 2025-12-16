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
                        "load_cached_data",
                        "Load Cached Data",
                        class_="btn-success",
                        icon=ui.tags.i(class_="fa fa-database"),
                        style="margin-right: 10px;"
                    ),
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
                        "Alcoholic beverages, tobacco products and recreational cannabis": "Alcohol, tobacco & cannabis",
                        "Clothing and footwear": "Clothing",
                        "Food": "Food",
                        "Gasoline": "Gasoline",
                        "Health and personal care": "Health",
                        "Household operations, furnishings and equipment": "Household ops",
                        "Recreation, education and reading": "Recreation & education",
                        "Shelter": "Shelter",
                        "Transportation": "Transportation",
                    },
                    selected=["All-items", "Goods", "Services"]
                ),
                ui.hr(),
                ui.h4("Display Options"),
                ui.input_checkbox(
                    "show_target_line",
                    "Show 2% inflation target",
                    value=True
                ),
                ui.input_checkbox(
                    "show_base_effects",
                    "Show base effects analysis",
                    value=True
                ),
                ui.div(
                    ui.input_radio_buttons(
                        "base_effects_momentum",
                        "Momentum period:",
                        choices={
                            "monthly": "Monthly (noisy)",
                            "quarterly": "Quarterly (3-month avg)",
                            "half_year": "Half-year (6-month avg)"
                        },
                        selected="quarterly",
                        inline=False
                    ),
                    ui.p(
                        "Longer momentum periods smooth out volatility to show underlying trends.",
                        style="font-size: 11px; color: #6c757d; margin-top: 5px;"
                    ),
                    id="base_effects_options"
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

            # Base Effects Analysis (conditional)
            ui.output_ui("base_effects_section"),

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
                        "Alcoholic beverages, tobacco products and recreational cannabis": "Alcohol, tobacco & cannabis",
                        "Clothing and footwear": "Clothing",
                        "Food": "Food",
                        "Gasoline": "Gasoline",
                        "Health and personal care": "Health",
                        "Household operations, furnishings and equipment": "Household ops",
                        "Recreation, education and reading": "Recreation & education",
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
                    selected=["All-items", "Goods", "Services"]
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


def create_research_tab():
    """Create the Research tab with methodology documentation."""
    return ui.nav_panel(
        "Research",
        ui.h3("Base Effects Methodology & Research"),
        ui.p(
            "This application's base effects analysis follows the methodology recommended by "
            "central banks and economic research institutions."
        ),

        ui.h4("📄 Research Paper"),
        ui.div(
            ui.h5("Understanding and Predicting Base Effects in Canadian Inflation"),
            ui.p(
                "A comprehensive guide to base effects in Canadian inflation from 2020-2025, "
                "covering the mathematical foundations, practical calculation methods, and "
                "historical episodes that shaped Canadian inflation readings."
            ),
            ui.tags.ul(
                ui.tags.li("Core formula: Base Effect = YoY Inflation − Annualized MoM"),
                ui.tags.li("Practical Excel-based tracking tools"),
                ui.tags.li("Analysis of 9 major base effect episodes (2020-2025)"),
                ui.tags.li("Forward-looking prediction methodology"),
            ),
            ui.download_button(
                "download_research_pdf",
                "Download Research Paper (PDF)",
                class_="btn-primary",
                style="margin-top: 15px; margin-bottom: 20px;"
            ),
            class_="metric-card"
        ),

        ui.hr(),

        ui.h4("📊 Methodology Used in This Application"),
        ui.div(
            ui.h5("Base Effects Calculation"),
            ui.tags.p(
                ui.tags.strong("Annualized Month-over-Month Momentum:"),
                " MoM change × 12"
            ),
            ui.tags.p("This shows what annual inflation would be if current monthly price changes continued for a full year."),

            ui.tags.p(
                ui.tags.strong("Base Effect Contribution:"),
                " YoY inflation − Annualized MoM"
            ),
            ui.tags.p(
                "This reveals how much of the year-over-year inflation rate is due to unusual price movements "
                "from 12 months ago rather than current price momentum."
            ),

            ui.h5("Interpretation", style="margin-top: 20px;"),
            ui.tags.ul(
                ui.tags.li(ui.tags.strong("Positive base effect:"), " YoY inflation is higher than current momentum suggests (prices 12 months ago were unusually low)"),
                ui.tags.li(ui.tags.strong("Negative base effect:"), " YoY inflation is lower than current momentum suggests (prices 12 months ago were unusually high)"),
                ui.tags.li(ui.tags.strong("Near-zero base effect:"), " YoY inflation accurately reflects current price trends"),
            ),
            class_="metric-card"
        ),

        ui.hr(),

        ui.h4("🎯 Momentum Period Options"),
        ui.div(
            ui.tags.p("To reduce noise from month-to-month volatility, this application offers three momentum smoothing options:"),
            ui.tags.ul(
                ui.tags.li(ui.tags.strong("Monthly:"), " Uses the most recent month's MoM change (noisy but timely)"),
                ui.tags.li(ui.tags.strong("Quarterly:"), " Uses 3-month average MoM change (recommended default)"),
                ui.tags.li(ui.tags.strong("Half-year:"), " Uses 6-month average MoM change (smoothest, lags trends)"),
            ),
            ui.tags.p(
                "The quarterly option (3-month average) provides the best balance between smoothing volatility "
                "and reflecting current trends, consistent with Bank of Canada analytical practices.",
                style="font-style: italic; color: #6c757d; margin-top: 10px;"
            ),
            class_="metric-card"
        ),

        ui.hr(),

        ui.h4("📚 Additional Resources"),
        ui.div(
            ui.tags.ul(
                ui.tags.li(
                    ui.tags.a(
                        "Statistics Canada - Consumer Price Index Portal",
                        href="https://www.statcan.gc.ca/en/subjects-start/prices_and_price_indexes/consumer_price_indexes",
                        target="_blank"
                    )
                ),
                ui.tags.li(
                    ui.tags.a(
                        "Bank of Canada - CPI Common Component",
                        href="https://www.bankofcanada.ca/rates/price-indexes/cpi/",
                        target="_blank"
                    )
                ),
                ui.tags.li(
                    ui.tags.a(
                        "European Central Bank - Base Effects Explained",
                        href="https://www.ecb.europa.eu/stats/macroeconomic_and_sectoral/hicp/html/index.en.html",
                        target="_blank"
                    )
                ),
            ),
            class_="metric-card"
        ),
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
            ui.output_ui("wide_format_table"),
        )
    )


# Main UI definition
app_ui = ui.page_navbar(
    create_recent_trends_tab(),
    create_historical_tab(),
    create_detailed_heatmap_tab(),
    create_data_table_tab(),
    create_research_tab(),
    title="Statistics Canada Inflation Analysis",
    id="main_navbar",
    fillable=True,
    header=ui.div(
        # Add Canadian maple leaf favicon as inline SVG data URI
        # This avoids file serving issues on shinyapps.io
        # SVG source: SVG Repo (www.svgrepo.com) - Noto emoji maple leaf
        ui.tags.script("""
            (function() {
                var link = document.createElement('link');
                link.rel = 'icon';
                link.type = 'image/svg+xml';
                link.href = 'data:image/svg+xml,' + encodeURIComponent('<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg"><path d="M59.17 122.18c.2.99 1.31 1.87 4.39 2.07c3.08.2 5.15-.3 5.23-1.95c.09-1.65-1.14-3.49-1.34-4.88c-.2-1.39-.99-10.74-1.19-15.61c-.2-4.87-.36-14.16-.36-14.16l-4.07.43s.06 9.65-.14 14.52c-.2 4.87-1.01 12.01-1.11 13.89c-.09 1.71-1.83 3.61-1.41 5.69z" fill="#df1324"/><defs><radialGradient id="g" cx="65.418" cy="73.028" r="42.057" gradientTransform="matrix(.9999 .0135 -.0173 1.2815 1.27 -21.44)" gradientUnits="userSpaceOnUse"><stop offset=".596" stop-color="#ff5617"/><stop offset="1" stop-color="#df1024"/></radialGradient></defs><path d="M63.88 89.48s-5.57 6.36-9.55 8.75c-3.98 2.39-9.55 5.27-10.54 4.57c-.99-.7 1.39-5.57 1.39-5.57s-8.32 1.88-17.53-.79c-8.82-2.55-14.09-6.37-13.69-7.47s4.57-1.69 8.65-3.28c4.08-1.59 9.55-4.18 9.55-4.18s-7.83-2.84-12.3-5.62s-7.29-5.41-7.39-6.31c-.1-.89 6.26-2.49 6.26-2.49s-3.48-2.39-6.07-10.14s-3.27-13.63-2.78-14.21c1.18-1.37 11.73 2.28 14.72 3.85c2.88 1.51 7.55 4.5 7.55 4.5s-.3-5.97.7-5.97c.99 0 3.58 2.39 5.87 5.37s9.05 13.32 10.74 12.53c1.69-.8.09-5.78-2.28-10.67c-1.49-3.08-3.59-8.23-4.78-14.29c-1.18-6-.5-10.94.2-11.53c.7-.6 7.46 4.67 7.46 4.67s-.54-5.79.55-10.76s2.03-6.46 2.62-6.56c.6-.1 2.99 3.4 2.99 3.4s.92-4.95 2.91-8.43s3.75-5.09 4.64-5.09c.89 0 3.52 3.49 4.71 7.17c1.19 3.68 1.88 6.73 1.88 6.73s1.51-3.09 2.18-3.2c.57-.09 2.58 2.16 3.57 7.43s.99 8.91.99 8.91s4.28-4.47 5.07-4.57c.8-.1 2.79 5.07 1.3 12.13c-1.49 7.06-5.37 13.88-6.27 17.56c-.89 3.68-1.69 7.29-.2 7.69s3-4.1 6.18-9.08s7.54-10.21 8.14-9.82c.6.4 1.49 2.29 1.69 3.28c.2.99.3 2.88.3 2.88s4.57-3.08 8.55-4.57c3.98-1.49 12.93-4.77 14.82-3.18c1.89 1.59-1.49 10.14-3.48 14.52c-1.99 4.38-6.36 10.93-6.36 10.93s5.95 1.14 5.85 2.03c-.1.89-4.95 4.89-9.33 7.18s-9.96 4.13-9.96 4.13s2.49 1.69 8.35 3.58c5.87 1.89 10.74 2.49 11.14 3.48s-2.29 4.47-11.24 6.86c-8.95 2.39-18.93 1.06-19.43 1.55c-.5.5 2.43 4.41 1.63 5.51s-6.17-.42-10.34-3.98c-5.35-4.56-9.63-9.43-9.63-9.43z" fill="url(#g)"/><path d="M63.97 91.94s1.82-1.4 5.59-2.16c2.07-.42 4.88-.47 7.95-.4c8.24.17 17.03 1.71 21.65 1.87c4.62.15 8.86 0 8.78-1s-7.16-.54-12.55-1.54s-13.17-2.08-16.41-2.23c-8.37-.41-10.09.77-10.09.77s10.78-9.55 14.79-12.63s10.47-8.12 16.41-13.4c5.17-4.6 14.63-14.33 14.02-15.17c-.62-.85-12.25 10.24-16.48 13.63c-4.24 3.39-9.85 7.6-18.55 14.46c-8.7 6.86-13.34 11.35-13.34 11.35s-.69-25.8-.92-31.89c-.23-6.08-.23-28.87-.39-31.64s.39-14.26-1-14.19c-1.39.08-1.62 9.4-1.77 14.1c-.15 4.7-.15 24.49-.31 30.58s.23 32.73.23 32.73s-16.56-12.46-22.72-17.39S22.39 53.61 21 52.45c-1.39-1.16-6.71-6.11-7.33-5.49c-.62.62 7.17 8.88 10.1 11.5s16.15 14.09 21.85 18.78s12.88 9.92 12.88 9.92s-6.78-.77-15.92.05c-6.93.62-13.43 1.42-16.28 1.65s-7.24.31-7.39.92c-.15.62 3.54 1.54 10.94 1.08c7.39-.46 11.26-.79 16.64-1.05c7.32-.35 12.02-.1 13.86.36c1.85.46 3.62 1.77 3.62 1.77z" fill="#ff8e00"/></svg>');
                document.head.appendChild(link);
            })();
        """),
        # Load Plotly library globally for all charts (version must match what Plotly Python generates)
        ui.tags.script(src="https://cdn.plot.ly/plotly-3.2.0.min.js", integrity="sha256-iZ2u/oU2wf/vDbl/ChcX93WgbBRSBvUO6N413hDz7xM=", crossorigin="anonymous"),
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

            /* Mobile Responsiveness */
            @media (max-width: 768px) {
                /* Auto-collapse sidebar on mobile for better UX */
                .bslib-sidebar-layout > .sidebar {
                    --_sidebar-width: 0px;
                }

                /* Ensure metric cards stack nicely */
                .metric-card {
                    margin-bottom: 10px;
                }

                /* Reduce padding on mobile */
                .page-header {
                    padding: 15px 10px;
                }
            }

            @media (min-width: 480px) and (max-width: 768px) {
                /* 2-column grid for metric cards on larger phones/small tablets */
                .metric-card {
                    width: calc(50% - 10px);
                    display: inline-block;
                    vertical-align: top;
                    margin-right: 10px;
                }
            }

            /* Heatmap mobile responsiveness */
            .heatmap-container {
                width: 100%;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
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
