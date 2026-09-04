import pandas as pd
import sqlite3

def run_etl():
    print("Starting ETL Pipeline...")

    # 1. EXTRACT: Read the raw CSV file
    print("Extracting raw data...")
    df = pd.read_csv('retail_price.csv')

    # 2. TRANSFORM: Clean missing values and engineer initial columns
    print("Cleaning and transforming data...")
    
    # If a competitor's price is missing (NaN), we fill it with our own unit_price 
    # as a neutral baseline so the machine learning model doesn't crash.
    df['comp_1'] = df['comp_1'].fillna(df['unit_price'])
    df['comp_2'] = df['comp_2'].fillna(df['unit_price'])
    df['comp_3'] = df['comp_3'].fillna(df['unit_price'])

    # Create a baseline average market price for easier modeling later
    df['market_avg_price'] = df[['comp_1', 'comp_2', 'comp_3']].mean(axis=1)

    # 3. LOAD: Save the cleaned DataFrame to a relational database
    print("Loading data into SQLite...")
    
    # This creates a file named 'ecommerce.db' in your folder if it doesn't exist
    conn = sqlite3.connect('ecommerce.db') 
    
    # Write the data into a SQL table named 'historical_pricing_logs'
    df.to_sql('historical_pricing_logs', conn, if_exists='replace', index=False)
    
    # Close the database connection
    conn.close()
    print("Success! Data loaded into ecommerce.db")

if __name__ == "__main__":
    run_etl()