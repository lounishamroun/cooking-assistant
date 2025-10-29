"""
Script for seasonal distribution by recipe type
"""

import pandas as pd
import os

# Import season_utils module (from same folder)
from .season_utils import get_season_from_date

# Import centralized configuration
from .config import DATA_PATH, JUSTIFICATION_PATH

def analyze_seasonal_distribution(merged_df=None):
    """
    Analyzes the distribution of reviews by season and recipe type.
    
    Args:
        merged_df: Pre-loaded DataFrame with season and type columns.
    
    Returns:
        dict: Analysis results with keys 'total_reviews', 'results', 'filepath'
    """
    print("\n[SEASONAL DISTRIBUTION ANALYSIS BY TYPE]")
    
    # Load data only if not provided
    if merged_df is None:
        interactions_path = os.path.join(DATA_PATH, "RAW_interactions.csv")
        recipes_path = os.path.join(DATA_PATH, "recipes_classified.csv")
        
        print("Loading data...")
        interactions_df = pd.read_csv(interactions_path, usecols=['recipe_id', 'date', 'rating'])
        recipes_df = pd.read_csv(recipes_path, usecols=['id', 'type'])
        
        # Clean interactions
        interactions_df['date'] = pd.to_datetime(interactions_df['date'], errors='coerce')
        interactions_df = interactions_df.dropna()
        
        print(f"   • {len(interactions_df):,} valid reviews")
        print(f"   • {len(recipes_df):,} recipes")
        
        # Add seasons
        interactions_df['season'] = interactions_df['date'].apply(get_season_from_date)
        
        print("Using existing classification (plat, dessert, boisson)")
        
        # Merge data
        merged_df = interactions_df.merge(recipes_df[['id', 'type']], 
                                         left_on='recipe_id', right_on='id', how='inner')
        
        print(f"{len(merged_df):,} reviews with identified type")
    else:
        print("Using pre-loaded data...")
        print(f"{len(merged_df):,} reviews")
    
    # Calculate distributions by type
    results = []
    total_all = len(merged_df)
    
    print("\n[Distribution by recipe type]:")
    print("=" * 55)
    
    for recipe_type in ['plat', 'dessert', 'boisson']:
        type_data = merged_df[merged_df['type'] == recipe_type]
        total_type = len(type_data)
        
        print(f"\n{recipe_type.upper()} ({total_type:,} reviews)")
        print("-" * 35)
        
        for season in ['Spring', 'Summer', 'Fall', 'Winter']:
            season_count = len(type_data[type_data['season'] == season])
            percentage = (season_count / total_type * 100) if total_type > 0 else 0
            
            results.append([recipe_type, season, season_count, round(percentage, 2)])
            print(f"   {season:8}: {season_count:6,} ({percentage:5.1f}%)")
    
    # Create DataFrame
    results_df = pd.DataFrame(results, columns=[
        'Type_Recette', 'Saison', 'Nombre_Reviews', 'Pourcentage'
    ])
    
    # Save
    filename = "distribution_saisonniere_par_type.csv"
    filepath = os.path.join(JUSTIFICATION_PATH, filename)
    
    results_df.to_csv(filepath, index=False)
    
    print(f"\nFile saved: {filename}")
    print(f"Location: {JUSTIFICATION_PATH}")
    
    return {
        'total_reviews': total_all,
        'results': results,
        'filepath': filepath,
        'dataframe': results_df
    }