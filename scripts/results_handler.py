"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           RESULTS MANAGEMENT                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

This module contains functions to save and display analysis results.
"""

import pandas as pd
import os
from datetime import datetime


def save_results(top_n_dict, recipe_type, results_path):
    """
    Saves results to a CSV file.
    
    Args:
        top_n_dict: Dictionary {season: DataFrame} with top N results
        recipe_type: Recipe type (plat, dessert, boisson)
        results_path: Path to output folder
        
    Returns:
        str: Path of saved file
    """
    
    print(f"\nSaving results - {recipe_type}...")
    
    # Combine all top N into a single DataFrame
    all_top_n = pd.concat(top_n_dict.values(), ignore_index=True)
    
    # Reorganize columns for clearer display
    columns_order = [
        'Saison', 'recipe_id', 'name', 'reviews_in_season', 
        'avg_rating', 'Q_Score_Bayesien', 
        'Poids_Popularite', 'Score_Final'
    ]
    all_top_n = all_top_n[columns_order]
    
    # Rename for clarity
    all_top_n = all_top_n.rename(columns={
        'reviews_in_season': 'Nb_Reviews_Season',
        'avg_rating': 'Average_Rating'
    })
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"top_20_{recipe_type}s_par_saison_{timestamp}.csv"
    filepath = os.path.join(results_path, filename)
    
    # Save
    all_top_n.to_csv(filepath, index=False, encoding='utf-8')
    print(f"File saved: {filename}")
    print(f"Location: {results_path}")
    
    return filepath


def display_summary(top_n_dict, recipe_type, season_order):
    """
    Displays a summary of the top N best recipes for each season in the console.
    
    Args:
        top_n_dict: Dictionary {season: DataFrame}
        recipe_type: Recipe type (used for display)
        season_order: List of seasons in order
    """
    
    for season in season_order:
        if season not in top_n_dict:
            continue
        
        top_n = top_n_dict[season]
        
        # Display top 5
        for _, row in top_n.head(5).iterrows():
            print(f"   {row.name + 1:2d}. {row['name'][:50]:50s} "
                  f"Score: {row['Score_Final']:.4f} "
                  f"(Rating: {row['avg_rating']:.2f}/5)")
        
        if len(top_n) > 5:
            print(f"   ... and {len(top_n) - 5} other recipes")
        
        print()
