import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import requests

# Page Configuration
st.set_page_config(
    page_title="SmartShop | AI Dynamic Pricing Admin",
    page_icon="⚡",
    layout="wide"
)

# Live Render Backend API URL
RENDER_API_URL = "https://ecommerce-dynamic-pricing.onrender.com/api/update-price"

st.title("⚡ SmartShop: AI Dynamic Pricing Admin Dashboard")
st.markdown("Manage real-time market elasticity, simulate demand spikes, and push live price optimizations to the customer storefront.")

# Load current product prices from local database for admin viewing
def load_current_prices():
    try:
        conn = sqlite3.connect('ecommerce.db')
        df = pd.read_sql("SELECT product_category_name, unit_price FROM historical_pricing_logs", conn)
        conn.close()
        return df
    except Exception as e:
        # Fallback dummy data if db is missing locally during testing
        return pd.DataFrame({
            "product_category_name": ["computers_accessories", "health_beauty", "watches_gifts", "perfumery", "garden_tools", "furniture_decor"],
            "unit_price": [113.19, 137.81, 145.55, 116.91, 98.32, 69.65]
        })

df_prices = load_current_prices()

# Sidebar Control Panel
st.sidebar.header("🎛️ AI Pricing Simulation")
selected_category = st.sidebar.selectbox(
    "Select Product Category", 
    df_prices["product_category_name"].tolist()
)

# Find current price of selected item
current_row = df_prices[df_prices["product_category_name"] == selected_category]
base_price = float(current_row["unit_price"].values[0]) if not current_row.empty else 100.00

st.sidebar.markdown("---")
st.sidebar.subheader("Market Variables")
demand_factor = st.sidebar.slider("Demand Multiplier (Traffic / Views)", 0.5, 2.0, 1.2, 0.1)
competitor_price = st.sidebar.number_input("Competitor Benchmark Price ($)", value=float(base_price * 0.95))
stock_level = st.sidebar.slider("Current Inventory Stock", 1, 500, 45)

# AI Dynamic Pricing Calculation Logic
# Formula: Base Price * Demand Factor adjusted by stock scarcity penalty/reward
scarcity_multiplier = 1.1 if stock_level < 20 else (0.95 if stock_level > 200 else 1.0)
calculated_price = round(base_price * demand_factor * scarcity_multiplier, 2)

# Main Dashboard Layout
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Current Base Price", value=f"${base_price:.2f}")

with col2:
    price_delta = round(calculated_price - base_price, 2)
    st.metric(
        label="AI Optimized Price", 
        value=f"${calculated_price:.2f}", 
        delta=f"{price_delta:+.2f} ({((price_delta/base_price)*100):+.1f}%)"
    )

with col3:
    st.metric(label="Inventory Stock Status", value=f"{stock_level} units", delta="Optimal" if stock_level > 20 else "Low Stock Alert")

st.markdown("---")

# ==========================================
# AI PRICE VS. TOTAL REVENUE OPTIMIZATION CURVE
# ==========================================
st.subheader("📈 AI Price vs. Total Revenue Optimization Curve")
st.markdown(f"This curve illustrates how market demand elasticity shapes total revenue across various price points for **{selected_category}**.")

# Simulate a range of potential prices around the base price (50% to 150%)
price_range = np.linspace(base_price * 0.5, base_price * 1.5, 50)
baseline_demand = 100
elasticity = 1.5

# Calculate projected demand and total revenue
simulated_demand = baseline_demand * (price_range / base_price) ** (-elasticity)
total_revenue = price_range * simulated_demand

# Create DataFrame for charting
df_revenue_curve = pd.DataFrame({
    'Optimized Price ($)': price_range,
    'Projected Total Revenue ($)': total_revenue
}).set_index('Optimized Price ($)')

# Render the interactive line chart
st.line_chart(df_revenue_curve)

optimal_price = price_range[total_revenue.argmax()]
st.success(f"💡 Revenue Maximization Insight: The optimal price point to achieve peak revenue for this category is **${optimal_price:.2f}**.")

st.markdown("---")

# Analytics & Preview Section
st.subheader("📊 Live Catalog Inventory & Pricing Overview")
st.dataframe(df_prices, use_container_width=True)

st.markdown("---")

# Action Section: Push to Cloud Backend
st.subheader("🚀 Deploy Price Update to Live Storefront")
st.info(f"Target Category: **{selected_category}** | New AI Price: **${calculated_price:.2f}**")

if st.button("Approve and Push Price to Global Storefront", type="primary"):
    payload = {
        "category": selected_category,
        "new_price": float(calculated_price)
    }
    
    with st.spinner("Syncing with cloud backend and SQLite database..."):
        try:
            # 1. Update local SQLite database so admin view updates instantly
            conn = sqlite3.connect('ecommerce.db')
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE historical_pricing_logs SET unit_price = ? WHERE product_category_name = ?",
                (calculated_price, selected_category)
            )
            conn.commit()
            conn.close()
            
            # 2. Send POST request to live Render backend to sync Netlify storefront
            response = requests.post(RENDER_API_URL, json=payload, timeout=10)
            
            if response.status_code == 200:
                st.success(f"Successfully deployed! ${calculated_price:.2f} is now live on your Netlify storefront.")
                st.balloons()
            else:
                st.error(f"Database updated locally, but cloud sync returned status code: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to live Render backend. Make sure your Render service is awake.")
        except Exception as e:
            st.error(f"An error occurred: {e}")