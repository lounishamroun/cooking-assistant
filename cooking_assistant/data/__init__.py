"""Module de données pour le package cooking_assistant."""

from .downloader import download_raw_data, ensure_raw_data_once
from .loader import load_recipes, load_interactions, load_classified_recipes
from .processor import prepare_merged_data

__all__ = [
    'download_raw_data',
    'ensure_raw_data_once',
    'load_recipes',
    'load_interactions',
    'load_classified_recipes',
    'prepare_merged_data',
]
