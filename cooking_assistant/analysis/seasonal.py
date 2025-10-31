"""Season derivation utilities.

Provides :func:`get_season_from_date` which maps a pandas ``Timestamp`` to
an astronomical season label (Spring, Summer, Fall, Winter). Invalid or
missing dates yield ``"Unknown"``.
"""

import pandas as pd


def get_season_from_date(date: pd.Timestamp) -> str:
    """Return the astronomical season for a given date.

    Boundaries (inclusive start, inclusive end):
    - Spring: 21 Mar – 20 Jun
    - Summer: 21 Jun – 20 Sep
    - Fall  : 21 Sep – 20 Dec
    - Winter: 21 Dec – 20 Mar

    Parameters
    ----------
    date : pd.Timestamp
        Parsed timestamp; ``NaT`` returns ``"Unknown"``.

    Returns
    -------
    str
        One of ``"Spring"``, ``"Summer"``, ``"Fall"``, ``"Winter"`` or ``"Unknown"``.
    """
    if pd.isna(date):
        return 'Unknown'
    
    month = date.month
    day = date.day
    
    # Season determination
    if (month == 3 and day >= 21) or (month in [4, 5]) or (month == 6 and day <= 20):
        return 'Spring'
    elif (month == 6 and day >= 21) or (month in [7, 8]) or (month == 9 and day <= 20):
        return 'Summer'
    elif (month == 9 and day >= 21) or (month in [10, 11]) or (month == 12 and day <= 20):
        return 'Fall'
    else:
        return 'Winter'


if __name__ == "__main__":
    # Tests
    from datetime import datetime
    
    test_dates = [
        datetime(2024, 3, 21),   # First day of spring
        datetime(2024, 6, 21),   # First day of summer
        datetime(2024, 9, 21),   # First day of fall
        datetime(2024, 12, 21),  # First day of winter
        datetime(2024, 7, 14),   # Summer
    ]
    
    for date in test_dates:
        season = get_season_from_date(pd.Timestamp(date))
        print(f"{date.strftime('%Y-%m-%d')} → {season}")
