import pandas as pd
import sqlite3
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import pickle

def train_pricing_model():
    print("Connecting to database...")
    conn = sqlite3.connect('ecommerce.db')
    
    # 1. LOAD: Read the clean data back into pandas
    query = "SELECT * FROM historical_pricing_logs"
    df = pd.read_sql(query, conn)
    conn.close()

    # 2. FEATURE ENGINEERING: Create stronger mathematical signals
    print("Engineering features...")
    # Ratio of our price vs the market average (e.g., 1.0 = exact match, 1.2 = 20% more expensive)
    df['price_competitiveness'] = df['unit_price'] / df['market_avg_price']

    # Select the columns the model will learn from (Features)
    X = df[['unit_price', 'market_avg_price', 'price_competitiveness']]
    
    # Select the column the model is trying to predict (Target)
    y = df['qty']

    # 3. SPLIT DATA: 80% for training, 20% for testing
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. TRAIN MODEL: Let the algorithm learn the historical patterns
    print("Training Random Forest model...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 5. SAVE MODEL: Export the trained brain to a file
    print("Saving the model...")
    with open('rf_pricing_model.pkl', 'wb') as file:
        pickle.dump(model, file)
        
    print("Success! Model trained and saved as 'rf_pricing_model.pkl'")

if __name__ == "__main__":
    train_pricing_model()