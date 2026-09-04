import streamlit as st
import pandas as pd
import pickle
import sqlite3
import numpy as np

# 1. LOAD MODEL
@st.cache_resource
def load_model():
    # Update the path to include the 'models/' folder
    with open('models/rf_pricing_model.pkl', 'rb') as file:
        model = pickle.load(file)
    return model
model = load_model()

st.title("E-Commerce Dynamic Pricing Engine")
st.write("Select a specific inventory item to optimize its price.")

# 2. FETCH REAL ITEMS FROM DATABASE
conn = sqlite3.connect('ecommerce.db')
# Get a list of actual products from the Kaggle dataset
categories_df = pd.read_sql("SELECT DISTINCT product_category_name FROM historical_pricing_logs", conn)

# UI: Dropdown menu for the business user
selected_item = st.selectbox("Select Product Category:", categories_df['product_category_name'].tolist())

# Fetch the real baseline prices for the chosen item
query = f"""
    SELECT AVG(unit_price) as current_price, AVG(market_avg_price) as market_price 
    FROM historical_pricing_logs 
    WHERE product_category_name = '{selected_item}'
"""
item_data = pd.read_sql(query, conn)
conn.close()

# Extract the real database numbers
db_current_price = float(item_data['current_price'].iloc[0])
db_market_price = float(item_data['market_price'].iloc[0])

st.subheader(f"Pricing Optimization for: {selected_item.replace('_', ' ').title()}")

# 3. DISPLAY REAL DATA
col1, col2 = st.columns(2)
with col1:
    st.metric("Current Database Price", f"${db_current_price:.2f}")
with col2:
    st.metric("Competitor Market Average", f"${db_market_price:.2f}")

# 4. RUN SIMULATION ON THE SPECIFIC ITEM
min_price = db_current_price * 0.8
max_price = db_current_price * 1.2
simulated_prices = np.linspace(min_price, max_price, 20)

results = []
for test_price in simulated_prices:
    price_comp = test_price / db_market_price
    
    input_data = pd.DataFrame({
        'unit_price': [test_price],
        'market_avg_price': [db_market_price],
        'price_competitiveness': [price_comp]
    })
    
    predicted_qty = model.predict(input_data)[0]
    predicted_revenue = test_price * predicted_qty
    
    results.append({
        'Simulated Price': test_price,
        'Predicted Sales Volume': predicted_qty,
        'Predicted Revenue': predicted_revenue
    })

results_df = pd.DataFrame(results)
best_scenario = results_df.loc[results_df['Predicted Revenue'].idxmax()]

# 5. FINAL RECOMMENDATION
st.success(f"**Action Recommended:** Update price to ${best_scenario['Simulated Price']:.2f} to maximize revenue.")

st.write("### Revenue Curve")
st.line_chart(data=results_df.set_index('Simulated Price')['Predicted Revenue'])
    # 6. ACTION EXECUTION: Write-back to the database
st.divider()
st.subheader("Execution")

optimal_price = best_scenario['Simulated Price']

if st.button(f"Approve and Update Price to ${optimal_price:.2f}"):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    update_query = f"""
        UPDATE historical_pricing_logs 
        SET unit_price = {optimal_price} 
        WHERE product_category_name = '{selected_item}'
    """
    
    cursor.execute(update_query)
    conn.commit()
    conn.close()
    
    st.balloons()
    st.success("Success! The database has been updated.")
    
    # ADD THIS LINE: Forces the app to instantly refresh from the top
    st.rerun()