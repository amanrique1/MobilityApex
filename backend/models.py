from pydantic import BaseModel
from typing import List, Dict

class CategoryStats(BaseModel):
    """Model for category-wise statistics"""
    revenue: List[Dict]
    mean: List[Dict]
    day: List[Dict]