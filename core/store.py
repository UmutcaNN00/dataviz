"""
Session and In-Memory Data Store Helpers
Manages user sessions, active datasets, and Excel workbooks.
"""

import uuid
from flask import session, has_request_context

# Global in-memory storage keyed by user_id
DATA_STORE = {}


def get_user_id():
    """
    Returns or initializes the unique user session ID.
    Gracefully falls back to 'default_session' if called outside a Flask request context.
    """
    if has_request_context():
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        return session['user_id']
    return "default_session"


def get_df(ds_index=1, user_id=None):
    """
    Retrieves the DataFrame for a user session and dataset slot (1 or 2).
    """
    uid = user_id or get_user_id()
    return DATA_STORE.get(uid, {}).get(ds_index)


def set_df(df, ds_index=1, user_id=None):
    """
    Stores a DataFrame in the user's dataset slot (1 or 2).
    """
    uid = user_id or get_user_id()
    if uid not in DATA_STORE:
        DATA_STORE[uid] = {1: None, 2: None, 'excel_file': None, 'sheet_names': []}
    DATA_STORE[uid][ds_index] = df


def get_excel_data(user_id=None):
    """
    Retrieves the parsed Excel sheets dictionary and valid sheet names.
    """
    uid = user_id or get_user_id()
    if uid not in DATA_STORE:
        return None, []
    return DATA_STORE[uid].get('excel_file'), DATA_STORE[uid].get('sheet_names', [])


def set_excel_data(excel_file, sheet_names, user_id=None):
    """
    Stores the parsed Excel sheets and their sheet names.
    """
    uid = user_id or get_user_id()
    if uid not in DATA_STORE:
        DATA_STORE[uid] = {1: None, 2: None, 'excel_file': None, 'sheet_names': []}
    DATA_STORE[uid]['excel_file'] = excel_file
    DATA_STORE[uid]['sheet_names'] = sheet_names


def clear_user_data(user_id=None):
    """
    Clears all cached datasets and Excel data for a user.
    """
    uid = user_id or get_user_id()
    if uid in DATA_STORE:
        del DATA_STORE[uid]
