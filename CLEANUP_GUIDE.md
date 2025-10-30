# 🧹 Guide de nettoyage des scripts

## 📊 État actuel des fichiers `scripts/`

### ✅ **Fichiers à GARDER**

| Fichier | Raison | Action |
|---------|--------|--------|
| `01_classifier_generator.py` | Script de classification complexe (575 lignes) | **Garder tel quel** - Refactorisation future |
| `example_calculate_rankings.py` | Nouveau script utilisant les modules | **Garder** - Exemple de bonne pratique |
| `analyze_seasonal_distribution.py` | Nouveau script pour distribution saisonnière | **Garder** - Remplace `season_distribution.py` |
| `__init__.py` | Nécessaire pour imports Python | **Garder** |

### ⚠️ **Fichiers DÉPRÉCIÉS** (logique intégrée dans `cooking_assistant/`)

| Fichier ancien | Remplacé par | Action recommandée |
|----------------|--------------|-------------------|
| `config.py` | `cooking_assistant/config.py` | 🗑️ Déplacer vers `deprecated/` |
| `data_loader_preparation.py` | `cooking_assistant/data/loader.py` + `processor.py` | 🗑️ Déplacer vers `deprecated/` |
| `import_raw_data_from_source.py` | `cooking_assistant/data/downloader.py` | 🗑️ Déplacer vers `deprecated/` |
| `season_utils.py` | `cooking_assistant/analysis/seasonal.py` | 🗑️ Déplacer vers `deprecated/` |
| `score_calculator.py` | `cooking_assistant/analysis/scoring.py` | 🗑️ Déplacer vers `deprecated/` |
| `top_reviews_analyzer.py` | `cooking_assistant/analysis/reviews.py` | 🗑️ Déplacer vers `deprecated/` |
| `results_handler.py` | `cooking_assistant/utils/results.py` | 🗑️ Déplacer vers `deprecated/` |
| `season_distribution.py` | `scripts/analyze_seasonal_distribution.py` | 🗑️ Déplacer vers `deprecated/` |

## 🚀 Plan de nettoyage

### Option 1 : Déplacement vers `deprecated/` (Recommandé)

```bash
# Créer le dossier deprecated
mkdir -p scripts/deprecated

# Déplacer les anciens fichiers
mv scripts/config.py scripts/deprecated/
mv scripts/data_loader_preparation.py scripts/deprecated/
mv scripts/import_raw_data_from_source.py scripts/deprecated/
mv scripts/season_utils.py scripts/deprecated/
mv scripts/score_calculator.py scripts/deprecated/
mv scripts/top_reviews_analyzer.py scripts/deprecated/
mv scripts/results_handler.py scripts/deprecated/
mv scripts/season_distribution.py scripts/deprecated/

# Créer un README dans deprecated
cat > scripts/deprecated/README.md << 'EOF'
# Scripts dépréciés

Ces scripts ont été remplacés par les modules dans `cooking_assistant/`.

## Migration

| Ancien script | Nouveau module |
|---------------|----------------|
| `config.py` | `cooking_assistant/config.py` |
| `data_loader_preparation.py` | `cooking_assistant/data/` |
| `import_raw_data_from_source.py` | `cooking_assistant/data/downloader.py` |
| `season_utils.py` | `cooking_assistant/analysis/seasonal.py` |
| `score_calculator.py` | `cooking_assistant/analysis/scoring.py` |
| `top_reviews_analyzer.py` | `cooking_assistant/analysis/reviews.py` |
| `results_handler.py` | `cooking_assistant/utils/results.py` |
| `season_distribution.py` | `scripts/analyze_seasonal_distribution.py` |

⚠️ Ces fichiers sont conservés pour référence historique uniquement.
EOF
```

**Avantages** :
- ✅ Conserve l'historique
- ✅ Permet la comparaison
- ✅ Réversible
- ✅ Ne casse rien

### Option 2 : Suppression complète (Plus risqué)

```bash
# ⚠️ ATTENTION : Vérifier d'abord que tout fonctionne avec les nouveaux modules !

# Supprimer définitivement les anciens fichiers
rm scripts/config.py
rm scripts/data_loader_preparation.py
rm scripts/import_raw_data_from_source.py
rm scripts/season_utils.py
rm scripts/score_calculator.py
rm scripts/top_reviews_analyzer.py
rm scripts/results_handler.py
rm scripts/season_distribution.py
```

**Inconvénients** :
- ❌ Perte de l'historique
- ❌ Difficile de comparer
- ❌ Irréversible

## 📁 Structure finale recommandée

```
scripts/
├── __init__.py
├── 01_classifier_generator.py              # ✅ Script complexe à garder
├── example_calculate_rankings.py           # ✅ Nouveau script exemple
├── analyze_seasonal_distribution.py        # ✅ Nouveau script
└── deprecated/                             # 🗑️ Anciens scripts
    ├── README.md
    ├── config.py
    ├── data_loader_preparation.py
    ├── import_raw_data_from_source.py
    ├── season_utils.py
    ├── score_calculator.py
    ├── top_reviews_analyzer.py
    ├── results_handler.py
    └── season_distribution.py
```

## 🔍 Vérification avant nettoyage

Avant de déplacer/supprimer, vérifiez qu'aucun autre fichier n'importe ces scripts :

```bash
# Rechercher les imports des anciens scripts
grep -r "from scripts.config import" .
grep -r "from scripts.data_loader_preparation import" .
grep -r "from scripts.season_utils import" .
# etc.
```

## 📝 Mise à jour du .gitignore

Si vous déplacez vers `deprecated/`, ajoutez au `.gitignore` :

```
# Scripts dépréciés (conservés pour historique seulement)
scripts/deprecated/
```

## ✅ Checklist de nettoyage

- [ ] Vérifier que tous les nouveaux modules fonctionnent
- [ ] Tester `example_calculate_rankings.py`
- [ ] Tester `analyze_seasonal_distribution.py`
- [ ] Rechercher les imports des anciens scripts
- [ ] Créer `scripts/deprecated/`
- [ ] Déplacer les 8 fichiers dépréciés
- [ ] Créer `scripts/deprecated/README.md`
- [ ] Mettre à jour `.gitignore` si nécessaire
- [ ] Commit des changements
- [ ] (Optionnel) Supprimer `deprecated/` après quelques semaines

## 🎯 Recommandation finale

**Utilisez l'Option 1 (deprecated/)** pour :
1. Conserver l'historique
2. Permettre la comparaison
3. Garder une trace de l'ancien code
4. Faciliter la transition

Vous pourrez supprimer `deprecated/` dans quelques semaines une fois que tout est stable.
