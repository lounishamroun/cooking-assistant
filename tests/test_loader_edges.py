import pandas as pd
import pytest
from pathlib import Path

# We test missing raw file handling by pointing loader helpers at a temp dir.

def test_load_recipes_missing(monkeypatch, tmp_path):
    from cooking_assistant.data import loader
    # Point RAW_DATA_DIR to empty tmp dir
    monkeypatch.setattr(loader, 'RAW_DATA_DIR', tmp_path)
    # Monkeypatch get_latest_file_with_prefix to raise FileNotFoundError like real behavior
    from cooking_assistant.config import get_latest_file_with_prefix
    monkeypatch.setattr(loader, 'get_latest_file_with_prefix', lambda prefix, directory: (_ for _ in ()).throw(FileNotFoundError('none')))
    with pytest.raises(FileNotFoundError):
        loader.load_recipes(tmp_path)


def test_load_classified_missing(monkeypatch, tmp_path):
    from cooking_assistant.data import loader
    missing = tmp_path / 'recipes_classified.csv'
    with pytest.raises(FileNotFoundError):
        loader.load_classified_recipes(missing)
