"""Tests for downloader helper functions without invoking network."""
from pathlib import Path
import cooking_assistant.data.downloader as dl
from cooking_assistant.data.downloader import has_any_timestamped_copy, main as downloader_main
import pandas as pd


def test_has_any_timestamped_copy(tmp_path, monkeypatch):
    # Point RAW_DIR to isolated tmp_path BEFORE calling helper
    monkeypatch.setattr(dl, 'RAW_DIR', tmp_path)
    assert not has_any_timestamped_copy('RAW_recipes')

    # Create timestamped file -> should be detected
    f = tmp_path / 'RAW_recipes_20240101-120000.csv'
    f.write_text('id,name\n1,Test')
    assert has_any_timestamped_copy('RAW_recipes')


def test_downloader_main_creates_files(tmp_path, monkeypatch, capsys):
    # Monkeypatch RAW_DIR
    monkeypatch.setattr(dl, 'RAW_DIR', tmp_path)
    # Fake kagglehub.load_dataset to return small DataFrame
    def fake_load_dataset(adapter, handle, fname):
        if 'recipes' in fname:
            return pd.DataFrame({'id':[1], 'name':['X']})
        return pd.DataFrame({'recipe_id':[1], 'rating':[5], 'date':['2024-03-21']})
    monkeypatch.setattr(dl.kagglehub, 'load_dataset', fake_load_dataset)
    # Ensure has_any_timestamped_copy returns False initially
    monkeypatch.setattr(dl, 'has_any_timestamped_copy', lambda stem: False)
    downloader_main()
    out = capsys.readouterr().out
    assert 'Saved ->' in out
    # Run again with skip path
    monkeypatch.setattr(dl, 'has_any_timestamped_copy', lambda stem: True)
    downloader_main()
    out2 = capsys.readouterr().out
    assert 'Already present, skip' in out2
