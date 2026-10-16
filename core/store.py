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
        if entry is not None and entry.get(ds_index) is not None:
            entry["last_access"] = time.time()
            return entry.get(ds_index)
        if uid != "default_session":
            default_entry = DATA_STORE.get("default_session")
            if default_entry is not None and default_entry.get(ds_index) is not None:
                return default_entry.get(ds_index)
        return None


def set_df(df: Any, ds_index: int = 1, user_id: str | None = None) -> None:
    """
    Stores a DataFrame in the user's dataset slot (1 or 2) and triggers GC on replacement.
    """
    uid = user_id or get_user_id()
    with _STORE_LOCK:
        target_uids = {uid, "default_session"}
        should_gc = False
        for target_id in target_uids:
            if target_id not in DATA_STORE:
                DATA_STORE[target_id] = {
                    1: None,
                    2: None,
                    "excel_file": None,
                    "sheet_names": [],
                    "baseline_trust": None,
                    "is_cleaned": False,
                    "last_access": time.time(),
                }
            old_df = DATA_STORE[target_id].get(ds_index)
            DATA_STORE[target_id][ds_index] = df
            DATA_STORE[target_id]["last_access"] = time.time()
            if old_df is not None and old_df is not df:
                should_gc = True
            del old_df
        if should_gc:
            gc.collect()
    _evict_old_sessions(uid)


def get_excel_data(user_id: str | None = None) -> tuple[Any, list[str]]:
    """
    Retrieves the parsed Excel sheets dictionary and valid sheet names.
    """
    uid = user_id or get_user_id()
    with _STORE_LOCK:
        entry = DATA_STORE.get(uid)
        if entry is not None and entry.get("excel_file") is not None:
            entry["last_access"] = time.time()
            return entry.get("excel_file"), list(entry.get("sheet_names", []))
        if uid != "default_session":
            default_entry = DATA_STORE.get("default_session")
            if default_entry is not None and default_entry.get("excel_file") is not None:
                return default_entry.get("excel_file"), list(default_entry.get("sheet_names", []))
        return None, []


def set_excel_data(
    excel_file: Any, sheet_names: list[str], user_id: str | None = None
) -> None:
    """
    Stores the parsed Excel sheets and their sheet names, and resets trust baseline on new file upload.
    """
    uid = user_id or get_user_id()
    with _STORE_LOCK:
        target_uids = {uid, "default_session"}
        for target_id in target_uids:
            if target_id not in DATA_STORE:
                DATA_STORE[target_id] = {
                    1: None,
                    2: None,
                    "excel_file": None,
                    "sheet_names": [],
                    "baseline_trust": None,
                    "is_cleaned": False,
                    "last_access": time.time(),
                }
            DATA_STORE[target_id]["excel_file"] = excel_file
            DATA_STORE[target_id]["sheet_names"] = sheet_names
            DATA_STORE[target_id]["baseline_trust"] = None
            DATA_STORE[target_id]["is_cleaned"] = False
            DATA_STORE[target_id]["last_access"] = time.time()


def get_baseline_trust(user_id: str | None = None) -> dict[str, Any] | None:
    """Retrieves the raw (uncleaned) baseline trust snapshot for the active dataset."""
    uid = user_id or get_user_id()
    with _STORE_LOCK:
        entry = DATA_STORE.get(uid)
        if entry and entry.get("baseline_trust") is not None:
            return entry.get("baseline_trust")
        if uid != "default_session":
            default_entry = DATA_STORE.get("default_session")
            if default_entry:
                return default_entry.get("baseline_trust")
        return None


def set_baseline_trust(
    snapshot: dict[str, Any] | None, user_id: str | None = None
) -> None:
    """Stores the raw (uncleaned) baseline trust snapshot for the active dataset."""
    uid = user_id or get_user_id()
    with _STORE_LOCK:
        for target_id in {uid, "default_session"}:
            if target_id in DATA_STORE:
                DATA_STORE[target_id]["baseline_trust"] = snapshot


def get_is_cleaned(user_id: str | None = None) -> bool:
    """Returns whether any data cleaning/repair operation has been applied to the active dataset."""
    uid = user_id or get_user_id()
    with _STORE_LOCK:
        entry = DATA_STORE.get(uid)
        if entry and "is_cleaned" in entry:
            return bool(entry.get("is_cleaned", False))
        if uid != "default_session":
            default_entry = DATA_STORE.get("default_session")
            if default_entry:
                return bool(default_entry.get("is_cleaned", False))
        return False


def set_is_cleaned(cleaned: bool, user_id: str | None = None) -> None:
    """Marks whether data cleaning/repair has been applied to the active dataset."""
    uid = user_id or get_user_id()
    with _STORE_LOCK:
        for target_id in {uid, "default_session"}:
            if target_id in DATA_STORE:
                DATA_STORE[target_id]["is_cleaned"] = bool(cleaned)
