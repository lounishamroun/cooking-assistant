#!/usr/bin/env python3
"""
Script principal pour lancer l'analyse des paramètres bayésiens.
Lance seasonal.py et top_reviews_analyzer.py et sauvegarde dans results_to_analyse.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import analysis modules
from scripts.season_distribution import analyze_seasonal_distribution
from scripts.top_reviews_analyzer import analyze_top_reviews_by_type_season
from cooking_assistant.data.loader import load_classified_recipes
from cooking_assistant.data.processor import prepare_merged_data


def main():
    """
    Lance les 2 analyses et sauvegarde dans results_to_analyse.
    """
    print("ANALYSE PARAMÈTRES BAYÉSIENS")
    print("=" * 50)
    
    # Output directory
    from cooking_assistant.config import JUSTIFICATION_DIR
    output_dir = str(JUSTIFICATION_DIR)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Sortie: {output_dir}")
    
    try:
        # 1. Chargement des données
        print("\n1. Chargement des données...")
        
        # Try to load classified recipes first, if not available load RAW and classify
        try:
            recipes_df = load_classified_recipes()
            print(" Données classifiées trouvées")
        except FileNotFoundError:
            print(" Données classifiées non trouvées, chargement des données RAW...")
            from cooking_assistant.data.loader import load_data
            recipes_df, _ = load_data()
            
            # Basic classification for analysis (simplified version)
            print("   → Classification rapide des recettes...")
            from cooking_assistant.analysis.scoring import classify_recipe_type
            
            # Add basic type classification
            recipes_df['type'] = recipes_df.apply(classify_recipe_type, axis=1)
            print(f" {len(recipes_df):,} recettes classifiées automatiquement")
        
        from cooking_assistant.data.loader import load_interactions
        interactions_df = load_interactions()
        
        merged_df = prepare_merged_data(recipes_df, interactions_df)
        print(f"   {len(recipes_df):,} recettes")
        print(f"   {len(interactions_df):,} interactions")
        print(f"   {len(merged_df):,} interactions fusionnées")
        
        # 2. Analyse saisonnière
        print("\n2. Analyse distribution saisonnière...")
        seasonal_results = analyze_seasonal_distribution(merged_df)
        
        # Sauvegarde saisonnière (timestamp + alias latest)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        seasonal_filename = f"season_type_distribution_{timestamp}.csv"
        seasonal_output = os.path.join(output_dir, seasonal_filename)
        df_season = seasonal_results['dataframe']
        df_season.to_csv(seasonal_output, index=False)
        # Canonical alias for Streamlit loader
        seasonal_latest = os.path.join(output_dir, "season_type_distribution_latest.csv")
        try:
            df_season.to_csv(seasonal_latest, index=False)
        except Exception as alias_err:
            print(f"  Impossible d'écrire l'alias latest: {alias_err}")
        print(f"   Sauvegardé: {seasonal_filename} (+ alias season_type_distribution_latest.csv)")
        
        # 3. Analyse top reviews (seulement top_100; suppression des anciens fichiers plus petits)
        print("\n3. Analyse top reviews...")
        top_reviews_results = analyze_top_reviews_by_type_season(
            merged_df=merged_df,
            recipes_df=recipes_df,
            output_dir=output_dir,
            top_n=100
        )
        # Create canonical alias for most recent top_100 file
        try:
            latest_top_files = sorted([
                f for f in os.listdir(output_dir)
                if f.startswith("top_100_reviews_by_type_season_") and f.endswith('.csv')
            ])
            if latest_top_files:
                newest = latest_top_files[-1]
                src = os.path.join(output_dir, newest)
                alias = os.path.join(output_dir, "top_100_reviews_by_type_season_latest.csv")
                with open(src, 'rb') as r, open(alias, 'wb') as w:
                    w.write(r.read())
        except Exception as e_alias:
            print(f"   Impossible de créer alias top_100 latest: {e_alias}")
        print("   Sauvegardé: top_100_reviews_by_type_season_*.csv (+ alias top_100_reviews_by_type_season_latest.csv)")
        # Nettoyage des fichiers historiques top_3/top_5/top_10 (pollution du dépôt)
        keep_smaller_sets = os.getenv("KEEP_SMALLER_TOP_FILES", "0") == "1"
        if keep_smaller_sets:
            print("   KEEP_SMALLER_TOP_FILES=1 → conservation des anciens fichiers top_3/top_5/top_10")
        else:
            obsolete_prefixes = ["top_3_reviews_by_type_season_", "top_5_reviews_by_type_season_", "top_10_reviews_by_type_season_"]
            removed = 0
            for f in os.listdir(output_dir):
                if any(f.startswith(pfx) for pfx in obsolete_prefixes) and f.endswith('.csv'):
                    try:
                        os.remove(os.path.join(output_dir, f))
                        removed += 1
                    except Exception as rm_err:
                        print(f"   Impossible de supprimer {f}: {rm_err}")
            if removed:
                print(f"   Nettoyage: {removed} fichier(s) top_3/top_5/top_10 supprimé(s)")
            else:
                print("   Aucun fichier top_3/top_5/top_10 à supprimer")
        
        # 4. Résumé
        print("\nANALYSE TERMINÉE!")
        print("=" * 50)
        print("Fichiers générés:")
        
        csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
        for i, file in enumerate(csv_files, 1):
            file_path = os.path.join(output_dir, file)
            size = os.path.getsize(file_path)
            print(f"{i}. {file} ({size:,} bytes)")
        
        return True
        
    except Exception as e:
        print(f"\nErreur: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\nMission accomplie!")
        print("Astuce: définissez KEEP_SMALLER_TOP_FILES=1 avant l'exécution pour conserver les jeux réduits si vous en avez encore besoin.")
    else:
        print("\nÉchec de l'analyse.")
        sys.exit(1)