"""
SEASONAL UTILITIES

Module to determine season from a date.
Based on scripts/season_utils.py
"""

import pandas as pd


def get_season_from_date(date: pd.Timestamp) -> str:
    """
    Returns the astronomical season corresponding to a date.
    
    Astronomical seasons:
    - Spring: March 21 to June 20
    - Summer: June 21 to September 20
    - Fall: September 21 to December 20
    - Winter: December 21 to March 20
    
    Args:
        date: Date to analyze (pd.Timestamp)
        
    Returns:
        Season name: 'Spring', 'Summer', 'Fall', 'Winter', or 'Unknown'
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
