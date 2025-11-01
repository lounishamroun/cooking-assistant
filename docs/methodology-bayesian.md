# Bayesian Ranking Methodology

Goal: Rank recipes within each (Season, Recipe Type) balancing rating quality and engagement (review volume) while preventing early over-inflation of sparse items.

## 1. Inputs
Per (recipe, season, type):
- `valid_avg_rating` – mean of ratings > 0 (ignore 0 placeholder ratings)
- `nb_valid_ratings` – count of ratings > 0
- `nb_season_reviews` – all reviews (including those with rating 0) in that season
- `season_avg` – baseline average rating for (type, season) (excluding those with rating 0)

## 2. Quality Shrinkage (Q)
Implemented formula:
```text
Q = (kb * season_avg + nb_valid_ratings * valid_avg_rating) / (kb + nb_valid_ratings)
```
Why shrink? Recipes with very few ratings regress toward the seasonal baseline preventing unstable spikes.

Interpretation:
- High `nb_valid_ratings` → Q approaches empirical average.
- Low `nb_valid_ratings` → Q stays near `season_avg` (less variance).

## 3. Popularity Weight
We apply a saturating curve so early review accumulation matters most:
```text
Pop_Weight = (1 - exp(- nb_season_reviews / kpop)) ^ gamma
```
Characteristics:
- Near 0 reviews → weight ≈ 0 (quality alone not enough to rank high).
- As reviews grow, weight rises quickly then plateaus (diminishing returns).
- `gamma > 1` amplifies separation between moderately and highly engaged items; `gamma = 1` is neutral.

## 4. Final Score
```text
Final = Q * Pop_Weight
```
Multiplicative combination ensures BOTH quality and engagement are required. A recipe with stellar ratings but no audience, or large audience with mediocre ratings, will not dominate.

## 5. Parameter Rationale

| Parameter | Role | Effect of Larger Value | Selection Rationale |
|-----------|------|------------------------|---------------------|
| `kb` | Shrink strength | More pull toward baseline for low-review items | Stabilizes early ranking; tuned so ~5–10 reviews begin to outweigh prior |
| `kpop` | Review count scale | Slower approach to saturation | Calibrated so typical seasonal mid-tier review volume (e.g. 15–30) yields ~70–80% of max weight |
| `gamma` | Popularity curvature | Increases contrast of high-engagement recipes | Mild >1 (e.g. 1.15–1.3) to avoid overpowering quality |

Parameters may differ per type (Dessert may have higher average engagement → slightly higher `kpop`; Beverage may need lower `kb` due to sparser ratings). See `cooking_assistant/config.py` for exact current values.

## 6. Design Choices
| Choice | Reason |
|--------|--------|
| Shrink to seasonal type average | Seasonal context captures temporal taste shifts (e.g. warm comfort food in Winter) |
| Exclude rating == 0 from `valid_avg_rating` | 0 often encodes interaction without a vote; including it biases averages downward unfairly |
| Saturating exponential popularity | Avoids linear runaway for viral items; keeps leaderboard diverse |
| Multiplication (Q * Pop_Weight) | Enforces joint necessity; additive models could let one term dominate |
| Per-type parameter tuning | Engagement distribution differs; uniform values produced skewed dominance by high-review categories |

## 7. Validation Procedure (Summary)
1. Holdout season slice to test stability of top-K membership under parameter perturbations.
2. Sensitivity sweeps: vary `kb`, `kpop`, `gamma` ±20% measuring Jaccard overlap of top 20 lists.
3. Manual spot checks: recipes with very low reviews should not rank above well-reviewed peers unless ratings are consistently high.

## 8. Edge Cases & Safeguards
- If `nb_valid_ratings = 0` → Q = `season_avg` (no misleading high score).
- If `nb_season_reviews = 0` → `Pop_Weight = 0` → Final = 0 (unengaged items defer ranking).
- Missing seasonal baseline falls back to global type average (rare; guarded in pipeline).

## 9. Limitations / Future Improvements
- Does not account for recency of reviews (time decay possible future enhancement).
- Treats all reviews equally; sentiment or text length could refine popularity weight.
- Seasonal baseline assumes consistent season segmentation; extreme climate variations not modeled.
- Popularity plateau may under-reward exceptionally sustained engagement; a second-tier boost could be explored.

## 10. Summary
The ranking intentionally balances stability (shrinkage) and responsiveness (popularity curve). Parameter choices were guided by top-K stability, preventing early volatility, and ensuring no single axis (quality vs. raw volume) monopolizes leaderboard positions.

For the exact numeric parameters and any recent tuning changes, consult the configuration in `cooking_assistant/config.py` and parameter justification CSVs.
