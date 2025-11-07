"""
Excel Export Functionality

Functions to create formatted Excel workbooks with inflation analysis results.
"""

import pandas as pd
import io
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def create_excel_report(
    df: pd.DataFrame,
    categories: Optional[list] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> io.BytesIO:
    """
    Create a comprehensive Excel report with multiple sheets.

    Args:
        df: CPI DataFrame with inflation metrics
        categories: Optional list of categories to include (None = all)
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)

    Returns:
        BytesIO object containing the Excel file
    """
    logger.info("Creating Excel report...")

    # Filter data
    export_df = df.copy()

    if categories:
        export_df = export_df[export_df['category'].isin(categories)]

    if start_date:
        export_df = export_df[export_df['date'] >= pd.to_datetime(start_date)]

    if end_date:
        export_df = export_df[export_df['date'] <= pd.to_datetime(end_date)]

    # Create BytesIO object
    output = io.BytesIO()

    # Create Excel writer
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'left'
        })

        date_format = workbook.add_format({
            'num_format': 'mmm yyyy',
            'align': 'left'
        })

        number_format = workbook.add_format({
            'num_format': '0.0',
            'align': 'right'
        })

        percent_format = workbook.add_format({
            'num_format': '0.00%',
            'align': 'right'
        })

        # Sheet 1: Summary
        _create_summary_sheet(writer, export_df, header_format, title_format)

        # Sheet 2: Recent Data (last 24 months)
        _create_recent_data_sheet(writer, export_df, header_format, date_format, number_format, percent_format)

        # Sheet 3: All Data
        _create_full_data_sheet(writer, export_df, header_format, date_format, number_format, percent_format)

        # Sheet 4: Category Breakdown (most recent)
        _create_category_breakdown_sheet(writer, export_df, header_format, percent_format)

        # Sheet 5: Data Dictionary
        _create_data_dictionary_sheet(writer, header_format)

    output.seek(0)
    logger.info("Excel report created successfully")
    return output


def _create_summary_sheet(writer, df, header_format, title_format):
    """Create summary statistics sheet."""
    from ..models.inflation import get_latest_inflation_rate, get_inflation_summary_stats

    # Get key categories
    key_categories = ["All-items", "Food", "Shelter", "Transportation", "Gasoline"]

    summary_data = []
    for category in key_categories:
        if category in df['category'].values:
            latest = get_latest_inflation_rate(df, category)
            summary_data.append({
                'Category': category,
                'Latest Date': latest['date'].strftime('%B %Y'),
                'Current CPI': latest['cpi_value'],
                'MoM Change (%)': latest.get('mom_change'),
                'YoY Change (%)': latest.get('yoy_change'),
            })

    summary_df = pd.DataFrame(summary_data)

    # Write to sheet
    summary_df.to_excel(writer, sheet_name='Summary', index=False, startrow=2)

    worksheet = writer.sheets['Summary']

    # Add title
    worksheet.write('A1', 'Canadian Inflation Summary', title_format)

    # Format header row
    for col_num, value in enumerate(summary_df.columns.values):
        worksheet.write(2, col_num, value, header_format)

    # Set column widths
    worksheet.set_column('A:A', 25)
    worksheet.set_column('B:B', 15)
    worksheet.set_column('C:E', 15)


def _create_recent_data_sheet(writer, df, header_format, date_format, number_format, percent_format):
    """Create recent data sheet (last 24 months)."""
    # Get last 24 months
    max_date = df['date'].max()
    cutoff_date = max_date - pd.DateOffset(months=24)
    recent_df = df[df['date'] >= cutoff_date].copy()

    # Select columns
    columns = ['date', 'category', 'value', 'mom_change', 'yoy_change']
    recent_df = recent_df[columns].copy()

    # Rename columns for clarity
    recent_df.columns = ['Date', 'Category', 'CPI Value', 'MoM Change (%)', 'YoY Change (%)']

    # Sort by date (descending) and category
    recent_df = recent_df.sort_values(['Date', 'Category'], ascending=[False, True])

    # Write to sheet
    recent_df.to_excel(writer, sheet_name='Recent Trends (24M)', index=False, startrow=0)

    worksheet = writer.sheets['Recent Trends (24M)']

    # Format header row
    for col_num, value in enumerate(recent_df.columns.values):
        worksheet.write(0, col_num, value, header_format)

    # Set column widths and formats
    worksheet.set_column('A:A', 12)
    worksheet.set_column('B:B', 30)
    worksheet.set_column('C:C', 12, number_format)
    worksheet.set_column('D:E', 15, percent_format)


