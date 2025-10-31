"""Top review volume analysis.

Generates per type × season tables of the most reviewed recipes and derives
median statistics used to justify Bayesian parameter calibration.
Outputs are saved as timestamped CSV files intended for transparent audit.
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, Optional

from ..config import RECIPE_TYPES, SEASONS, JUSTIFICATION_DIR


def analyze_top_reviews_by_type_season(
    merged_df: pd.DataFrame,
    recipes_df: pd.DataFrame,
    output_dir: str = str(JUSTIFICATION_DIR),
    top_n: int = 100,
    verbose: bool = True
) -> Dict:
    """Compile top-N most reviewed recipes per (type, season) and medians.

    For each recipe type and season the function counts total reviews
    (all interactions) and valid reviews (rating > 0), computes an average
    rating over valid reviews, ranks recipes by total review volume, and
    stores the top-N subset. Afterwards, a seasonal median review count
    summary is generated and merged back for parameter justification.

    Parameters
    ----------
    merged_df : pd.DataFrame
        Interaction-level data joined to recipe metadata; must include
        columns ``recipe_id``, ``rating``, ``season``, ``type``.
    recipes_df : pd.DataFrame
        Recipes catalog including columns ``id``, ``name``.
    output_dir : str, default ``JUSTIFICATION_DIR``
        Destination directory for the timestamped combined CSV.
    top_n : int, default 100
        Number of recipes retained per (type, season) combination.
    verbose : bool, default True
        When True prints progress and small summaries.

    Returns
    -------
    Dict
        Keys: ``combined_results`` (pd.DataFrame), ``by_type_season`` (nested
        dict), ``median_analysis`` (pd.DataFrame or None), ``files_created``
        (paths of generated artifacts).
    """
    if verbose:
        print(f"\n{'=' * 80}")
        print(f"ANALYZING TOP {top_n} RECIPES BY NUMBER OF REVIEWS")
        print(f"{'=' * 80}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Store results
    all_results = []
    results_by_type_season = {}
    
    # Analyze each type × season combination
    for recipe_type in RECIPE_TYPES:
        if verbose:
            print(f"\nAnalyzing {recipe_type.upper()}...")
        
        # Filter by recipe type
        type_df = merged_df[merged_df['type'] == recipe_type].copy()
        
        results_by_type_season[recipe_type] = {}
        
        for season in SEASONS:
            # Filter by season
            season_df = type_df[type_df['season'] == season].copy()
            
            if len(season_df) == 0:
                if verbose:
                    print(f"   {season:10s} : No data")
                continue
            
            # Count reviews per recipe (all reviews including rating=0)
            total_reviews = season_df.groupby('recipe_id').size().reset_index(name='total_reviews')
            
            # Count only valid ratings (rating > 0)
            valid_ratings = season_df[season_df['rating'] > 0].groupby('recipe_id').agg({
                'rating': ['count', 'mean']
            }).reset_index()
            valid_ratings.columns = ['recipe_id', 'valid_reviews', 'avg_valid_rating']
            
            # Merge with valid ratings
            review_stats = total_reviews.merge(valid_ratings, on='recipe_id', how='left')
            
            # Fill missing values
            review_stats['valid_reviews'] = review_stats['valid_reviews'].fillna(0)
            review_stats['avg_valid_rating'] = review_stats['avg_valid_rating'].fillna(0)
            
            # Add recipe names
            review_stats = review_stats.merge(
                recipes_df[['id', 'name']],
                left_on='recipe_id',
                right_on='id',
                how='left'
            ).drop(columns=['id'])
            
            # Add metadata
            review_stats['type'] = recipe_type
            review_stats['season'] = season
            
            # Sort by total reviews and take top N
            top_recipes = review_stats.sort_values('total_reviews', ascending=False).head(top_n)
            
            # Store results
            results_by_type_season[recipe_type][season] = top_recipes
            all_results.append(top_recipes)
            
            if verbose:
                print(f"   {season:10s} : {len(top_recipes)} recipes extracted")
                print(f"                 Max reviews : {top_recipes['total_reviews'].max()}")
                print(f"                 Min reviews : {top_recipes['total_reviews'].min()}")
                print(f"                 Avg rating  : {top_recipes['avg_valid_rating'].mean():.3f}")
    
    # Combine all results
    combined_results = pd.concat(all_results, ignore_index=True)
    
    # Median analysis
    if verbose:
        print(f"\n{'=' * 80}")
        print(f"MEDIAN ANALYSIS (TOP {top_n})")
        print(f"{'=' * 80}")
    
    median_analysis = []
    
    for recipe_type in RECIPE_TYPES:
        if verbose:
            print(f"\n{recipe_type.upper()}")
        
        for season in SEASONS:
            season_type_data = combined_results[
                (combined_results['type'] == recipe_type) & 
                (combined_results['season'] == season)
            ]
            
            if len(season_type_data) > 0:
                median_reviews = season_type_data['total_reviews'].median()
                max_reviews = season_type_data['total_reviews'].max()
                min_reviews = season_type_data['total_reviews'].min()
                
                median_analysis.append({
                    'Type_Recette': recipe_type,
                    'Saison': season,
                    'Mediane_Reviews_Top100': median_reviews,
                    'Max_Reviews_Top100': max_reviews,
                    'Min_Reviews_Top100': min_reviews,
                    'Nb_Recettes_Analysees': len(season_type_data)
                })
                
                if verbose:
                    print(f"   {season:10s} : {median_reviews:6.0f} reviews (median)")
            else:
                if verbose:
                    print(f"   {season:10s} : No data")
    
    # Create median DataFrame
    median_df = pd.DataFrame(median_analysis) if median_analysis else pd.DataFrame()
    
    # Merge median statistics with combined results
    if not median_df.empty:
        median_df_merge = median_df.rename(columns={
            'Type_Recette': 'type',
            'Saison': 'season',
            'Mediane_Reviews_Top100': 'median_reviews_type_season',
            'Max_Reviews_Top100': 'max_reviews_type_season',
            'Min_Reviews_Top100': 'min_reviews_type_season',
            'Nb_Recettes_Analysees': 'nb_recipes_in_top'
        })
        
        combined_results = combined_results.merge(
            median_df_merge,
            on=['type', 'season'],
            how='left'
        )
        
        if verbose:
            print("\nMedian statistics added to combined file")
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    combined_filename = f"top_{top_n}_reviews_by_type_season_{timestamp}.csv"
    combined_filepath = os.path.join(output_dir, combined_filename)
    
    # Reorganize columns for better readability
    column_order = [
        'season', 'type', 'recipe_id', 'name', 'total_reviews', 'valid_reviews',
        'median_reviews_type_season'
    ]
    
    # Ensure all columns exist
    available_columns = [col for col in column_order if col in combined_results.columns]
    combined_results = combined_results[available_columns]
    
    combined_results.to_csv(combined_filepath, index=False, encoding='utf-8')
    
    if verbose:
        print(f"\n{'=' * 80}")
        print(f"Results saved: {combined_filename}")
        print(f"   Location: {output_dir}")
        print(f"   Total rows: {len(combined_results):,}")
        print(f"{'=' * 80}\n")
    
    return {
        'combined_results': combined_results,
        'by_type_season': results_by_type_season,
        'median_analysis': median_df if not median_df.empty else None,
        'files_created': {
            'combined': combined_filepath
        }
    }


if __name__ == "__main__":
    print("Top reviews analysis module")
    print("Use this module via scripts or API")
