"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      TÉLÉCHARGEMENT DES DONNÉES                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module pour télécharger les données depuis Kaggle.
Basé sur scripts/import_raw_data_from_source.py
"""

import logging
import shutil
from pathlib import Path
from datetime import datetime

import kagglehub
from kagglehub import KaggleDatasetAdapter

from ..config import (
    KAGGLE_DATASET_HANDLE,
    RAW_DATA_DIR,
    DOWNLOAD_LOG_FILE
)

# Configuration du logging
logging.basicConfig(
    filename=str(DOWNLOAD_LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def ensure_raw_data_once() -> None:
    """
    S'assure que les données brutes sont disponibles localement.
    
    Comportement :
    - Si data/raw existe et n'est pas vide :
        → Ne fait rien (skip le téléchargement)
    - Sinon :
        → Télécharge le dataset depuis Kaggle
        → Copie tous les fichiers dans data/raw avec un timestamp
        → Log ce qui a été sauvegardé
    
    Cette fonction est idempotente : après le premier succès,
    les appels futurs termineront immédiatement.
    """
    
    # Vérifier si les données existent déjà
    if RAW_DATA_DIR.exists() and any(RAW_DATA_DIR.iterdir()):
        print(f"✓ Données brutes déjà présentes dans {RAW_DATA_DIR}, skip du téléchargement.")
        logger.info("Données brutes déjà présentes dans %s, skip du téléchargement.", RAW_DATA_DIR)
        return
    
    print(f"📥 Téléchargement du dataset depuis Kaggle...")
    logger.info("Début du téléchargement du dataset '%s'", KAGGLE_DATASET_HANDLE)
    
    # Prévisualiser un fichier (optionnel)
    file_path = "RAW_recipes.csv"
    try:
        df = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            KAGGLE_DATASET_HANDLE,
            file_path,
        )
        print(f"✓ Prévisualisation de {file_path} : {len(df)} lignes")
        logger.info("Chargé %s via kagglehub.load_dataset()", file_path)
    except Exception as e:
        logger.warning("Échec de la prévisualisation de %s: %s", file_path, e)
    
    # Télécharger le dataset complet
    try:
        res = kagglehub.dataset_download(KAGGLE_DATASET_HANDLE)
        
        # Gérer les deux formats de retour possibles
        local_path = res[0] if isinstance(res, (tuple, list)) else res
        local_dir = Path(local_path)
        
        if not local_dir.exists():
            raise FileNotFoundError(f"Chemin téléchargé introuvable : {local_dir}")
        
        logger.info("Dataset '%s' téléchargé dans %s", KAGGLE_DATASET_HANDLE, local_dir)
        
    except Exception as e:
        logger.error("Échec du téléchargement du dataset '%s': %s", KAGGLE_DATASET_HANDLE, e)
        raise
    
    # Préparer le dossier de destination
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Identifier les fichiers sources
    if local_dir.is_file():
        src_files = [local_dir]
    else:
        src_files = [p for p in local_dir.iterdir() if p.is_file()]
    
    if not src_files:
        logger.warning("Aucun fichier trouvé à copier depuis %s", local_dir)
        print(f"⚠️  Aucun fichier trouvé dans {local_dir}")
        return
    
    # Copier chaque fichier avec timestamp
    print(f"\n📁 Copie des fichiers dans {RAW_DATA_DIR}...")
    for p in src_files:
        dst = RAW_DATA_DIR / f"{p.stem}_{timestamp}{p.suffix}"
        shutil.copy2(p, dst)
        print(f"   ✓ Sauvegardé : {dst.name}")
        logger.info("Sauvegardé : %s", dst)
    
    print(f"\n✅ Téléchargement terminé : {len(src_files)} fichier(s) copié(s)")
    logger.info("Téléchargement terminé : %d fichier(s)", len(src_files))


def download_raw_data() -> None:
    """
    Alias pour ensure_raw_data_once().
    Point d'entrée pour les scripts.
    """
    ensure_raw_data_once()


if __name__ == "__main__":
    # Permet d'exécuter ce module directement
    ensure_raw_data_once()
