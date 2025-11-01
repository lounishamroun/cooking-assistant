# Classification Methodology

Goal: Assign each recipe a type (Main Dish, Dessert, Beverage) with a confidence score using layered signals that are robust to sparse or noisy text.

## 1. Data Signals
- Raw nutrition fields (calories, macronutrients, sugar, sodium, etc.)
- Tokenized name & tag strings (lowercased, stemmed where applicable)
- Curated keyword lexicons (STRONG, SOFT) per type

## 2. Phases Overview
| Phase | Name | Purpose | Key Outputs |
|-------|------|---------|-------------|
| 0 | Structural Feature Extraction | Derive flavor / energy indices from nutrition | `sweet_idx`, `savory_idx`, `lean_idx`, `hybrid_idx` |
| 1 | Prototype Similarity | Map recipe vector → cosine similarity vs curated archetypes | Raw structural logits |
| 2 | NLP Lexicon Scoring | Score presence & frequency of type-indicative terms | Lexicon-derived logits |
| 3 | Arbitration Layer | Combine structural & lexical logits into final decision | `Type`, `Confidence_Percentage` |

### Phase 0 – Structural Feature Extraction
Compute normalized densities & energy proportions. Indices (example weights):
```text
sweet_idx  = 0.55 * sugar_E% + 0.45 * sugar_density
savory_idx = 0.55 * prot_density + 0.45 * (sod_density/10)
lean_idx   = 1 - fat_E%
hybrid_idx = min(sweet_idx, savory_idx)  # detects mixed profiles
```
Rationale: Nutrition offers stable signals compared to noisy user-entered tags.

### Phase 1 – Prototype Similarity
Prototypes encode typical flavor vectors:
```text
Dessert  ≈ (0.68, 0.07, 0.40)
Main Dish ≈ (0.12, 0.28, 0.45)
Beverage ≈ (0.09, 0.05, 0.85)
```
Each recipe’s (sweet_idx, savory_idx, lean_idx) is cosine-compared to these prototypes. Heuristics adjust logits (e.g. penalize implausibly low-cal savory items; boost fruit-forward desserts).

### Phase 2 – NLP Lexicon Scoring
Two lexicons:
- STRONG (binary): decisive anchors (`cheesecake`, `smoothie`, `curry`).
- SOFT (counts): supportive context tokens.
Combined formula (illustrative):
```text
lexicon_logit = 3.0 * STRONG + 0.8 * SOFT + 0.1
```
Then normalized (softmax) to produce lexical confidence per type.
Rationale: Text captures dish intent even if nutrition ambiguous (e.g. beverages low-cal but distinctive names).

### Phase 3 – Arbitration Layer
Blends structural and lexical logits:
1. Compute structural confidence: gap between top and second structural logits.
2. Cases:
	- High structural confidence → structural type retained; lexical used only to boost certainty if coherent.
	- Medium structural confidence & strong lexical evidence → lexical wins.
	- Disagreement with low structural & weak lexical → fallback to structural top (conservative).
3. Explicit overrides: beverage keywords (e.g. `smoothie`, `milkshake`) force Beverage if lexical score passes threshold.
4. Edge exceptions: Handful of IDs manually corrected if known misclassification patterns.

### Confidence Calculation
Base confidence = max(blended_logits) * 100 (rounded). Adjustments:
- Penalize if structural & lexical disagree strongly (> threshold delta).
- Slight bonus if both agree and have > median certainty.

## 3. Output Fields
- `Type` – Final category.
- `Confidence_Percentage` – 0–100 summarizing blended certainty.
- (Interim) indices & logits retained in interim file for auditing.

## 4. Design Choices & Rationale
| Choice | Reason |
|--------|--------|
| Multi-phase instead of single text model | Combats sparse / noisy titles; nutrition offers objective signals |
| Cosine similarity prototypes | Lightweight, interpretable; avoids need for training embeddings |
| Two-tier lexicon (STRONG/SOFT) | Preserves high-precision anchors while allowing broader context influence |
| Arbitration logic (rule-based) | Deterministic & explainable under time constraints; future ML stacking possible |
| Manual overrides for beverages | Beverage nutrition overlaps with dessert; keywords disambiguate |

## 5. Validation & Quality Checks
- Spot check high-confidence predictions across types for semantic plausibility.
- Distribution balance: ensure no dominant type due solely to nutrition skew.
- Review misclassified borderline items (high hybrid_idx) for lexicon gaps → iteratively add missing terms.

## 6. Limitations / Future Improvements
- Manual prototype vectors; could be learned from clustered embeddings.
- Lexicon maintenance required for emerging culinary terms.
- Rule-based arbitration might miss nuanced cases (e.g., dessert beverages vs beverage desserts).
- Does not leverage full ingredient list semantics (only nutrition aggregates & name tokens).
- Confidence formula heuristic, not calibrated probability.

## 7. Summary
The classifier combines interpretable nutritional structure with flexible lexical cues, then arbitrates using transparent rules to produce stable, auditable type assignments feeding seasonal ranking.

For deeper numeric examples and parameter context, see the justification artifacts in `analysis_parameter_justification/`.
