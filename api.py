from fastapi import FastAPI
import sqlite3
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS so your HTML webpage can talk to your Python backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/prices")
def get_live_prices():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute("SELECT product_category_name, unit_price FROM historical_pricing_logs")
    rows = cursor.fetchall()
    conn.close()
    
    # Format data as a dictionary for the frontend
    prices = {row[0]: row[1] for row in rows}
    return {"status": "success", "data": prices}