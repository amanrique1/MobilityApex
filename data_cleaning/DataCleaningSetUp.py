import sqlite3
import pandas as pd

def clean_data(df):
    # Basic Cleaning
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df = df.dropna(subset=['quantity', 'price'], how='all')
    df['quantity'] = df['quantity'].fillna(0)

    medians = df.groupby("category")['price'].median()
    df['price'] = df['price'].fillna(medians).fillna(0)

    df['total_sales'] = df['quantity'] * df['price']
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.day_name()
    df['high_volume'] = df['quantity'] > 10

    return df

def calculate_category_mean(df):
    """Calculate mean price for each category-product combination."""
    return df.groupby(["category", "product"])['price'].mean()

def calculate_category_revenue(df):
    """Calculate total revenue for each category."""
    return df.groupby("category")['total_sales'].sum()

def calculate_category_day(df):
    """Identify the day with the highest sales for each category."""
    category_day = df.groupby(['category', 'date'])['total_sales'].sum().reset_index()
    idx = category_day.groupby('category')['total_sales'].transform('max') == category_day['total_sales']
    return category_day[idx]

def process_outliers(df):
    """Detect transactions where quantity is more than 2 standard deviations from the category mean."""
    stats = df.groupby("category")['quantity'].agg(['mean', 'std']).reset_index()
    df = df.merge(stats, on="category")
    df['outlier'] = ((df['quantity'] < df['mean'] - 2 * df['std']) |
                     (df['quantity'] > df['mean'] + 2 * df['std']))
    df_outliers = df[df['outlier']].drop(columns=['mean', 'std', 'outlier'])
    df_cleaned = df[~df['outlier']].drop(columns=['mean', 'std', 'outlier'])
    return df_cleaned, df_outliers

def create_database(df, df_outliers, df_category_day, df_category_mean, df_category_revenue, db_file):
    conn = sqlite3.connect(db_file)
    try:
        df.to_sql('sales', conn, if_exists='replace', index=False)
        df_outliers.to_sql('outliers', conn, if_exists='replace', index=False)
        df_category_day.to_sql('category_day', conn, if_exists='replace', index=False)
        df_category_mean.to_sql('category_mean', conn, if_exists='replace')
        df_category_revenue.to_sql('category_revenue', conn, if_exists='replace')
    finally:
        conn.close()

def main():
    # Read data from CSV (you can replace 'data.csv' with the actual file path)
    df = pd.read_csv('data.csv')

    # Clean and process data
    df = clean_data(df)
    df_category_mean = calculate_category_mean(df)
    df_category_revenue = calculate_category_revenue(df)
    df_category_day = calculate_category_day(df)
    df_cleaned, df_outliers = process_outliers(df)

    # Set database file path (you can replace it with a custom path)
    db_file = 'data.db'

    # Create SQLite database and save tables
    create_database(df_cleaned, df_outliers, df_category_day, df_category_mean, df_category_revenue, db_file)
    print("Data processing complete and database created successfully.")

if __name__ == "__main__":
    main()