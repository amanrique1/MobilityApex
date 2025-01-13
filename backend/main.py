from fastapi import FastAPI, HTTPException, Query
from typing import Dict, List, Optional
import logging
from datetime import datetime
from database import query_to_df
from models import CategoryStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sales Analytics API",
    description="API for querying sales data across products, categories, and time periods",
    version="1.0.0"
)

def validate_date_format(date_str: Optional[str]) -> None:
    """Validates if the provided date string matches YYYY-MM-DD format."""
    if date_str:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Please use 'YYYY-MM-DD'"
            )

@app.get("/sales/product", response_model=List[Dict])
async def get_products(
    product: Optional[str] = Query(None, description="Product name to filter by"),
    category: Optional[str] = Query(None, description="Category name to filter by")
) -> List[Dict]:
    """Retrieves product sales data with optional filtering."""
    base_query = "SELECT * FROM sales"
    params = {}

    if product and category:
        base_query += " WHERE product = :product AND category = :category"
        params["product"] = product
        params["category"] = category
    elif product:
        base_query += " WHERE product = :product"
        params["product"] = product
    elif category:
        base_query += " WHERE category = :category"
        params["category"] = category

    df = query_to_df(base_query, params)
    return df.to_dict(orient="records")

@app.get("/sales/day", response_model=List[Dict])
async def get_daily_sales(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
) -> List[Dict]:
    """Retrieves daily sales data within an optional date range."""
    validate_date_format(start_date)
    validate_date_format(end_date)

    base_query = "SELECT * FROM sales"
    params = {}

    if start_date and end_date:
        base_query += " WHERE date BETWEEN :start_date AND :end_date"
        params["start_date"] = start_date
        params["end_date"] = end_date
    elif start_date:
        base_query += " WHERE date >= :start_date"
        params["start_date"] = start_date
    elif end_date:
        base_query += " WHERE date <= :end_date"
        params["end_date"] = end_date

    df = query_to_df(base_query, params)
    return df.to_dict(orient="records")

@app.get("/sales/category", response_model=CategoryStats)
async def get_sales_category() -> CategoryStats:
    """Retrieves aggregated sales statistics by category."""
    return CategoryStats(
        revenue=query_to_df("SELECT * FROM category_revenue").to_dict(orient="records"),
        mean=query_to_df("SELECT * FROM category_mean").to_dict(orient="records"),
        day=query_to_df("SELECT * FROM category_day").to_dict(orient="records")
    )

@app.get("/sales/outliers", response_model=List[Dict])
async def get_outliers() -> List[Dict]:
    """Retrieves sales data points identified as outliers."""
    df = query_to_df("SELECT * FROM outliers")
    return df.to_dict(orient="records")

@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    logger.info("Starting Sales Analytics API")

@app.on_event("shutdown")
async def shutdown_event():
    """Run cleanup tasks."""
    logger.info("Shutting down Sales Analytics API")