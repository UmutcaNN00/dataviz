"""
Session and In-Memory Data Store Helpers
Manages user sessions, active datasets, and Excel workbooks.
"""

import gc
import threading
import time
import uuid
from typing import Any

from flask import has_request_context, session

from core.config import MAX_ACTIVE_SESSIONS

# Global in-memory storage keyed by user_id
DATA_STORE: dict[str, dict[Any, Any]] = {}
_STORE_LOCK = threading.RLock()


def _evict_old_sessions(current_uid: str) -> None:
    """Evicts oldest inactive sessions when DATA_STORE exceeds MAX_ACTIVE_SESSIONS."""
    with _STORE_LOCK:
        if len(DATA_STORE) <= MAX_ACTIVE_SESSIONS:
            return
        sorted_uids = sorted(
            (uid for uid in DATA_STORE if uid != current_uid),
            key=lambda u: DATA_STORE[u].get("last_access", 0),
        )
        while len(DATA_STORE) > MAX_ACTIVE_SESSIONS and sorted_uids:
            old_uid = sorted_uids.pop(0)
            DATA_STORE.pop(old_uid, None)
        gc.collect()


def get_user_id() -> str:
    """
    Returns or initializes the unique user session ID.
    Gracefully falls back to 'default_session' if called outside a Flask request context.
    """
    if has_request_context():
        if "user_id" not in session:
            session["user_id"] = str(uuid.uuid4())
        return str(session["user_id"])
    return "default_session"


def get_df(ds_index: int = 1, user_id: str | None = None) -> Any:
    """
    Retrieves the DataFrame for a user session and dataset slot (1 or 2).
    """
    uid = user_id or get_user_id()
    with _STORE_LOCK:
        entry = DATA_STORE.get(uid)
        if entry is not None:
            entry["last_access"] = time.time()
            return entry.get(ds_index)
        return None


def set_df(df: Any, ds_index: int = 1, user_id: str | None = None) -> None:
    """
    Stores a DataFrame in the user's dataset slot (1 or 2) and triggers GC on replacement.
    """
    uid = user_id or get_user_id()
    with _STORE_LOCK:
        if uid not in DATA_STORE:
            DATA_STORE[uid] = {
                1: None,
                2: None,
                "excel_file": None,
                "sheet_names": [],
                "last_access": time.time(),
            }
        old_df = DATA_STORE[uid].get(ds_index)
        DATA_STORE[uid][ds_index] = df
        DATA_STORE[uid]["last_access"] = time.time()
        if old_df is not None and old_df is not df:
            del old_df
            gc.collect()
    _evict_old_sessions(uid)


def get_excel_data(user_id: str | None = None) -> tuple[Any, list[str]]:
    """
    Retrieves the parsed Excel sheets dictionary and valid sheet names.
    """
    uid = user_id or get_user_id()
    with _STORE_LOCK:
        if uid not in DATA_STORE:
            return None, []
        DATA_STORE[uid]["last_access"] = time.time()
        return DATA_STORE[uid].get("excel_file"), list(
            DATA_STORE[uid].get("sheet_names", [])
        )


def set_excel_data(
    excel_file: Any, sheet_names: list[str], user_id: str | None = None
) -> None:
    """
    Stores the parsed Excel sheets and their sheet names.
    """
    uid = user_id or get_user_id()
    with _STORE_LOCK:
        if uid not in DATA_STORE:
            DATA_STORE[uid] = {
                1: None,
                2: None,
                "excel_file": None,
                "sheet_names": [],
                "last_access": time.time(),
            }
        DATA_STORE[uid]["excel_file"] = excel_file
        DATA_STORE[uid]["sheet_names"] = sheet_names
        DATA_STORE[uid]["last_access"] = time.time()


def clear_user_data(user_id: str | None = None) -> None:
    """
    Clears all cached datasets and Excel data for a user.
    """
    uid = user_id or get_user_id()
    with _STORE_LOCK:
        if uid in DATA_STORE:
            del DATA_STORE[uid]
            gc.collect()
