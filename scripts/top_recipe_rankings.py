"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          SCRIPT EXEMPLE : Calcul des Top 20 par Type et Saison              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Ce script montre comment utiliser les modules cooking_assistant pour :
1. Charger les données
2. Calculer les top 20 par type et saison
3. Sauvegarder les résultats

Remplace progressivement les anciens scripts monolithiques.
"""

import sys
from pathlib import Path

# Ajouter le projet au path si nécessaire
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
    """Point d'entrée principal du script."""
    
    print("=" * 80)
    print("CALCUL DES TOP 20 RECETTES PAR TYPE ET SAISON")
    print("=" * 80)
    
    # 1. Charger les données
    print("\n Étape 1 : Chargement des données")
    print("-" * 80)
    
    try:
        recipes_df = load_classified_recipes()
        interactions_df = load_interactions()
    except FileNotFoundError as e:
        print(f"\nErreur : {e}")
        print("\nConseil : Exécutez d'abord :")
        print("   1. python -m cooking_assistant.data.downloader")
        print("   2. python scripts/01_classifier_generator.py")
        return 1
    
    # 2. Préparer les données fusionnées
    print("\n🔧 Étape 2 : Préparation et fusion des données")
    print("-" * 80)
    
    merged_df = prepare_merged_data(recipes_df, interactions_df, verbose=True)
    
    # 3. Calculer les tops pour chaque type
    print("\nÉtape 3 : Calcul des rankings")
    print("-" * 70)
    
    all_results = {}
    
    for recipe_type in RECIPE_TYPES:
        print(f"\n{'=' * 80}")
        print(f"Type : {recipe_type.upper()}")
        print(f"{'=' * 80}")
        
        # Récupérer les paramètres bayésiens pour ce type
        params = BAYESIAN_PARAMS[recipe_type]
        
        print(f"\nParamètres bayésiens :")
        print(f"  • kb (régression)    : {params['kb']}")
        print(f"  • kpop (popularité)  : {params['kpop']}")
        print(f"  • gamma (amplif.)    : {params['gamma']}")
        
        # Calculer les tops
        tops_by_season = calculate_top_n_by_type(
            merged_df=merged_df,
            recipes_df=recipes_df,
            recipe_type=recipe_type,
            params=params,
            top_n=TOP_N,
            verbose=True
        )
        
        all_results[recipe_type] = tops_by_season
    
    # 4. Sauvegarder les 3 fichiers CSV finaux dans processed/
    print("\n" + "=" * 80)
    print("SAUVEGARDE DES FICHIERS CSV FINAUX")
    print("=" * 80)
    
    saved_files = save_combined_results_by_type(all_results)
    
    # 5. Résumé final
    print("\n" + "=" * 80)
    print("TRAITEMENT TERMINÉ")
    print("=" * 80)
    
    print(f"\nFichiers générés dans : {PROCESSED_DATA_DIR}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
