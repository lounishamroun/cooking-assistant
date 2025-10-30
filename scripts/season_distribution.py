"""
Script for seasonal distribution by recipe type
"""

import pandas as pd
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import from the modular structure
from cooking_assistant.analysis.seasonal import get_season_from_date
from cooking_assistant.config import INTERIM_DATA_DIR

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
        from cooking_assistant.data.loader import load_classified_recipes
        from cooking_assistant.data.processor import prepare_merged_data
        
        print("Loading data...")
        recipes_df = load_classified_recipes()
        merged_df = prepare_merged_data()
        
        print(f"   • {len(merged_df):,} valid reviews")
        print(f"   • {len(recipes_df):,} recipes")
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
    filename = "season_type_distribution.csv"
    # Use a simple output path since JUSTIFICATION_PATH doesn't exist anymore
    output_dir = "/tmp"  # Will be overridden by calling function
    filepath = os.path.join(output_dir, filename)
    
    results_df.to_csv(filepath, index=False)
    
    print(f"\nFile saved: {filename}")
    print(f"Location: {output_dir}")
    
    return {
        'total_reviews': total_all,
        'results': results,
        'filepath': filepath,
        'dataframe': results_df
    }