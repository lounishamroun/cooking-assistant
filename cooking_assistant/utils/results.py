"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                       GESTION DES RÉSULTATS                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module pour sauvegarder et afficher les résultats d'analyse.
Basé sur scripts/results_handler.py
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
    """
    Sauvegarde les résultats du top N dans un fichier CSV.
    
    Args:
        top_n_dict: Dictionnaire {saison: DataFrame} avec les tops N
        recipe_type: Type de recette (plat, dessert, boisson)
        results_path: Chemin du dossier de sortie
        top_n: Nombre de recettes dans le top
        
    Returns:
        Path du fichier sauvegardé
    """
    print(f"\n💾 Sauvegarde des résultats - {recipe_type}...")
    
    # Combiner tous les tops N en un seul DataFrame
    all_top_n = pd.concat(top_n_dict.values(), ignore_index=True)
    
    # Réorganiser les colonnes pour plus de clarté
    columns_order = [
        'Saison', 'recipe_id', 'name', 'reviews_in_season', 
        'avg_rating', 'Q_Score_Bayesien', 
        'Poids_Popularite', 'Score_Final'
    ]
    
    # S'assurer que toutes les colonnes existent
    available_cols = [col for col in columns_order if col in all_top_n.columns]
    all_top_n = all_top_n[available_cols]
    
    # Renommer pour plus de clarté
    all_top_n = all_top_n.rename(columns={
        'reviews_in_season': 'Nb_Reviews_Season',
        'avg_rating': 'Note_Moyenne'
    })
    
    # Générer le timestamp pour le nom de fichier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"top_{top_n}_{recipe_type}_par_saison_{timestamp}.csv"
    filepath = results_path / filename
    
    # Créer le dossier si nécessaire
    results_path.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder
    all_top_n.to_csv(filepath, index=False, encoding='utf-8')
    print(f"   ✓ Fichier sauvegardé : {filename}")
    print(f"   📁 Emplacement : {results_path}")
    
    return filepath


def display_top_summary(
    top_n_dict: Dict[str, pd.DataFrame],
    recipe_type: str,
    season_order: List[str] = SEASON_ORDER,
    show_top: int = 5
) -> None:
    """
    Affiche un résumé des meilleures recettes pour chaque saison.
    
    Args:
        top_n_dict: Dictionnaire {saison: DataFrame}
        recipe_type: Type de recette (pour l'affichage)
        season_order: Liste des saisons dans l'ordre
        show_top: Nombre de recettes à afficher par saison
    """
    print(f"\n{'=' * 80}")
    print(f"TOP {show_top} RECETTES PAR SAISON - {recipe_type.upper()}")
    print(f"{'=' * 80}\n")
    
    for season in season_order:
        if season not in top_n_dict:
            continue
        
        top_n = top_n_dict[season]
        
        print(f"🌸 {season.upper()}")
        print("-" * 80)
        
        # Afficher le top N
        for idx, row in top_n.head(show_top).iterrows():
            rank = idx + 1 if isinstance(idx, int) else len(top_n[:idx]) + 1
            recipe_name = str(row['name'])[:50]
            score = row['Score_Final']
            rating = row.get('avg_rating', row.get('Note_Moyenne', 0))
            
            print(f"   {rank:2d}. {recipe_name:50s} "
                  f"Score: {score:.4f} "
                  f"(Note: {rating:.2f}/5)")
        
        if len(top_n) > show_top:
            print(f"   ... et {len(top_n) - show_top} autres recettes")
        
        print()


def save_all_type_results(
    all_results: Dict[str, Dict[str, pd.DataFrame]],
    results_path: Path = RESULTS_DIR,
    top_n: int = 20
) -> Dict[str, Path]:
    """
    Sauvegarde les résultats pour tous les types de recettes.
    
    Args:
        all_results: Dict {type: {saison: DataFrame}}
        results_path: Chemin du dossier de sortie
        top_n: Nombre de recettes dans le top
        
    Returns:
        Dictionnaire {type: filepath} des fichiers sauvegardés
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


if __name__ == "__main__":
    print("Module de gestion des résultats")
    print("Utilisez ce module via les scripts ou l'API")
