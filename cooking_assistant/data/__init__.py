"""Module de données pour le package cooking_assistant."""

from .loader import load_recipes, load_interactions, load_classified_recipes
from .processor import prepare_merged_data

__all__ = [
    'load_recipes',
    'load_interactions',
    'load_classified_recipes',
    'prepare_merged_data',
]
