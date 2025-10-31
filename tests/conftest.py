"""Pytest shared fixtures for cooking-assistant.

Fixtures create small synthetic DataFrames to keep tests fast and deterministic.
"""
from __future__ import annotations

import pandas as pd
import pytest
from datetime import datetime

from cooking_assistant.config import BAYESIAN_PARAMS

@pytest.fixture(scope="session")
def recipes_df() -> pd.DataFrame:
    """Synthetic recipes with pre-classified types."""
    return pd.DataFrame([
        {"id": 1, "name": "Salade de Printemps", "type": "plat"},
        {"id": 2, "name": "Mousse au Chocolat", "type": "dessert"},
        {"id": 3, "name": "Thé Glacé", "type": "boisson"},
        {"id": 4, "name": "Soupe d'Hiver", "type": "plat"},
    ])

@pytest.fixture(scope="session")
def interactions_df() -> pd.DataFrame:
    """Synthetic interactions spanning seasons with varied ratings (0 means no rating)."""
    base = [
        # Spring interactions for recipe 1 & 2
        {"recipe_id": 1, "rating": 5, "date": "2024-03-10"},
        {"recipe_id": 1, "rating": 4, "date": "2024-04-01"},
        {"recipe_id": 2, "rating": 0, "date": "2024-03-12"},
        {"recipe_id": 2, "rating": 5, "date": "2024-04-15"},
        # Summer interactions for recipe 3
        {"recipe_id": 3, "rating": 4, "date": "2024-07-02"},
        {"recipe_id": 3, "rating": 0, "date": "2024-08-11"},
        # Fall interactions for recipe 1
        {"recipe_id": 1, "rating": 3, "date": "2024-10-05"},
        # Winter interactions for recipe 4
        {"recipe_id": 4, "rating": 5, "date": "2024-12-01"},
        {"recipe_id": 4, "rating": 4, "date": "2024-12-20"},
        {"recipe_id": 4, "rating": 0, "date": "2024-12-25"},
    ]
    return pd.DataFrame(base)

@pytest.fixture(scope="session")
def params_plat() -> dict:
    return BAYESIAN_PARAMS["plat"]

@pytest.fixture(scope="session")
def params_dessert() -> dict:
    return BAYESIAN_PARAMS["dessert"]

@pytest.fixture(scope="session")
def params_boisson() -> dict:
    return BAYESIAN_PARAMS["boisson"]

@pytest.fixture(scope="session")
def merged_df(recipes_df, interactions_df) -> pd.DataFrame:
    """Produce merged DataFrame using the preprocessing function to ensure season labels."""
    from cooking_assistant.data.processor import prepare_merged_data
    return prepare_merged_data(recipes_df, interactions_df, verbose=False)

@pytest.fixture(scope="session")
def spring_plat_df(merged_df) -> pd.DataFrame:
    return merged_df[(merged_df["type"] == "plat") & (merged_df["season"] == "Spring")]

@pytest.fixture(scope="function")
def tmp_results_dir(tmp_path):
    d = tmp_path / "results"
    d.mkdir()
    return d
