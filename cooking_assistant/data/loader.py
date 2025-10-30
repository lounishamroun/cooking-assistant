"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      CHARGEMENT DES DONNÉES CSV                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module pour charger les fichiers CSV (recettes, interactions, classifications).
Basé sur scripts/data_loader_preparation.py
"""

import pandas as pd
from pathlib import Path
from typing import Tuple

from ..config import (
    RAW_DATA_DIR,
    INTERIM_DATA_DIR,
    RAW_RECIPES_PREFIX,
    RAW_INTERACTIONS_PREFIX,
    RECIPES_CLASSIFIED_FILE,
    get_latest_file_with_prefix
)


def load_recipes(data_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """
    Charge le fichier de recettes brutes (RAW_recipes_*.csv).
    
    Args:
        data_dir: Répertoire contenant les données brutes
        
    Returns:
        DataFrame avec les recettes
        
    Raises:
        FileNotFoundError: Si aucun fichier de recettes n'est trouvé
    """
    recipes_file = get_latest_file_with_prefix(RAW_RECIPES_PREFIX, data_dir)
    
    print(f"📂 Chargement des recettes depuis : {recipes_file.name}")
    df = pd.read_csv(recipes_file, encoding='utf-8')
    print(f"   ✓ {len(df):,} recettes chargées")
    
    return df


def load_interactions(data_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """
    Charge le fichier d'interactions/reviews (RAW_interactions_*.csv).
    
    Args:
        data_dir: Répertoire contenant les données brutes
        
    Returns:
        DataFrame avec les interactions (reviews)
        
    Raises:
        FileNotFoundError: Si aucun fichier d'interactions n'est trouvé
    """
    interactions_file = get_latest_file_with_prefix(RAW_INTERACTIONS_PREFIX, data_dir)
    
    print(f"📂 Chargement des interactions depuis : {interactions_file.name}")
    df = pd.read_csv(interactions_file, encoding='utf-8')
    print(f"   ✓ {len(df):,} interactions chargées")
    
    return df


def load_classified_recipes(file_path: Path = RECIPES_CLASSIFIED_FILE) -> pd.DataFrame:
    """
    Charge le fichier de recettes classifiées (avec colonne 'type').
    
    Args:
        file_path: Chemin vers le fichier de recettes classifiées
        
    Returns:
        DataFrame avec les recettes classifiées
        
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Fichier de recettes classifiées introuvable : {file_path}\n"
            "Veuillez d'abord exécuter le script de classification (01_classifier_generator.py)"
        )
    
    print(f"📂 Chargement des recettes classifiées depuis : {file_path.name}")
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"   ✓ {len(df):,} recettes classifiées chargées")
    
    return df


def load_data(data_dir: Path = RAW_DATA_DIR) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Charge à la fois les recettes et les interactions.
    
    Args:
        data_dir: Répertoire contenant les données
        
    Returns:
        Tuple (recipes_df, interactions_df)
    """
    print("=" * 80)
    print("CHARGEMENT DES DONNÉES")
    print("=" * 80)
    
    recipes_df = load_recipes(data_dir)
    interactions_df = load_interactions(data_dir)
    
    print()
    return recipes_df, interactions_df


if __name__ == "__main__":
    # Test du chargement
    recipes, interactions = load_data()
    print(f"\nTest réussi!")
    print(f"   Recettes : {len(recipes)} lignes")
    print(f"   Interactions : {len(interactions)} lignes")
