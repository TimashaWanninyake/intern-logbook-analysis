from __future__ import annotations
import os
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
from django.conf import settings
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId


def get_mongo_client() -> MongoClient:
    """
    Create a MongoDB client using Django settings or env vars.
    """
    uri = getattr(settings, "MONGODB_URI", None) or os.environ.get("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI not configured in settings or environment.")
    return MongoClient(uri)


def get_logbook_collection():
    """
    Return the MongoDB collection that stores logbook entries.
    """
    db_name = getattr(settings, "MONGODB_DB_NAME", None) or os.environ.get("MONGODB_DB_NAME")
    collection_name = getattr(settings, "MONGODB_LOGBOOK_COLLECTION", "dailyrecords")
    print(f"Using MongoDB Database: {db_name}, Collection: {collection_name}")
    if not db_name:
        raise RuntimeError("MONGODB_DB_NAME not configured in settings or environment.")
    client = get_mongo_client()
    return client[db_name][collection_name]



# def get_week_range(end_date: datetime | None = None, days: int = 7) -> tuple[datetime, datetime]:
#     """
#     Return (start, end) datetime objects for a sliding window of 'days' ending at end_date (inclusive).
#     """
#     if end_date is None:
#         end_date = datetime.utcnow()
#     start_date = end_date - timedelta(days=days - 1)
#     # Normalize to 00:00 and 23:59 for querying
#     start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
#     end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
#     return start_date, end_date

def get_week_range(days: int = 7):
    """
    Returns start_date_str, end_date_str in 'YYYY-MM-DD' format,
    without time components.
    """
    today = date(2025, 10, 25) #[TODO]:Hard coded date here. Make it to current date.
    start_date = today - timedelta(days=days - 1)
   
    return (
        start_date.strftime("%Y-%m-%d"),
        today.strftime("%Y-%m-%d"),
    )


def fetch_logbook_entries(
    intern_id: str,
    start_date: str,
    end_date: str,
) -> List[Dict[str, Any]]:
    """
    Fetch logbook entries for a single intern within a date range.
    Expected logbook schema:
      - intern_id (string)
      - date (ISO string or datetime)
      - status
      - tech_stack
      - todays_work
      - challenges
      - tomorrow_plan
    """
    collection = get_logbook_collection()   
    try:
        intern_object_id = ObjectId(intern_id)
    except InvalidId:
        # Fallback: in case something else is passed, use it as-is
        intern_object_id = intern_id

    query = {
        "internId": intern_object_id,
        "date": {
            "$gte": start_date,
            "$lte": end_date,
        },
    }

    cursor = collection.find(query).sort("date", 1)
    entries: List[Dict[str, Any]] = []

    for doc in cursor:
        # Convert Mongo datetime to python datetime, normalize keys
        entries.append(
            {
                "date": doc.get("date"),
                "status": (doc.get("status") or "").strip(),
                "tech_stack": (doc.get("stack") or "").strip(),
                "todays_work": (doc.get("task") or "").strip(),
                "challenges": (doc.get("progress") or "").strip(),
                "tomorrow_plan": (doc.get("blockers") or "").strip(),
            }
        )
    return entries
