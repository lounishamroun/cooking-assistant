"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     DATA LOADING AND PREPARATION                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

This module contains functions to load CSV data and prepare it for analysis.
"""

import pandas as pd
import os
from .season_utils import get_season_from_date


def load_data(data_path):
    '''
    Loads CSV files containing recipes and interactions (reviews).
    
    Args:
        data_path (str): Path to the folder containing the data
        
    Returns:
        tuple: (recipes_df, interactions_df)
            - recipes_df: DataFrame with recipes (id, name, etc.)
            - interactions_df: DataFrame with reviews (recipe_id, rating, date, etc.)
    '''
    print("Loading data")
    
    # Load the classified recipes file
    recipes_path = os.path.join(data_path, "recipes_classified.csv")
    recipes_df = pd.read_csv(recipes_path, encoding='utf-8')
    print(f"Recipes loaded: {len(recipes_df)} recipes")
    
    # Load the interactions file (reviews)
    interactions_path = os.path.join(data_path, "RAW_interactions.csv")
    interactions_df = pd.read_csv(interactions_path, encoding='utf-8')
    print(f"Interactions loaded: {len(interactions_df)} reviews")
    
    return recipes_df, interactions_df


def prepare_data(recipes_df, interactions_df):
    '''
    Merges recipes with their reviews and adds the season column.
    
    Args:
        recipes_df: DataFrame of recipes
        interactions_df: DataFrame of interactions
        
    Returns:
        pd.DataFrame: Merged DataFrame with 'season', 'type', etc. columns
    '''
    print("\n Data preparation")

    
    # Merge recipes with interactions
    merged_df = interactions_df.merge(
        recipes_df[['id', 'name', 'type']], 
        left_on='recipe_id', 
        right_on='id', 
        how='left'
    )
    
    # Convert dates and add season column
    merged_df['date_parsed'] = pd.to_datetime(merged_df['date'], errors='coerce')
    merged_df['season'] = merged_df['date_parsed'].apply(get_season_from_date)
    merged_df['year'] = merged_df['date_parsed'].dt.year
    print("Seasons added")
    
    # Display recipe type distribution
    print("Distribution by type:")
    type_counts = merged_df['type'].value_counts()
    for recipe_type, count in type_counts.items():
        print(f"   • {recipe_type:10s}: {count:,} reviews")
    
    return merged_df

