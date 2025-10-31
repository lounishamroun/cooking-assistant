"""Tests for seasonal utility get_season_from_date."""
import pandas as pd
from datetime import datetime
from cooking_assistant.analysis.seasonal import get_season_from_date


def test_get_season_from_date_basic_mapping_boundaries():
    # Boundary days according to implementation: Spring starts Mar 21, Winter until Mar 20
    assert get_season_from_date(datetime(2024, 3, 20)) == 'Winter'
    assert get_season_from_date(datetime(2024, 3, 21)) == 'Spring'
    assert get_season_from_date(datetime(2024, 6, 20)) == 'Spring'
    assert get_season_from_date(datetime(2024, 6, 21)) == 'Summer'
    assert get_season_from_date(datetime(2024, 9, 20)) == 'Summer'
    assert get_season_from_date(datetime(2024, 9, 21)) == 'Fall'
    assert get_season_from_date(datetime(2024, 12, 20)) == 'Fall'
    assert get_season_from_date(datetime(2024, 12, 21)) == 'Winter'


def test_get_season_from_date_invalid():
    assert get_season_from_date(None) == 'Unknown'
