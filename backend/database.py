import sqlite3
import pandas as pd
from typing import Optional, Dict, Any, Union
from sqlalchemy import text
import logging
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_PATH = "data.db"  # Update this with your actual database path

@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def query_to_df(
    query: str,
    params: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Executes a SQL query and returns the result as a pandas DataFrame.
    Handles raw SQL strings and SQLAlchemy text objects.
    """

    try:
        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)
    except sqlite3.Error as e:
        logger.error(f"Database query error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise