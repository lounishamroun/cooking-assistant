# Design Rationale

## Removed Correlation Matrix
The correlation heatmap page was removed because it did not materially inform parameter tuning or ranking decisions. It risked distracting evaluators with low-signal pairwise correlations, offering little actionable guidance beyond what targeted metrics (quadrants, seasonal distribution) already convey.

## Canonical vs Timestamped Artifacts
Justification scripts produce timestamped CSV snapshots for historical traceability AND stable `*_latest.csv` aliases used by the UI. This prevents brittle hard-coded filenames while preserving reproducibility.

## Multi-Phase Classification
Structured nutritional indices are less noisy than raw names; lexical signals capture semantic intent. Arbitration ensures neither dominates when uncertain. This yields interpretable, auditable decisions for grading.

## Bayesian Ranking Choices
Shrinkage protects early stage recipes from volatile averages. Saturating popularity curve prevents runaway effects. Multiplicative combination enforces joint quality + engagement.

## Language Normalization
French-origin column & type labels are normalized to English in UI to reduce cognitive switching for evaluators; raw values retained for provenance.

## Simplicity over Heavy Modeling
Rule-based + lightweight similarity chosen due to time constraints and to emphasize transparency. Future iterations can layer learned embeddings or calibrated probability models.

## Confidence Metric
Heuristic blend of structural and lexical certainty (agreement bonus, disagreement penalty). Not a probability; documented to avoid misinterpretation.

## Future Improvement Targets
- Learn prototype vectors via clustering.
- Sentiment or semantic review weighting.
- Time decay in popularity.
- Automated lexicon expansion from corpus statistics.
