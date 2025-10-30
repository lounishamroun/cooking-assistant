"""
EXAMPLE SCRIPT: Calculate Top 20 by Type and Season

This script shows how to use cooking_assistant modules to:
1. Load data
2. Calculate top 20 by type and season
3. Save results

Progressively replaces old monolithic scripts.
"""

import sys
from pathlib import Path

# Add project to path if needed
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cooking_assistant.data import (
    load_classified_recipes,
    load_interactions,
    prepare_merged_data
)
from cooking_assistant.analysis import calculate_top_n_by_type
from cooking_assistant.utils.results import save_combined_results_by_type
from cooking_assistant.config import (
    BAYESIAN_PARAMS,
    RECIPE_TYPES,
    PROCESSED_DATA_DIR,
    TOP_N
)


def main():
    """Main entry point of the script."""
    
    print("=" * 80)
    print("CALCULATE TOP 20 RECIPES BY TYPE AND SEASON")
    print("=" * 80)
    
    # 1. Load data
    print("\n Step 1: Loading data")
    print("-" * 80)
    
    try:
        recipes_df = load_classified_recipes()
        interactions_df = load_interactions()
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nAdvice: Run first:")
        print("   1. python -m cooking_assistant.data.downloader")
        print("   2. python scripts/01_classifier_generator.py")
        return 1
    
    # 2. Prepare merged data
    print("\n🔧 Step 2: Data preparation and merging")
    print("-" * 80)
    
    merged_df = prepare_merged_data(recipes_df, interactions_df, verbose=True)
    
    # 3. Calculate tops for each type
    print("\nStep 3: Rankings calculation")
    print("-" * 70)
    
    all_results = {}
    
    for recipe_type in RECIPE_TYPES:
        print(f"\n{'=' * 80}")
        print(f"Type: {recipe_type.upper()}")
        print(f"{'=' * 80}")
        
        # Get Bayesian parameters for this type
        params = BAYESIAN_PARAMS[recipe_type]
        
        print(f"\nBayesian parameters:")
        print(f"  • kb (regression)    : {params['kb']}")
        print(f"  • kpop (popularity)  : {params['kpop']}")
        print(f"  • gamma (amplif.)    : {params['gamma']}")
        
        # Calculate tops
        tops_by_season = calculate_top_n_by_type(
            merged_df=merged_df,
            recipes_df=recipes_df,
            recipe_type=recipe_type,
            params=params,
            top_n=TOP_N,
            verbose=True
        )
        
        all_results[recipe_type] = tops_by_season
    
    # 4. Save the 3 final CSV files in processed/
    print("\n" + "=" * 80)
    print("SAVING FINAL CSV FILES")
    print("=" * 80)
    
    saved_files = save_combined_results_by_type(all_results)
    
    # 5. Final summary
    print("\n" + "=" * 80)
    print("PROCESSING COMPLETED")
    print("=" * 80)
    
    print(f"\nFiles generated in: {PROCESSED_DATA_DIR}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
