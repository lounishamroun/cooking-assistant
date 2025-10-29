"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    RECIPE RECOMMENDATION SYSTEM                              ║
║                    Based on Bayesian Q-Score                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

This main script orchestrates the recipe analysis process and generates
the top 20 best recipes by type and season. it also adds a top 100 reviews analysis
for parameter justification and a proportion analysis of seasonal distribution of reviews that helps
to justify the parameters used in the recommendation system.

METHODOLOGY:
------------
1. Bayesian Q-Score: Combines average rating with Bayesian regression
   to prevent recipes with few reviews from having inflated scores.
   
2. Popularity Weight: Uses exponential function to favor
   recipes that have been tested by more people.
   
3. Final Score: Multiplies Q-Score by popularity weight to obtain
   a balanced score between quality and confidence.

FORMULAS:
---------
- Q-Score = (valid_avg_rating * nb_valid_ratings + season_avg * kb) / (nb_valid_ratings + kb)
- Pop_Weight = (1 - exp(-nb_season_reviews / kpop))^gamma
- Final_Score = Q-Score * Pop_Weight

valid_avg_rating: Average rating considering only ratings > 0
nb_valid_ratings: Number of reviews with rating > 0
season_avg: Average rating across all recipes in the season
kb: Bayesian regression parameter (pseudo-reviews)
nb_season_reviews: Total number of reviews for the recipe in the season
kpop: Popularity threshold parameter
gamma: Popularity amplification factor

PARAMETERS BY TYPE:
-------------------
- Main Dishes : kb=65,  kpop=45,  gamma=1.2
- Desserts    : kb=60,  kpop=40,  gamma=1.2
- Beverages   : kb=20,  kpop=4,   gamma=0.7
"""

import os
import sys
import pandas as pd

# Add scripts folder to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

# Import local modules
from scripts.config import (
    DATA_PATH, RESULTS_PATH, JUSTIFICATION_PATH, SEASON_ORDER, TOP_N,
    PARAMS_PLATS, PARAMS_DESSERTS, PARAMS_BOISSONS
)
from scripts.data_loader_preparation import load_data, prepare_data
from scripts.score_calculator import calculate_top_n_by_type
from scripts.results_handler import save_results, display_summary
from scripts.season_distribution import analyze_seasonal_distribution
from scripts.top_reviews_analyzer import analyze_top_reviews_by_type_season


def main():
    """
    Main function that orchestrates the entire process.
    
    PROCESS:
    --------
    1. Generate parameter justification analysis:
       - Seasonal distribution by recipe type
       - Top 100 reviews analysis for parameter justification
    2. Load data (recipes + interactions)
    3. Prepare data (merge + add season)
    4. Calculate top 20 for each recipe type:
       - Main Dishes
       - Desserts
       - Beverages
    5. Save results to CSV
    6. Display summary
    
    OUTPUT FILES:
    -------------
    Main Analysis (in results/):
    - top_20_plats_par_saison.csv
    - top_20_desserts_par_saison.csv  
    - top_20_boissons_par_saison.csv
    
    Parameter Justification (in bayesian_parameters_justification/):
    - distribution_saisonniere_par_type.csv
    - top_100_reviews_by_type_season.csv (combined only)
    """ 
    try:
        # STEP 1: Generate parameter justification analysis
        print("\n[PARAMETER JUSTIFICATION ANALYSIS]")
        print("="*70)
        
        # Load and prepare data once
        print("Loading and preparing data...")
        recipes_df, interactions_df = load_data(DATA_PATH)
        merged_df = prepare_data(recipes_df, interactions_df)
        
        # 1a. Seasonal distribution analysis (reuse loaded data)
        print("\nAnalyzing seasonal distribution by recipe type...")
        seasonal_results = analyze_seasonal_distribution(merged_df)
        print(f"   > Seasonal distribution analyzed: {seasonal_results['total_reviews']:,} reviews")
        
        # 1b. Top 100 reviews analysis (reuse loaded data)
        print("\nAnalyzing top 100 recipes by review count...")
        reviews_analysis = analyze_top_reviews_by_type_season(
            merged_df, recipes_df, JUSTIFICATION_PATH, top_n=100
        )
        print("   > Top 100 reviews analysis completed")
        
        print(f"\nParameter justification files saved in: {JUSTIFICATION_PATH}")
        
        # STEP 2-3: Main analysis pipeline (reuse already loaded data)
        print("\n[MAIN ANALYSIS PIPELINE]")
        print("="*50)
        
        # STEP 4: Calculate top 20 for each type
        results = {}
        
        # MAIN DISHES
        results['plat'] = calculate_top_n_by_type(
            merged_df, recipes_df, 'plat', PARAMS_PLATS, SEASON_ORDER, TOP_N
        )
        
        # DESSERTS
        results['dessert'] = calculate_top_n_by_type(
            merged_df, recipes_df, 'dessert', PARAMS_DESSERTS, SEASON_ORDER, TOP_N
        )
        
        # BEVERAGES
        results['boisson'] = calculate_top_n_by_type(
            merged_df, recipes_df, 'boisson', PARAMS_BOISSONS, SEASON_ORDER, TOP_N
        )
        
        # STEP 5: Save results
        print("\n[SAVING RESULTS]")       
        saved_files = {}
        for recipe_type, top_n_dict in results.items():
            saved_files[recipe_type] = save_results(top_n_dict, recipe_type, RESULTS_PATH)
        
        # STEP 6: Display summaries
        for recipe_type, top_n_dict in results.items():
            display_summary(top_n_dict, recipe_type, SEASON_ORDER)
        
        # STEP 7: End message
        print("\n" + "="*70)
        print("[PROCESSING COMPLETED SUCCESSFULLY]")
        print("="*70)
        print("\n[MAIN ANALYSIS FILES]:")
        for recipe_type, filepath in saved_files.items():
            print(f"   • {recipe_type:10s}: {os.path.basename(filepath)}")

        print(f"\nMain results directory: {RESULTS_PATH}")
        print(f"Parameter justification: {JUSTIFICATION_PATH}")
        
        print("\n[SUMMARY]:")
        print(f"   • Seasonal distribution: {seasonal_results['total_reviews']:,} reviews analyzed")
        print("   • Top 20 recipes calculated for 3 types × 4 seasons = 12 analyses")
        print("   • Top 100 reviews analysis generated for parameter justification")
        print("   • Parameter distribution analysis completed")
        print(f"   • Combined justification file: {os.path.basename(reviews_analysis['files_created']['combined'])}")
        print(f"   • Seasonal distribution file: {os.path.basename(seasonal_results['filepath'])}")
        
    except (FileNotFoundError, pd.errors.EmptyDataError, KeyError, ValueError) as e:
        print(f"\n ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    """
    Script entry point. Executes the main function and returns the exit code.
    """
    exit_code = main()
    exit(exit_code)
