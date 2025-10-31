# Multi-Signal Recipe Classifier (Structural x NLP)

**Objective:** Classify recipes into **`plat` / `dessert` / `boisson`** by combining quantitative nutritional features and textual cues through a dual-phase model followed by an explicit arbitration layer. The entire process is designed to be interpretable, numerically stable, and reproducible.

## Data

**Source:** [Food.com Recipes & Interactions (Kaggle)](https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions?select=RAW_interactions.csv)
We use `INPUT_rawrecipes.csv` as the primary dataset.

---

## Method Overview

The pipeline consists of **four sequential phases**, moving from raw nutritional data to a final decision obtained through a rule-based stacking mechanism.

### Phase 0 — Structural Features (Nutrition Parsing)
We parse the field `nutrition -> [cal, fat, sugar, sod, prot, sat, carbs]` and construct normalized, calorie-scaled variables.

Initial formulas:
```
sugar_density = sugar / (cal + ε) 
prot_density  = prot  / (cal + ε)
sod_density   = sod   / (cal + ε)
```

Energy contributions:
```
fat_E%  = 9 * fat   / cal
carb_E% = 4 * carbs / cal
prot_E% = 4 * prot  / cal
```

Composite indicators:
```
sweet_idx  = 0.55 * sugar_E%   + 0.45 * sugar_density
savory_idx = 0.55 * prot_density + 0.45 * (sod_density / 10)
hybrid_idx = min(sweet_idx, savory_idx)
lean_idx   = 1 - fat_E%
```

All metrics are bounded and ε-regularized to avoid numerical instability.

### Phase 1 — Structural Prototype Classifier
Each recipe is embedded in a 3D flavor-energy space `(sweet, savory, lean)` and compared to fixed class prototypes:

| Class | Sweet | Savory | Lean |
|-------|:-----:|:------:|:----:|
| Dessert | 0.68 | 0.07 | 0.40 |
| Plat    | 0.12 | 0.28 | 0.45 |
| Boisson | 0.09 | 0.05 | 0.85 |

Classification uses cosine similarity plus heuristic corrections (e.g. high-sugar + low-sodium → dessert, lean + low-protein → boisson). Probabilities via softmax; confidence uses probability margin + entropy.

### Phase 2 — NLP (Name + Tags)
Lexical extraction from `name` and `tags` using two dictionaries:
* STRONG lexicon: decisive terms (presence 0/1)
* SOFT lexicon: suggestive terms (counts)

Logits:
`logits = α * STRONG + β * SOFT + 0.1` with `α=3.0`, `β=0.8`; then softmax.

Examples:
* “stew”, “curry”, “chili” → `plat`
* “cake”, “brownie”, “cheesecake” → `dessert`
* “smoothie”, “latte”, “milkshake” → `boisson`

### Phase 3 — Explicit Arbiter (Mini-Stacking)
Phases 1 and 2 are independent classifiers. An arbitration layer:
1. Derives NLP vote (label + strength)
2. Compares with structural label & confidence
3. Blends probabilities based on agreement and confidence hierarchy

Rules summary:
* Strong structural confidence → structure dominates, NLP adjusts
* Weak structural confidence → NLP gains weight or overrides
* ID-based exceptions for known ground truth; domain-specific forced mappings (e.g. smoothies → boisson)

Confidence recalculated from blended probabilities using calibrated entropy/margin mapping.

## Outputs
Each recipe receives:
* `p_struct_*`, `p_nlp_*`, `p_final_*` probability vectors
* `type` final predicted class
* `conf_%` calibrated confidence
* optional `exception_hit` flag

## Reproducibility Notes
* Nutritional parsing is defensive with ε stabilizers to avoid division by zero.
* Lexicons are compiled into single regex unions for speed.
* Prototype similarities use cosine; logits adjusted with domain heuristics before softmax.
* Confidence function combines margin + entropy with penalties for ambiguous hybrids.

## Extensibility
* Add new classes by defining prototype vectors and extending lexicons.
* Replace heuristics with learned calibration (e.g. logistic regression on hold‑out ground truth) once labeled data available.
* Export intermediate probability tables for audit in `data/interim/` (future enhancement).

---
For deeper mathematical context or Bayesian ranking parameter justifications, see:
* `analysis_parameter_justification/bayesian_parameters_docs_justification.md`
