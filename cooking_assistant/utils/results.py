"""Results persistence and console summaries.

Utilities to serialize top-N seasonal ranking tables and produce readable
terminal summaries. All functions operate on DataFrames already scored by
the analysis module.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from ..config import RESULTS_DIR, SEASON_ORDER


def save_top_results(
    top_n_dict: Dict[str, pd.DataFrame],
    recipe_type: str,
    results_path: Path = RESULTS_DIR,
    top_n: int = 20
) -> Path:
    """Persist a combined CSV of seasonal top-N rows for one recipe type.

    Parameters
    ----------
    top_n_dict : Dict[str, pd.DataFrame]
        Mapping season → ranked DataFrame.
    recipe_type : str
        Category label (``plat``, ``dessert``, ``boisson``).
    results_path : Path, default ``RESULTS_DIR``
        Destination directory (created if missing).
    top_n : int, default 20
        Number included per season (used only for filename convention).

    Returns
    -------
    Path
        Location of the saved CSV.
    """
    print(f"\nSaving results - {recipe_type}...")
    
    # Combine all top N into a single DataFrame
    all_top_n = pd.concat(top_n_dict.values(), ignore_index=True)
    
    # Reorganize columns for clarity
    columns_order = [
        'Saison', 'recipe_id', 'name', 'reviews_in_season', 
        'avg_rating', 'Q_Score_Bayesien', 
        'Poids_Popularite', 'Score_Final'
    ]
    
    # Ensure all columns exist
    available_cols = [col for col in columns_order if col in all_top_n.columns]
    all_top_n = all_top_n[available_cols]
    
    # Rename for clarity
    all_top_n = all_top_n.rename(columns={
        'reviews_in_season': 'Nb_Reviews_Season',
        'avg_rating': 'Note_Moyenne'
    })
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"top_{top_n}_{recipe_type}_by_season_{timestamp}.csv"
    filepath = results_path / filename
    
    # Create folder if necessary
    results_path.mkdir(parents=True, exist_ok=True)
    
    # Save
    all_top_n.to_csv(filepath, index=False, encoding='utf-8')
    print(f" File saved: {filename}")
    print(f" Location: {results_path}")
    
    return filepath


def display_top_summary(
    top_n_dict: Dict[str, pd.DataFrame],
    recipe_type: str,
    season_order: List[str] = SEASON_ORDER,
    show_top: int = 5
) -> None:
    """Print a concise console summary of top scored recipes per season.

    Parameters
    ----------
    top_n_dict : Dict[str, pd.DataFrame]
        Mapping season → ranked DataFrame.
    recipe_type : str
        Category label for heading display.
    season_order : List[str], default ``SEASON_ORDER``
        Order in which seasons are displayed.
    show_top : int, default 5
        Number of rows printed for each season.
    """
    print(f"\n{'=' * 80}")
    print(f"TOP {show_top} RECIPES BY SEASON - {recipe_type.upper()}")
    print(f"{'=' * 80}\n")
    
    for season in season_order:
        if season not in top_n_dict:
            continue
        
        top_n = top_n_dict[season]
        
        print(f"{season.upper()}")
        print("-" * 80)
        
        # Display top N
        for idx, row in top_n.head(show_top).iterrows():
            rank = idx + 1 if isinstance(idx, int) else len(top_n[:idx]) + 1
            recipe_name = str(row['name'])[:50]
            score = row['Score_Final']
            rating = row.get('avg_rating', row.get('Note_Moyenne', 0))
            
            print(f"   {rank:2d}. {recipe_name:50s} "
                  f"Score: {score:.4f} "
                  f"(Rating: {rating:.2f}/5)")
        
        if len(top_n) > show_top:
            print(f"   ... and {len(top_n) - show_top} other recipes")
        
        print()


def save_all_type_results(
    all_results: Dict[str, Dict[str, pd.DataFrame]],
    results_path: Path = RESULTS_DIR,
    top_n: int = 20
) -> Dict[str, Path]:
    """Persist combined top-N CSV for each recipe type.

    Parameters
    ----------
    all_results : Dict[str, Dict[str, pd.DataFrame]]
        Mapping recipe_type → (season → DataFrame).
    results_path : Path, default ``RESULTS_DIR``
        Destination directory.
    top_n : int, default 20
        Number included per season (for filename purpose only).

    Returns
    -------
    Dict[str, Path]
        Mapping recipe_type → saved CSV path.
    """
    saved_files = {}
    
    for recipe_type, tops_by_season in all_results.items():
        filepath = save_top_results(
            tops_by_season,
            recipe_type,
            results_path,
            top_n
        )
        saved_files[recipe_type] = filepath
    
    return saved_files


def save_combined_results_by_type(
    all_results: Dict[str, Dict[str, pd.DataFrame]],
    results_path: Path = None
) -> Dict[str, Path]:
    """Create one CSV per recipe type aggregating all seasonal top lists.

    Parameters
    ----------
    all_results : Dict[str, Dict[str, pd.DataFrame]]
        Mapping recipe_type → (season → DataFrame) already scored and ranked.
    results_path : Path, optional
        Destination directory; defaults to ``PROCESSED_DATA_DIR`` when ``None``.

    Returns
    -------
    Dict[str, Path]
        Mapping recipe_type → saved aggregated CSV path.
    """
    from ..config import PROCESSED_DATA_DIR, SEASONS, TOP_N
    
    if results_path is None:
        results_path = PROCESSED_DATA_DIR
    
    results_path.mkdir(parents=True, exist_ok=True)
    saved_files = {}
    
    print(f"\nSaving final CSV files to {results_path}")
    print("=" * 80)
    
    for recipe_type, seasons_data in all_results.items():
        print(f"\n Processing: {recipe_type.upper()}")
        
        combined_data = []
        
        # Combine all seasons for this type
        for season in SEASONS:
            if season in seasons_data and not seasons_data[season].empty:
                season_df = seasons_data[season].copy()
                season_df['season'] = season
                season_df['rank_in_season'] = range(1, len(season_df) + 1)
                combined_data.append(season_df)
                print(f"   ✓ {season:10s} : {len(season_df)} recipes")
        
        if combined_data:
            # Combine all DataFrames
            final_df = pd.concat(combined_data, ignore_index=True)
            
            # Select and reorganize columns according to specifications
            # We harmonize naming to ensure downstream (Streamlit) robustness.
            # Preferred final columns: ranking, recipe_id, name, Q_Score_Bayesien, Pop_Weight, Final_Score, reviews_in_season, Saison
            if 'Q_Score_Bayesien_Poids_popularité' in final_df.columns:
                # Legacy combined score column name; create Final_Score
                final_df['Final_Score'] = final_df['Q_Score_Bayesien_Poids_popularité']
            elif 'Score_Final' in final_df.columns:
                final_df['Final_Score'] = final_df['Score_Final']
            elif 'Q_Score_Bayesien' in final_df.columns and 'Poids_Popularite' in final_df.columns:
                # Compute combined score if only components exist
                final_df['Final_Score'] = final_df['Q_Score_Bayesien'] * final_df['Poids_Popularite']

            # Popularity weight rename
            if 'Poids_Popularite' in final_df.columns and 'Pop_Weight' not in final_df.columns:
                final_df['Pop_Weight'] = final_df['Poids_Popularite']
            
            # Select only the requested columns in specified order
            columns_wanted = [
                'rank_in_season',           # → ranking 
                'recipe_id',                # → recipe_id
                'name',                     # → name
                'Q_Score_Bayesien',         # → Q_Score_Bayesien (individual quality score)
                'Pop_Weight',               # → Pop_Weight (popularity weight)
                'Final_Score',              # → Final_Score (combined score)
                'reviews_in_season',        # → reviews_in_season
                'season'                    # → Saison
            ]
            
            # Rename columns to final names
            column_renames = {
                'rank_in_season': 'ranking',
                'season': 'Saison'
            }
            
            # Check that all columns exist
            available_columns = [col for col in columns_wanted if col in final_df.columns]
            final_df = final_df[available_columns]
            
            # Rename columns
            final_df = final_df.rename(columns=column_renames)
            
            # Save
            filename = f"top{TOP_N}_{recipe_type}_for_each_season.csv"
            output_path = results_path / filename
            
            final_df.to_csv(output_path, index=False, encoding='utf-8')
            saved_files[recipe_type] = output_path
            
            print(f"   Saved: {filename}")
            print(f"      {len(final_df)} total recipes")
            print(f"      🌍 {len(combined_data)} seasons")
            
        else:
            print(f"   No data for {recipe_type}")
    
    return saved_files


if __name__ == "__main__":
    print("Results management module")
    print("Use this module via scripts or API")
