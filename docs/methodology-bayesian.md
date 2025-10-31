# Bayesian Ranking Methodology

We compute a shrunk score per recipe type-season:

Score = (gamma * mean_rating + k_pop * popularity_adjustment + k_b * baseline) / (gamma + k_pop + k_b)

Where:
- mean_rating: empirical average rating
- popularity_adjustment: log or damped count-based uplift rewarding sufficient reviews
- baseline: global prior toward central tendency to prevent early inflation
- gamma, k_pop, k_b: hyperparameters tuned via holdout stability & top-K precision analysis.

Final ranking selects top-N per (type, season) and exposes both shrunk and raw metrics.
