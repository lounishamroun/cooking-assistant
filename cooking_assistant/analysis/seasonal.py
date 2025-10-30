"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         UTILITAIRES SAISONNIERS                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module pour déterminer la saison à partir d'une date.
Basé sur scripts/season_utils.py
"""

import pandas as pd


def get_season_from_date(date: pd.Timestamp) -> str:
    """
    Retourne la saison astronomique correspondant à une date.
    
    Saisons astronomiques :
    - Spring (Printemps) : 21 mars au 20 juin
    - Summer (Été)       : 21 juin au 20 septembre
    - Fall (Automne)     : 21 septembre au 20 décembre
    - Winter (Hiver)     : 21 décembre au 20 mars
    
    Args:
        date: Date à analyser (pd.Timestamp)
        
    Returns:
        Nom de la saison : 'Spring', 'Summer', 'Fall', 'Winter', ou 'Unknown'
    """
    if pd.isna(date):
        return 'Unknown'
    
    month = date.month
    day = date.day
    
    # Détermination de la saison
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
        datetime(2024, 3, 21),   # Premier jour du printemps
        datetime(2024, 6, 21),   # Premier jour de l'été
        datetime(2024, 9, 21),   # Premier jour de l'automne
        datetime(2024, 12, 21),  # Premier jour de l'hiver
        datetime(2024, 7, 14),   # Été
    ]
    
    for date in test_dates:
        season = get_season_from_date(pd.Timestamp(date))
        print(f"{date.strftime('%Y-%m-%d')} → {season}")
