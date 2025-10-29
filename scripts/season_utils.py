"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          SEASON UTILITIES                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

This module contains functions to determine the season from a date.
"""

import pandas as pd


def get_season_from_date(date):
    '''
    Returns the astronomical season corresponding to a date.
    
    Astronomical seasons:
    - Spring: March 21 to June 20
    - Summer: June 21 to September 20
    - Fall  : September 21 to December 20
    - Winter: December 21 to March 20
    
    Args:
        date (pd.Timestamp): Date to analyze
        
    Returns:
        str: Season name ('Spring', 'Summer', 'Fall', 'Winter')
    '''
    if pd.isna(date):
        return 'Unknown'
    
    month = date.month
    day = date.day
    
    # Season determination logic
    if (month == 3 and day >= 21) or (month in [4, 5]) or (month == 6 and day <= 20):
        return 'Spring'
    elif (month == 6 and day >= 21) or (month in [7, 8]) or (month == 9 and day <= 20):
        return 'Summer'
    elif (month == 9 and day >= 21) or (month in [10, 11]) or (month == 12 and day <= 20):
        return 'Fall'
    else:
        return 'Winter'
