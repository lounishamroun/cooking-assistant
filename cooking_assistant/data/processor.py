"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     DATA PREPROCESSING AND MERGING                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module to merge recipes with interactions and add seasons.
Based on scripts/data_loader_preparation.py
"""

import pandas as pd
from typing import Optional

from ..analysis.seasonal import get_season_from_date


def prepare_merged_data(
    recipes_df: pd.DataFrame,
    interactions_df: pd.DataFrame,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Merges recipes with interactions and adds the 'season' column.
    
    Args:
        recipes_df: DataFrame of recipes (must contain 'id', 'name', 'type')
        interactions_df: DataFrame of interactions (must contain 'recipe_id', 'rating', 'date')
        verbose: Display progress information
        
    Returns:
        Merged DataFrame with columns: recipe_id, name, type, rating, date, season, year
    """
    if verbose:
        print("DATA PREPARATION")
        print("=" * 40)
    
    # Check that required columns exist
    required_recipe_cols = ['id', 'name', 'type']
    required_interaction_cols = ['recipe_id', 'rating', 'date']
    
    missing_recipe = [col for col in required_recipe_cols if col not in recipes_df.columns]
    missing_interaction = [col for col in required_interaction_cols if col not in interactions_df.columns]
    
    if missing_recipe:
        raise ValueError(f"Missing columns in recipes_df: {missing_recipe}")
    if missing_interaction:
        raise ValueError(f"Missing columns in interactions_df: {missing_interaction}")
    
    # Merge recipes with interactions
    if verbose:
        print("\n Merging recipes with interactions")
    
    merged_df = interactions_df.merge(
        recipes_df[['id', 'name', 'type']],
        left_on='recipe_id',
        right_on='id',
        how='left'
    )
    
    if verbose:
        print(f"{len(merged_df):,} rows after merge")
    
    # Convert dates and add season
    if verbose:
        print("\n2 Converting dates and calculating seasons")
    
    merged_df['date_parsed'] = pd.to_datetime(merged_df['date'], errors='coerce')
    merged_df['season'] = merged_df['date_parsed'].apply(get_season_from_date)
    merged_df['year'] = merged_df['date_parsed'].dt.year
    
    if verbose:
        print("Seasons added")
    
    # Display statistics by type
    if verbose:
        print("\nDistribution by recipe type:")
        type_counts = merged_df['type'].value_counts().sort_index()
        for recipe_type, count in type_counts.items():
            percentage = (count / len(merged_df)) * 100
            print(f"   • {recipe_type:10s} : {count:>8,} reviews ({percentage:>5.2f}%)")
    
    # Display statistics by season
    if verbose:
        print("\nDistribution by season:")
        season_counts = merged_df['season'].value_counts()
        for season in ['Spring', 'Summer', 'Fall', 'Winter']:
            count = season_counts.get(season, 0)
            percentage = (count / len(merged_df)) * 100 if len(merged_df) > 0 else 0
            print(f"   • {season:10s} : {count:>8,} reviews ({percentage:>5.2f}%)")
        
        unknown = season_counts.get('Unknown', 0)
        if unknown > 0:
            print(f"   • {'Unknown':10s} : {unknown:>8,} reviews")
    
    if verbose:
        print("\n" + "=" * 80)
        print(f"Preparation completed: {len(merged_df):,} merged rows")
        print("=" * 80 + "\n")
    
    return merged_df


if __name__ == "__main__":
    # Test module
    from .loader import load_data
    
    recipes, interactions = load_data()
    merged = prepare_merged_data(recipes, interactions)
    
    print("\nPreparation test successful!")
    print(f"Columns: {list(merged.columns)}")
    print(f"Shape: {merged.shape}")
