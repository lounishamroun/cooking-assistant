"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CONFIGURATION CENTRALE DU PROJET                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

Configuration unifiée pour le système de recommandation de recettes.
Contient tous les chemins, paramètres bayésiens, et constantes du projet.
"""

import os
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# CHEMINS DES RÉPERTOIRES
# ══════════════════════════════════════════════════════════════════════════════

# Répertoire racine du projet
ROOT_DIR = Path(__file__).parent.parent
BASE_DIR = ROOT_DIR

# Données
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Sorties et rapports
RESULTS_DIR = ROOT_DIR / "resultats"
REPORTS_DIR = ROOT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# Documentation
JUSTIFICATION_DIR = ROOT_DIR / "docs" / "bayesian_parameters_docs_justification"

# Logs
LOGS_DIR = ROOT_DIR / "logs"

# Créer les dossiers s'ils n'existent pas
for directory in [RESULTS_DIR, REPORTS_DIR, FIGURES_DIR, JUSTIFICATION_DIR, LOGS_DIR,
                  RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# FICHIERS PRINCIPAUX
# ══════════════════════════════════════════════════════════════════════════════

# Kaggle dataset handle
KAGGLE_DATASET_HANDLE = "shuyangli94/food-com-recipes-and-user-interactions"

# Fichiers d'entrée (les noms seront trouvés dynamiquement avec timestamp)
RAW_RECIPES_PREFIX = "RAW_recipes"
RAW_INTERACTIONS_PREFIX = "RAW_interactions"

# Fichiers de sortie
RECIPES_CLASSIFIED_FILE = INTERIM_DATA_DIR / "recipes_classified.csv"
DOWNLOAD_LOG_FILE = LOGS_DIR / "data_set_download.log"


# ══════════════════════════════════════════════════════════════════════════════
# TYPES DE RECETTES ET SAISONS
# ══════════════════════════════════════════════════════════════════════════════

# Types de recettes reconnus
RECIPE_TYPES = ["plat", "dessert", "boisson"]

# Saisons (ordre d'affichage)
SEASONS = ["Spring", "Summer", "Fall", "Winter"]
SEASON_ORDER = SEASONS  # Alias pour compatibilité

# Mapping français <-> anglais pour les saisons
SEASON_FR_TO_EN = {
    "Printemps": "Spring",
    "Été": "Summer",
    "Automne": "Fall",
    "Hiver": "Winter"
}

SEASON_EN_TO_FR = {v: k for k, v in SEASON_FR_TO_EN.items()}


# ══════════════════════════════════════════════════════════════════════════════
# PARAMÈTRES BAYÉSIENS PAR TYPE DE RECETTE
# ══════════════════════════════════════════════════════════════════════════════

# Les paramètres sont justifiés dans docs/bayesian_parameters_docs_justification/

# Paramètres pour les PLATS
PARAMS_PLATS = {
    'kb': 65,           # Nombre de "pseudo-avis" pour la régression bayésienne
    'kpop': 45.0,       # Seuil de popularité (avis nécessaires pour 63% du poids max)
    'gamma': 1.2        # Facteur d'amplification de la popularité
}

# Paramètres pour les DESSERTS
PARAMS_DESSERTS = {
    'kb': 60,           # Plus élevé = plus conservateur (tire vers la moyenne)
    'kpop': 40.0,       # Les desserts ont généralement plus d'avis
    'gamma': 1.2        # Amplification modérée
}

# Paramètres pour les BOISSONS
PARAMS_BOISSONS = {
    'kb': 20,           # Bas = fait plus confiance aux notes réelles
    'kpop': 4.0,        # Les boissons ont moins d'avis
    'gamma': 0.7        # Faible amplification (priorité à la qualité)
}

# Dictionnaire de mapping pour accès facile
BAYESIAN_PARAMS = {
    'plat': PARAMS_PLATS,
    'dessert': PARAMS_DESSERTS,
    'boisson': PARAMS_BOISSONS
}


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES D'ANALYSE
# ══════════════════════════════════════════════════════════════════════════════

# Nombre de recettes dans le top
TOP_N = 20

# Nombre de recettes pour l'analyse de popularité
TOP_REVIEWS_ANALYSIS_N = 100

# Seuil epsilon pour éviter la division par zéro
EPSILON = 1e-6


# ══════════════════════════════════════════════════════════════════════════════
# PARAMÈTRES DE CLASSIFICATION
# ══════════════════════════════════════════════════════════════════════════════

# Priors pour la classification (plat, dessert, boisson)
CLASSIFICATION_PRIORS = [0.50, 0.35, 0.15]

# Classes de classification
CLASSIFICATION_CLASSES = ["plat", "dessert", "boisson"]

# Prototypes pour la classification par nutrition
NUTRITIONAL_PROTOTYPES = {
    'dessert':  {'sweet': 0.68, 'savory': 0.07, 'lean': 0.40},
    'plat':     {'sweet': 0.12, 'savory': 0.28, 'lean': 0.45},
    'boisson':  {'sweet': 0.09, 'savory': 0.05, 'lean': 0.85},
}

# Probabilités canoniques pour les exceptions
CANONICAL_PROBABILITIES = {
    'plat':    [0.86, 0.09, 0.05],
    'dessert': [0.10, 0.84, 0.06],
    'boisson': [0.06, 0.10, 0.84],
}


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DE L'APPLICATION STREAMLIT
# ══════════════════════════════════════════════════════════════════════════════

APP_TITLE = "🍳 Cooking Assistant"
APP_SUBTITLE = "Découvrez les meilleures recettes par type et par saison"
APP_ICON = "🍳"
APP_LAYOUT = "wide"


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS POUR LES CHEMINS
# ══════════════════════════════════════════════════════════════════════════════

def get_latest_file_with_prefix(prefix: str, directory: Path = RAW_DATA_DIR) -> Path:
    """
    Trouve le fichier CSV le plus récent avec un préfixe donné.
    
    Args:
        prefix: Préfixe du fichier (ex: "RAW_recipes")
        directory: Répertoire où chercher
        
    Returns:
        Path vers le fichier le plus récent
        
    Raises:
        FileNotFoundError: Si aucun fichier n'est trouvé
    """
    # Chercher avec timestamp
    candidates = sorted(directory.glob(f"{prefix}_*.csv"))
    
    # Chercher sans timestamp si aucun fichier trouvé
    if not candidates:
        candidates = sorted(directory.glob(f"{prefix}.csv"))
    
    if not candidates:
        raise FileNotFoundError(
            f"Aucun fichier CSV commençant par '{prefix}' trouvé dans {directory}"
        )
    
    # Retourner le plus récent (ordre alphabétique avec timestamp)
    return max(candidates, key=lambda p: p.name)


# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION DE LA CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

def validate_config():
    """Valide que la configuration est correcte."""
    errors = []
    
    # Vérifier que les types de recettes correspondent aux paramètres
    if set(RECIPE_TYPES) != set(BAYESIAN_PARAMS.keys()):
        errors.append("Les RECIPE_TYPES ne correspondent pas aux clés de BAYESIAN_PARAMS")
    
    # Vérifier que les classes de classification correspondent
    if set(RECIPE_TYPES) != set(CLASSIFICATION_CLASSES):
        errors.append("Les RECIPE_TYPES ne correspondent pas aux CLASSIFICATION_CLASSES")
    
    if errors:
        raise ValueError("Erreurs de configuration:\n" + "\n".join(f"  - {e}" for e in errors))


# Valider au chargement du module
validate_config()
