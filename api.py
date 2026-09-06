from fastapi import FastAPI
import sqlite3
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PriceUpdate(BaseModel):
    category: str
    new_price: float

@app.get("/api/prices")
def get_live_prices():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute("SELECT product_category_name, unit_price FROM historical_pricing_logs")
    rows = cursor.fetchall()
    conn.close()
    prices = {row[0]: row[1] for row in rows}
    return {"status": "success", "data": prices}

# NEW: Endpoint to receive price updates from your Streamlit dashboard
@app.post("/api/update-price")
def update_price(data: PriceUpdate):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE historical_pricing_logs SET unit_price = ? WHERE product_category_name = ?",
        (data.new_price, data.category)
    )
    conn.commit()
    conn.close()
    return {"status": "success", "updated_category": data.category, "new_price": data.new_price}