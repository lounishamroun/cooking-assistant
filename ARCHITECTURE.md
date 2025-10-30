# 🍳 Cooking Assistant - Architecture Modulaire

## 📋 Vue d'ensemble

Projet de classification et d'analyse de recettes par type (plat, dessert, boisson) et par saison.

## 🏗️ Architecture du projet

```
cooking-assistant/
│
├── cooking_assistant/              # 📦 PACKAGE PRINCIPAL
│   ├── __init__.py
│   ├── config.py                   # ⚙️  Configuration centrale
│   │
│   ├── data/                       # 📂 Gestion des données
│   │   ├── __init__.py
│   │   ├── downloader.py           # Téléchargement depuis Kaggle
│   │   ├── loader.py               # Chargement des CSV
│   │   └── processor.py            # Fusion et prétraitement
│   │
│   ├── classification/             # 🏷️ Classification des recettes
│   │   └── __init__.py             # (À implémenter)
│   │
│   ├── analysis/                   # 📊 Analyse et ranking
│   │   ├── __init__.py
│   │   ├── seasonal.py             # Utilitaires saisonniers
│   │   ├── scoring.py              # Calcul scores bayésiens
│   │   └── reviews.py              # Analyse des tops par avis
│   │
│   └── utils/                      # 🛠️ Utilitaires
│       └── __init__.py
│
├── scripts/                        # 🚀 Scripts d'automatisation
│   ├── 01_classifier_generator.py  # Génère recettes classifiées
│   ├── config.py                   # (Ancien, sera déprécié)
│   ├── data_loader_preparation.py  # (Ancien, sera déprécié)
│   ├── season_utils.py             # (Ancien, sera déprécié)
│   ├── score_calculator.py         # (Ancien, sera déprécié)
│   └── top_reviews_analyzer.py     # (Ancien, sera déprécié)
│
├── data/                           # 💾 Données
│   ├── raw/                        # Données brutes (Kaggle)
│   ├── interim/                    # Données intermédiaires
│   │   └── recipes_classified.csv  # Recettes avec colonne 'type'
│   └── processed/                  # Données finales
│
├── resultats/                      # 📈 Résultats des rankings
├── reports/                        # 📊 Rapports et visualisations
├── docs/                           # 📚 Documentation
└── pyproject.toml                  # ⚙️  Configuration Poetry
```

## 🚀 Installation

```bash
# Installer les dépendances avec Poetry
poetry install

# Ou avec pip
pip install -e .
```

## 📖 Utilisation

### 1️⃣ Télécharger les données brutes

```python
from cooking_assistant.data import download_raw_data

# Télécharge depuis Kaggle si pas déjà fait
download_raw_data()
```

### 2️⃣ Charger et préparer les données

```python
from cooking_assistant.data import load_data, prepare_merged_data

# Charger recettes et interactions
recipes_df, interactions_df = load_data()

# Fusionner et ajouter les saisons
merged_df = prepare_merged_data(recipes_df, interactions_df)
```

### 3️⃣ Calculer les top 20 par type et saison

```python
from cooking_assistant.analysis import calculate_top_n_by_type
from cooking_assistant.config import BAYESIAN_PARAMS

# Calculer pour les plats
tops = calculate_top_n_by_type(
    merged_df=merged_df,
    recipes_df=recipes_df,
    recipe_type='plat',
    params=BAYESIAN_PARAMS['plat']
)

# Accéder au top 20 du printemps
spring_top20 = tops['Spring']
```

### 4️⃣ Analyser les tops par nombre d'avis

```python
from cooking_assistant.analysis import analyze_top_reviews_by_type_season

# Analyser les 100 recettes les plus commentées
results = analyze_top_reviews_by_type_season(
    merged_df=merged_df,
    recipes_df=recipes_df,
    top_n=100
)
```

## 🔧 Configuration

Toute la configuration est centralisée dans `cooking_assistant/config.py` :

- **Chemins** : `RAW_DATA_DIR`, `PROCESSED_DATA_DIR`, `RESULTS_DIR`
- **Types** : `RECIPE_TYPES = ["plat", "dessert", "boisson"]`
- **Saisons** : `SEASONS = ["Spring", "Summer", "Fall", "Winter"]`
- **Paramètres bayésiens** : `BAYESIAN_PARAMS`

## 📊 Paramètres Bayésiens

Les paramètres sont justifiés dans `docs/bayesian_parameters_docs_justification/`

| Type     | kb  | kpop | gamma | Description                    |
|----------|-----|------|-------|--------------------------------|
| Plat     | 65  | 45.0 | 1.2   | Équilibre qualité/popularité   |
| Dessert  | 60  | 40.0 | 1.2   | Plus d'avis en général         |
| Boisson  | 20  | 4.0  | 0.7   | Priorité à la qualité          |

## 🔄 Migration depuis l'ancienne architecture

Les anciens scripts dans `scripts/` utilisent maintenant le package `cooking_assistant` :

**Avant** :
```python
from scripts.config import PARAMS_PLATS
from scripts.data_loader_preparation import load_data
```

**Après** :
```python
from cooking_assistant.config import BAYESIAN_PARAMS
from cooking_assistant.data import load_data

params_plats = BAYESIAN_PARAMS['plat']
```

## 🧪 Tests

```bash
# Tester le chargement des données
python -m cooking_assistant.data.loader

# Tester le calcul des saisons
python -m cooking_assistant.analysis.seasonal
```

## 📝 Scripts principaux

### Script 1 : Classification (01_classifier_generator.py)

**Ce script reste complexe et nécessite une refactorisation future.**

Génère `recipes_classified.csv` avec la colonne `type`.

### Scripts futurs (à créer avec les modules)

```python
# scripts/02_calculate_rankings.py
from cooking_assistant.data import load_classified_recipes, load_interactions, prepare_merged_data
from cooking_assistant.analysis import calculate_top_n_by_type
from cooking_assistant.config import BAYESIAN_PARAMS, RECIPE_TYPES

def main():
    # Charger les données
    recipes = load_classified_recipes()
    interactions = load_interactions()
    merged = prepare_merged_data(recipes, interactions)
    
    # Calculer pour chaque type
    for recipe_type in RECIPE_TYPES:
        tops = calculate_top_n_by_type(
            merged, recipes, recipe_type,
            BAYESIAN_PARAMS[recipe_type]
        )
        # Sauvegarder les résultats...

if __name__ == "__main__":
    main()
```

## 🎯 Prochaines étapes

1. ✅ Architecture modulaire créée
2. ✅ Configuration centralisée
3. ✅ Modules data, analysis créés
4. ⏳ Refactoriser 01_classifier_generator.py
5. ⏳ Créer scripts simplifiés utilisant les modules
6. ⏳ Interface Streamlit
7. ⏳ Tests unitaires
8. ⏳ Documentation Sphinx

## 👥 Contributeurs

- Lounis Hamroun
- Alexandre Donnat
- Omar Fekih
- Leo Ivars

## 📄 Licence

*À définir*
