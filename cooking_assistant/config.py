"""Central configuration module.

Defines canonical paths, recipe type lists, season ordering, Bayesian
parameter sets per type, and small helpers such as
``get_latest_file_with_prefix`` plus a ``validate_config`` sanity check.
All paths are resolved relative to the package root enabling portable
execution inside or outside containers.
"""

import os
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# DIRECTORY PATHS
# ══════════════════════════════════════════════════════════════════════════════

# Project root directory
ROOT_DIR = Path(__file__).parent.parent

# Data directories
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Output and reports
RESULTS_DIR = PROCESSED_DATA_DIR  # Use standard data/processed directory
RESULTS_PROCESSED_DIR = PROCESSED_DATA_DIR  # Same as above for compatibility
REPORTS_DIR = ROOT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# Analysis and justification
JUSTIFICATION_DIR = ROOT_DIR / "analysis_parameter_justification" / "results_to_analyse"

# Logs
LOGS_DIR = ROOT_DIR / "logs"

# Create directories if they don't exist
for directory in [RESULTS_DIR, RESULTS_PROCESSED_DIR, REPORTS_DIR, FIGURES_DIR, JUSTIFICATION_DIR, LOGS_DIR,
                  RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN FILES
# ══════════════════════════════════════════════════════════════════════════════

# Kaggle dataset handle
KAGGLE_DATASET_HANDLE = "shuyangli94/food-com-recipes-and-user-interactions"

# Input files (names will be found dynamically with timestamp)
RAW_RECIPES_PREFIX = "RAW_recipes"
RAW_INTERACTIONS_PREFIX = "RAW_interactions"

# Output files
RECIPES_CLASSIFIED_FILE = INTERIM_DATA_DIR / "recipes_classified.csv"
DOWNLOAD_LOG_FILE = LOGS_DIR / "data_set_download.log"


# ══════════════════════════════════════════════════════════════════════════════
# RECIPE TYPES AND SEASONS
# ══════════════════════════════════════════════════════════════════════════════

# Recognized recipe types
RECIPE_TYPES = ["plat", "dessert", "boisson"]

# Seasons (display order)
SEASONS = ["Spring", "Summer", "Fall", "Winter"]
SEASON_ORDER = SEASONS  # Alias for compatibility


# ══════════════════════════════════════════════════════════════════════════════
# BAYESIAN PARAMETERS BY RECIPE TYPE
# ══════════════════════════════════════════════════════════════════════════════

# Parameters are justified in docs/bayesian_parameters_docs_justification/

# Parameters for PLATS (main dishes)
PARAMS_PLATS = {
    'kb': 65,           # Number of "pseudo-reviews" for Bayesian regression
    'kpop': 47.0,       # Popularity threshold (reviews needed for 63% of max weight)
    'gamma': 1.2        # Popularity amplification factor
}

# Parameters for DESSERTS
PARAMS_DESSERTS = {
    'kb': 60,           # Higher = more conservative (pulls toward mean)
    'kpop': 40.0,       # Desserts generally have more reviews
    'gamma': 1.2        # Moderate amplification
}

# Parameters for BOISSONS (drinks)
PARAMS_BOISSONS = {
    'kb': 20,           # Low = trusts actual ratings more
    'kpop': 4.0,        # Drinks have fewer reviews
    'gamma': 0.7        # Low amplification (quality priority)
}

# Mapping dictionary for easy access
BAYESIAN_PARAMS = {
    'plat': PARAMS_PLATS,
    'dessert': PARAMS_DESSERTS,
    'boisson': PARAMS_BOISSONS
}


# ══════════════════════════════════════════════════════════════════════════════
# ANALYSIS CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

# Number of recipes in the top ranking, you can adapt this rank as needed 
TOP_N = 20

# Number of recipes for popularity analysis
TOP_REVIEWS_ANALYSIS_N = 100

# Epsilon threshold to avoid division by zero
EPSILON = 1e-6


# ══════════════════════════════════════════════════════════════════════════════
# PATH HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def get_latest_file_with_prefix(prefix: str, directory: Path = RAW_DATA_DIR) -> Path:
    """
    Finds the most recent CSV file with a given prefix.
    
    Args:
        prefix: File prefix (e.g., "RAW_recipes")
        directory: Directory to search in
        
    Returns:
        Path to the most recent file
        
    Raises:
        FileNotFoundError: If no file is found
    """
    # Search with timestamp
    candidates = sorted(directory.glob(f"{prefix}_*.csv"))
    
    # Search without timestamp if no file found
    if not candidates:
        candidates = sorted(directory.glob(f"{prefix}.csv"))
    
    if not candidates:
        raise FileNotFoundError(
            f"No CSV file starting with '{prefix}' found in {directory}"
        )
    
    # Return the most recent (alphabetical order with timestamp)
    return max(candidates, key=lambda p: p.name)


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def validate_config():
    """Validates that the configuration is correct."""
    errors = []
    
    # Check that recipe types match parameters
    if set(RECIPE_TYPES) != set(BAYESIAN_PARAMS.keys()):
        errors.append("RECIPE_TYPES don't match BAYESIAN_PARAMS keys")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))


# Validate on module loading
validate_config()
