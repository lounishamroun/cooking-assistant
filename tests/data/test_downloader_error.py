"""Tests downloader error recovery path (DataCorruptionError)."""
from pathlib import Path
import pandas as pd
import cooking_assistant.data.downloader as dl
from kagglehub.exceptions import DataCorruptionError
import runpy


def test_downloader_error_recovery(tmp_path, monkeypatch, capsys):
    # Point RAW_DIR
    monkeypatch.setattr(dl, 'RAW_DIR', tmp_path)

    # Force load_dataset to raise DataCorruptionError
    def fake_load_dataset(adapter, handle, fname):
        raise DataCorruptionError('corrupted')
    monkeypatch.setattr(dl.kagglehub, 'load_dataset', fake_load_dataset)

    # Provide dataset_download returning directory containing required csv
    download_dir = tmp_path / 'kaggle_cache'
    download_dir.mkdir()
    # Create both files expected in FILES
    for fname in dl.FILES:
        (download_dir / fname).write_text('id,name\n1,X' if 'recipes' in fname else 'recipe_id,rating,date\n1,5,2024-03-21')
    def fake_dataset_download(handle, force_download=True):
        return [str(download_dir)]
    monkeypatch.setattr(dl.kagglehub, 'dataset_download', fake_dataset_download)

    # ensure has_any_timestamped_copy returns False initial
    monkeypatch.setattr(dl, 'has_any_timestamped_copy', lambda stem: False)

    dl.main()
    out = capsys.readouterr().out
    assert 'Cache corrupted.' in out or 'Cache corrupted' in out
    assert 'Saved ->' in out
