# Evaluation Cheat Sheet
(For quick instructor review)

| Aspect | Key Point |
|--------|-----------|
| Objective | Seasonal recipe ranking + transparent classification |
| Classification Phases | Structural indices → Prototype similarity → Lexicon scoring → Arbitration |
| Ranking Formula | Q shrinkage + popularity saturation → Final = Q * Pop_Weight |
| Data Sources | RAW_recipes.csv (classification) + RAW_interactions.csv (ranking) + recipes_classified.csv |
| Shrinkage Rationale | Stabilize few-rating items using seasonal baseline |
| Popularity Curve | Exponential saturation prevents dominance by very high review counts |
| Artifacts Strategy | Timestamped history + stable `*_latest.csv` for UI reliability |
| Removed Feature | Correlation matrix (low decision impact) |
| Confidence | Blended structural+lexical logits (agreement bonus, disagreement penalty) |
| Naming Consistency | UI: Main Dish / Dessert / Beverage; raw retains plat/dessert/boisson |
| Robustness | Fallback interpreter logic; graceful data missing warnings |
| Limitations | Manual prototypes, static lexicon, no time decay, heuristic confidence |
| Future Work | Embedding-based prototypes, sentiment-weighted popularity, dynamic seasons |
