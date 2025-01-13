import sqlite3
import pandas as pd

# Read the data from the file
df = pd.read_csv('data.csv')

# # Basic Cleaning
# Convert 'Price' to numeric, setting errors='coerce' turns invalid values into NaN
df['price'] = pd.to_numeric(df['price'], errors='coerce')

# Drop columns with NaN in price and quantity
df = df.dropna(subset=['quantity', 'price'], how = 'all')

# Fill missing values in quantity with 0
df['quantity'] = df['quantity'].fillna(0)

# Calculate the median price for each category
medians = df.groupby("category")['price'].median()
# Fill missing values in 'price' with the median of the category
df['price'] = df['price'].fillna(medians)

# Get the total sales by multiplying quantity and price
df['total_sales'] = df['quantity'] * df['price']

# Get week day
df['date'] = pd.to_datetime(df['date'])
df['day_of_week'] = df['date'].dt.day_name()

# Set high volume flag
df['high_volume'] = df['quantity'] > 10


# # Transformations
# Get the category mean
df_category_mean = df.groupby("category")['price'].mean()

# Get the category revenue
df_category_revenue = df.groupby("category")['total_sales'].sum()

# Get the day with highest sales for each category
# Group by category and day_of_week, sum the total_sales (reset index used to keep the columns)
category_day = df.groupby(['category', 'day_of_week'])['total_sales'].sum().reset_index()
# Get the index of the max value for each category
idx = category_day.groupby('category')['total_sales'].transform(max) == category_day['total_sales']
# Filter the dataframe with the idx
df_category_day = category_day[idx]

# Filter outliers (2+ standard deviations from category mean)
# Calculate the mean and standard deviation for each category
stats = df.groupby("category")['quantity'].agg(['mean', 'std']).reset_index()
# Merge stats back into the original DataFrame
df = df.merge(stats, on="category")
# Tag outliers
df['outlier'] = ((df['quantity'] < df['mean'] - 2 * df['std']) |
                    (df['quantity'] > df['mean'] + 2 * df['std']))
# Filter outliers and clean up the DataFrame
df_outliers = df[df['outlier']].drop(columns=['mean', 'std', 'outlier'])
df = df[~df['outlier']].drop(columns=['mean', 'std', 'outlier'])

# # Export data

# SQLite database file
db_file = "data.db"

# Connect to the database (creates the file if it doesn't exist)
conn = sqlite3.connect(db_file)

try:
    # Save dataframes as separate tables
    df.to_sql('sales', conn, if_exists='replace', index=False)
    df_outliers.to_sql('outliers', conn, if_exists='replace', index=False)
    df_category_day.to_sql('category_day', conn, if_exists='replace', index=False)
    df_category_mean.to_sql('category_mean', conn, if_exists='replace')
    df_category_revenue.to_sql('category_revenue', conn, if_exists='replace')
    print("DataFrames saved successfully!")
finally:
    # Close the connection
    conn.close()
