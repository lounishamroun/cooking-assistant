"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                       TOP REVIEWS ANALYZER                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

This module analyzes the top 100 recipes by number of reviews, organized by type and season.
Generates CSV files for parameter justification analysis.
"""

import pandas as pd
import os
from datetime import datetime


def analyze_top_reviews_by_type_season(merged_df, recipes_df, output_dir, top_n=100):
    """
    Analyzes the top N recipes by number of reviews for each type and season.
    
    Args:
        merged_df: Merged DataFrame with interactions and recipe types
        recipes_df: DataFrame with recipe information
        output_dir: Directory to save CSV files
        top_n: Number of top recipes to extract (default: 100)
    
    Returns:
        dict: Dictionary with results organized by type and season
    """
    
    print(f"Analyzing top {top_n} recipes by review count...")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Recipe types and seasons to analyze
    recipe_types = ['plat', 'dessert', 'boisson']
    seasons = ['Spring', 'Summer', 'Fall', 'Winter']
    
    # Results storage
    all_results = []
    results_by_type_season = {}
    
    # Analyze each combination of type and season
    for recipe_type in recipe_types:
        print(f"\nAnalyzing {recipe_type.upper()}...")
        
        # Filter by recipe type
        type_df = merged_df[merged_df['type'] == recipe_type].copy()
        
        results_by_type_season[recipe_type] = {}
        
        for season in seasons:
                
            # Filter by season
            season_df = type_df[type_df['season'] == season].copy()
            
            if len(season_df) == 0:
                print(f"No data for {recipe_type} in {season}")
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
            
            # Fill missing values for recipes with no valid ratings
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
            
            print(f"Top {len(top_recipes)} recipes extracted")
            print(f"Max reviews: {top_recipes['total_reviews'].max()}")
            print(f"Min reviews: {top_recipes['total_reviews'].min()}")
            print(f"Avg rating: {top_recipes['avg_valid_rating'].mean():.3f}")

    # Combine all results
    combined_results = pd.concat(all_results, ignore_index=True)
    
    # Median analysis section
    print(f"\nCalculating median analysis for top {top_n}")
    
    # Calculate medians by type and season
    median_analysis = []
    
    print("MEDIAN TOP 100 BY SEASON AND TYPE")
   

    for recipe_type in recipe_types:
        print(f"\n{recipe_type.upper()}")
       
        
        type_medians = []
        
        for season in seasons:
            # Filter data for this type and season
            season_type_data = combined_results[
                (combined_results['type'] == recipe_type) & 
                (combined_results['season'] == season)]
            
            if len(season_type_data) > 0:
                median_reviews = season_type_data['total_reviews'].median()
                max_reviews = season_type_data['total_reviews'].max()
                min_reviews = season_type_data['total_reviews'].min()
                type_medians.append(median_reviews)
                
                median_analysis.append({
                    'Type_Recette': recipe_type,
                    'Saison': season,
                    'Mediane_Reviews_Top100': median_reviews,
                    'Max_Reviews_Top100': max_reviews,
                    'Min_Reviews_Top100': min_reviews,
                    'Nb_Recettes_Analysees': len(season_type_data)
                })
                
                print(f"{season:8s}: {median_reviews:6.0f} reviews (median)")
                print(f"{max_reviews:6.0f} reviews (max)")
                print(f"{min_reviews:6.0f} reviews (min)")
            else:
                print(f"{season:8s}: No data")

    # Create median DataFrame
    median_df = pd.DataFrame(median_analysis)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Merge median statistics with combined results
    if not median_df.empty:
        # Create median mapping by type and season
        median_df_merge = median_df.rename(columns={
            'Type_Recette': 'type',
            'Saison': 'season',
            'Mediane_Reviews_Top100': 'median_reviews_type_season',
            'Max_Reviews_Top100': 'max_reviews_type_season',
            'Min_Reviews_Top100': 'min_reviews_type_season',
            'Nb_Recettes_Analysees': 'nb_recipes_in_top'
        })
        
        # Add statistics columns to combined DataFrame
        combined_results = combined_results.merge(
            median_df_merge,
            on=['type', 'season'],
            how='left'
        )

        print("\n> Median statistics added to combined file")

    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    combined_filename = f"top_{top_n}_reviews_by_type_season_{timestamp}.csv"
    combined_filepath = os.path.join(output_dir, combined_filename)
    
    # Reorder columns for better readability
    column_order = [
        'season', 'type', 'recipe_id', 'name', 'total_reviews', 'valid_reviews',
        'median_reviews_type_season'
    ]
    
    combined_results = combined_results[column_order]
    combined_results.to_csv(combined_filepath, index=False, encoding='utf-8')
    
    print(f"\nCombined results saved: {combined_filename}")
    print(f"Location: {output_dir}")
    print(f"Total records: {len(combined_results):,}")
    print("\nAnalysis completed successfully!")
    
    return {
        'combined_results': combined_results,
        'by_type_season': results_by_type_season,
        'median_analysis': median_df if not median_df.empty else None,
        'files_created': {
            'combined': combined_filepath
        }
    }


