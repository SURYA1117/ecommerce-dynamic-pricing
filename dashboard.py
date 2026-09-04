import streamlit as st
import pandas as pd
import sqlite3
import pickle
import numpy as np

# Page Configuration
st.set_page_config(page_title="E-Commerce Dynamic Pricing Engine", layout="wide")

st.title("🛍️ E-Commerce Dynamic Pricing & Revenue Optimization")
st.markdown("Simulate price changes, analyze demand elasticity, and update live prices instantly.")

# 1. Load the Trained Machine Learning Model (from root directory)
@st.cache_resource
def load_model():
    with open('rf_pricing_model.pkl', 'rb') as file:
        model = pickle.load(file)
    return model

model = load_model()

# 2. Connect to SQLite Database and Load Data
@st.cache_data(ttl=60)
def load_data():
    conn = sqlite3.connect('ecommerce.db')
    df = pd.read_sql("SELECT * FROM historical_pricing_logs", conn)
    conn.close()
    return df

df = load_data()

# 3. Sidebar Selection for Product Category
st.sidebar.header("Configuration")
categories = df['product_category_name'].unique() if 'product_category_name' in df.columns else []
selected_item = st.sidebar.selectbox("Select Product Category", categories)

if selected_item:
    # Filter data for selected item
    item_data = df[df['product_category_name'] == selected_item].iloc[0]
    current_price = item_data['unit_price']
    
    st.subheader(f"Analysis for: {selected_item}")
    st.metric(label="Current Live Price", value=f"${current_price:.2f}")

    # 4. Simulation Logic (What-if scenario testing)
    st.divider()
    st.subheader("Price Elasticity & Revenue Simulation")
    
    # Define a range of test prices around the current price
    price_range = np.linspace(current_price * 0.7, current_price * 1.3, 20)
    simulation_results = []

    for test_price in price_range:
        # Prepare input features for the model
        input_features = np.array([[test_price, item_data.get('comp_1', test_price), item_data.get('freight_price', 10)]])
        
        # Predict expected quantity sold
        predicted_qty = model.predict(input_features)[0]
        predicted_revenue = test_price * max(predicted_qty, 0)
        
        simulation_results.append({
            'Simulated Price': test_price,
            'Predicted Revenue': predicted_revenue,
            'Predicted Quantity': predicted_qty
        })

    sim_df = pd.DataFrame(simulation_results)
    
    # Find optimal price (max revenue)
    best_scenario = sim_df.loc[sim_df['Predicted Revenue'].idxmax()]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Recommended Optimal Price", value=f"${best_scenario['Simulated Price']:.2f}")
    with col2:
        st.metric(label="Projected Peak Revenue", value=f"${best_scenario['Predicted Revenue']:.2f}")

    # 5. Visualizing the Revenue Curve
    st.line_chart(sim_df.set_index('Simulated Price')['Predicted Revenue'])

    # 6. ACTION EXECUTION: Write-back to the database
    st.divider()
    st.subheader("Execution")

    optimal_price = best_scenario['Simulated Price']

    if st.button(f"Approve and Update Price to ${optimal_price:.2f}", key="update_price_button"):
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
        
        # Forces the app to instantly refresh from the top
        st.rerun()