def _create_full_data_sheet(writer, df, header_format, date_format, number_format, percent_format):
    """Create full historical data sheet."""
    # Select columns
    columns = ['date', 'category', 'value', 'mom_change', 'yoy_change']
    full_df = df[columns].copy()

    # Rename columns for clarity
    full_df.columns = ['Date', 'Category', 'CPI Value', 'MoM Change (%)', 'YoY Change (%)']

    # Sort by category and date
    full_df = full_df.sort_values(['Category', 'Date'])

    # Write to sheet
    full_df.to_excel(writer, sheet_name='Historical Data', index=False, startrow=0)

    worksheet = writer.sheets['Historical Data']

    # Format header row
    for col_num, value in enumerate(full_df.columns.values):
        worksheet.write(0, col_num, value, header_format)

    # Set column widths and formats
    worksheet.set_column('A:A', 12)
    worksheet.set_column('B:B', 30)
    worksheet.set_column('C:C', 12, number_format)
    worksheet.set_column('D:E', 15, percent_format)


def _create_category_breakdown_sheet(writer, df, header_format, percent_format):
    """Create category breakdown sheet for most recent date."""
    from ..models.analysis import get_category_breakdown

    breakdown = get_category_breakdown(df)

    # Select and rename columns
    breakdown_export = breakdown[['category', 'value', 'yoy_change']].copy()
    breakdown_export.columns = ['Category', 'Current CPI', 'YoY Inflation (%)']

    # Write to sheet
    breakdown_export.to_excel(writer, sheet_name='Category Breakdown', index=False, startrow=2)

    worksheet = writer.sheets['Category Breakdown']

    # Add title with date
    latest_date = df['date'].max().strftime('%B %Y')
    worksheet.write('A1', f'Category Inflation Breakdown - {latest_date}', header_format)

    # Format header row
    for col_num, value in enumerate(breakdown_export.columns.values):
        worksheet.write(2, col_num, value, header_format)

    # Set column widths
    worksheet.set_column('A:A', 35)
    worksheet.set_column('B:B', 15)
    worksheet.set_column('C:C', 18, percent_format)

    # Add conditional formatting for inflation column
    worksheet.conditional_format(3, 2, 2 + len(breakdown_export), 2, {
        'type': '3_color_scale',
        'min_color': '#63BE7B',  # Green for low
        'mid_color': '#FFEB84',  # Yellow for medium
        'max_color': '#F8696B',  # Red for high
    })


def _create_data_dictionary_sheet(writer, header_format):
    """Create data dictionary explaining the metrics."""
    dictionary_data = [
        ['Metric', 'Description'],
        ['CPI Value', 'Consumer Price Index value (base year 2002=100)'],
        ['MoM Change (%)', 'Month-over-Month percentage change in CPI'],
        ['YoY Change (%)', 'Year-over-Year percentage change in CPI (12 months)'],
        ['Category', 'CPI product category as defined by Statistics Canada'],
        ['Date', 'Month and year of the measurement'],
    ]

    dictionary_df = pd.DataFrame(dictionary_data[1:], columns=dictionary_data[0])

    # Write to sheet
    dictionary_df.to_excel(writer, sheet_name='Data Dictionary', index=False, startrow=2)

    worksheet = writer.sheets['Data Dictionary']

    # Add title
    worksheet.write('A1', 'Data Dictionary', header_format)

    # Format header row
    for col_num, value in enumerate(dictionary_df.columns.values):
        worksheet.write(2, col_num, value, header_format)

    # Set column widths
    worksheet.set_column('A:A', 20)
    worksheet.set_column('B:B', 60)

    # Add metadata
    worksheet.write('A10', 'Data Source:', header_format)
    worksheet.write('B10', 'Statistics Canada Table 18-10-0004-01')

    worksheet.write('A11', 'Export Date:', header_format)
    worksheet.write('B11', datetime.now().strftime('%Y-%m-%d %H:%M'))


def create_simple_csv_export(
    df: pd.DataFrame,
    categories: Optional[list] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> str:
    """
    Create a simple CSV export of filtered data.

    Args:
        df: CPI DataFrame with inflation metrics
        categories: Optional list of categories to include
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)

    Returns:
        CSV string
    """
    # Filter data
    export_df = df.copy()

    if categories:
        export_df = export_df[export_df['category'].isin(categories)]

    if start_date:
        export_df = export_df[export_df['date'] >= pd.to_datetime(start_date)]

    if end_date:
        export_df = export_df[export_df['date'] <= pd.to_datetime(end_date)]

    # Select columns
    columns = ['date', 'category', 'value', 'mom_change', 'yoy_change']
    export_df = export_df[columns]

    # Convert to CSV
    return export_df.to_csv(index=False)
