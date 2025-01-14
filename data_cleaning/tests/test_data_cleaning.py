import pytest
import pandas as pd
import sqlite3
from ..DataCleaningSetUp import (
    clean_data,
    calculate_category_mean,
    calculate_category_revenue,
    calculate_category_day,
    process_outliers,
    create_database
)

# Fixtures for sample data and temporary paths
@pytest.fixture
def sample_data():
    """Sample data to test the functions."""
    return pd.DataFrame({
        'date': ['2024-07-01', '2024-07-01', '2024-07-01', '2024-07-02', '2024-07-02', '2024-07-02', '2024-07-03'],
        'category': ['Widget', 'Gadget', 'Widget', 'Doodad', 'Widget', 'Gadget', 'Widget'],
        'product': ['Widget-A', 'Gadget-X', 'Widget-B', 'Doodad-1', 'Widget-C', 'Gadget-Y', 'Widget-D'],
        'quantity': [10, 5, None, 4, 3, None, None],  # Add None for some quantities
        'price': [9.99, 19.99, 'not_a_number', 4.99, None, None, 5.0]  # Add 'not_a_number' and None for some prices
    })

@pytest.fixture
def temp_db_path(tmp_path):
    """Provide a temporary database path."""
    return tmp_path / "test_database.db"

# Tests for clean_data
def test_clean_data(sample_data):
    df = clean_data(sample_data)

    # Test price conversion and NaN handling
    assert pd.api.types.is_float_dtype(df['price'])  # Ensure 'price' is converted to float
    assert df['price'].isna().sum() == 0  # No NaN values should remain in 'price'

    # Test quantity NaN replacement
    assert df['quantity'].isna().sum() == 0  # No NaN values should remain in 'quantity'

    # Ensure no rows with both quantity and price as NaN
    assert df[['quantity', 'price']].isna().all(axis=1).sum() == 0  # No rows should have both NaN

    # Ensure that at least one missing value in 'price' is replaced (due to 'not_a_number' or None)
    assert (df['price'] == 0.0).sum() >= 1  # At least one 'price' should be replaced with 0

    # Ensure that at least one missing value in 'quantity' is replaced with 0
    print(df['quantity'].head(10))
    assert (df['quantity'] == 0.0).sum() >= 1  # At least one 'quantity' should be replaced with 0

    # Ensure at least one row with both 'quantity' and 'price' missing has been removed
    assert df[['quantity', 'price']].isna().all(axis=1).sum() == 0  # No rows should have both 'quantity' and 'price' missing

    # Optional: You could also assert specific conditions for other values, e.g., ensuring the total sales was calculated.
    assert df['total_sales'].isna().sum() == 0  # Ensure total_sales is not NaN for any row

    # Test date conversion and day_of_week column
    assert pd.api.types.is_datetime64_any_dtype(df['date'])
    assert 'day_of_week' in df.columns
    assert all(df['day_of_week'].notna())

    # Test high_volume flag
    assert all(df['high_volume'].isin([True, False]))

# Tests for calculate_category_mean
def test_calculate_category_mean(sample_data):
    df = clean_data(sample_data)
    category_mean = calculate_category_mean(df)

    # Test index and values
    assert isinstance(category_mean, pd.Series)
    assert category_mean.index.names == ['category', 'product']
    assert all(category_mean.notna())

# Tests for calculate_category_revenue
def test_calculate_category_revenue(sample_data):
    df = clean_data(sample_data)
    category_revenue = calculate_category_revenue(df)

    # Test index and values
    assert isinstance(category_revenue, pd.Series)
    assert category_revenue.index.names == ['category']
    assert all(category_revenue.notna())
    assert all(category_revenue >= 0)

# Tests for calculate_category_day
def test_calculate_category_day(sample_data):
    df = clean_data(sample_data)
    category_day = calculate_category_day(df)

    # Test structure and values
    assert isinstance(category_day, pd.DataFrame)
    assert 'category' in category_day.columns
    assert 'date' in category_day.columns
    assert 'total_sales' in category_day.columns

    # Test that each category has only one max day
    assert category_day['category'].is_unique

# Tests for process_outliers
def test_process_outliers(sample_data):
    df = clean_data(sample_data)
    df_cleaned, df_outliers = process_outliers(df)

    # Test that outliers were separated
    assert isinstance(df_cleaned, pd.DataFrame)
    assert isinstance(df_outliers, pd.DataFrame)

    # Check that outliers don't exist in the cleaned data
    assert not df_cleaned['quantity'].isin(df_outliers['quantity']).any()

    # Check that all outliers match the outlier condition
    stats = df.groupby("category")['quantity'].agg(['mean', 'std']).reset_index()
    stats = stats.set_index("category")  # Ensures the category column is set as index
    outlier_condition = (
        (df_outliers['quantity'] < stats.loc[df_outliers['category'], 'mean'] - 2 * stats.loc[df_outliers['category'], 'std']) |
        (df_outliers['quantity'] > stats.loc[df_outliers['category'], 'mean'] + 2 * stats.loc[df_outliers['category'], 'std'])
    )
    assert all(outlier_condition)

# Tests for create_database
def test_create_database(sample_data, temp_db_path):
    df = clean_data(sample_data)
    df_cleaned, df_outliers = process_outliers(df)
    df_category_mean = calculate_category_mean(df)
    df_category_revenue = calculate_category_revenue(df)
    df_category_day = calculate_category_day(df)

    create_database(
        df_cleaned,
        df_outliers,
        df_category_day,
        df_category_mean,
        df_category_revenue,
        str(temp_db_path)
    )

    # Check that tables were created in the database
    with sqlite3.connect(str(temp_db_path)) as conn:
        cursor = conn.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [table[0] for table in tables]

        assert 'sales' in table_names
        assert 'outliers' in table_names
        assert 'category_day' in table_names
        assert 'category_mean' in table_names
        assert 'category_revenue' in table_names