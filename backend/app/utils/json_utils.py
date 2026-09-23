from datetime import date, datetime

import numpy as np
import pandas as pd


def clean_json_value(value):
    """
    Convert pandas / NumPy values into JSON-safe Python values.
    """

    # None
    if value is None:
        return None

    # pandas NaT / NaN
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    # NumPy scalar types
    if isinstance(value, np.generic):
        return value.item()

    # pandas timestamp
    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    # Python datetime/date
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    return value


def clean_json_data(data):
    """
    Recursively sanitize dictionaries and lists.
    """

    if isinstance(data, dict):
        return {
            key: clean_json_data(value)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [
            clean_json_data(value)
            for value in data
        ]

    return clean_json_value(data)