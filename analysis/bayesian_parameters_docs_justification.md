#  Parameter Selection Analysis

## Purpose

This directory contains analysis files that contribute to justify the choice of **Bayesian parameters** (kb, kpop, gamma) used in the recipe recommendation system for a top 20 evaluation of recipes by season and by type of recipes (dish, beverage, dessert).

The analysis uses existing scripts from the `scripts/` directory:
- `scripts/season_distribution.py` - For seasonal distribution analysis  
- `scripts/top_reviews_analyzer.py` - For top reviews analysis


### Generated Files

The analysis generates 2 CSV files saved in `analysis/results_to_analyse/`:

- **`distribution_saisonniere_par_type.csv`** - Seasonal distribution analysis showing review counts by recipe type and season
- **`top_100_reviews_by_type_season_[timestamp].csv`** - Combined analysis of top 100 recipes by reviews for each recipe type and season

## How to Generate Analysis Files

These files are automatically generated when running the analysis script:
```bash
cd analysis/parameter_justification
python generate_csv_to_analyse_for_parameter_justification.py
```

The script will:
1. **Load classified recipes** from the cooking assistant data modules
2. **Run seasonal distribution analysis** using `scripts/season_distribution.py`
3. **Run top reviews analysis** using `scripts/top_reviews_analyzer.py`
4. **Save both CSV files** directly to `analysis/results_to_analyse/`

This analysis provides immediate insights into the data structure and helps to justify the Bayesian parameters choices.

### Data Structure

#### `top_100_reviews_by_type_season.csv`
| Column | Description |
|--------|-------------|
| `season` | Season (Spring, Summer, Fall, Winter) |
| `type` | Recipe type (plat, dessert, boisson) |
| `recipe_id` | Unique recipe identifier |
| `name` | Recipe name |
| `total_reviews` | Total number of reviews for the recipe |
| `valid_reviews` | Number of reviews with rating > 0 |
| `median_reviews_type_season` | Median number of reviews for the top 100 recipes of this type in this season |

#### `distribution_saisonniere_par_type.csv`
| Column | Description |
|--------|-------------|
| `Type_Recette` | Recipe type (plat, dessert, boisson) |
| `Saison` | Season (Spring, Summer, Fall, Winter) |
| `Nombre_Reviews` | Number of reviews for this type in this season |
| `Pourcentage` | Percentage of reviews for this type in this season |

## Analysis Purpose

This analysis helps to justify the parameter selection by showing:

1. **Review Distribution Patterns** - How reviews are distributed across seasons and recipe types 
2. **Popular Recipe Characteristics** - What makes recipes successful in terms of review volume 
3. **Median** - The median number of reviews for top 100 recipes provides insight into typical popularity levels by type and season
4. **Parameter Calibration** - Evidence for choosing specific 'kb', 'kpop', and 'gamma' values depending on data patterns
5. **Seasonal Bias Analysis** - Understanding how recipe popularity varies by season to inform parameter choices


##  Mathematical Context of the Bayesian model

### Bayesian Q-Score Formula

(1) Q-Score = (valid_avg_rating × nb_valid_ratings + season_avg × kb) / (nb_valid_ratings + kb)

**Where:**
- valid_avg_rating : Average rating of reviews with rating > 0 (excludes rating=0 which are considered as non-ratings)
- nb_valid_ratings : Number of reviews with rating > 0 for this recipe in this season
- season_avg : Average rating for all recipes of this type during this season (seasonal baseline)
- kb : Bayesian parameter controlling conservatism 

### Popularity Weight Formula

(2) Pop_Weight = (1 - exp(-nb_season_reviews / kpop))^gamma

**Where:**
- nb_season_reviews : Total number of reviews (including rating=0) for this recipe in this season
- kpop : Popularity threshold parameter 
- gamma : Amplification factor for popularity (higher gamma = more emphasis on popularity vs quality)

### Final Score

(3) Final_Score = Q-Score*Pop_Weight

- Final_Score : Combined score balancing quality and popularity (0 to 5 scale)

## Hypothesis made for the model

# Treatment of rating = 0

For our model, the null rating attributed in the dataset does not means certainly that the reviewers put a 0 on the recipe but it could mean a total absence of reviews (A lot of recipes with 0 have a positive review). In this idea, in our model, we choose to retire the reviews with 0 in the determination of the average rating of the recipe but we keep it as a review in the population factor because the review exists and this weight has to be considered. 

# Choice of favorizing the population over the quality

Considering the system of ratings attributed in the dataset (0 to 5 with a large amount of rates of 4 and 5), it is pertinent for a high number of reviews (over 50) in this case that population predominates over quality when you make a top 20,30, 50 because the system of ratings is too large and not sufficiently efficient to applicate a 50/50 contribution. For a top with a small number of reviews, quality has a higher part because there is a small differences of reviews between the top and the difference is made by the factor of quality.

Then, it is the role of the data scientists and his customer after meetings to determine how we want to prioritize for the top. In absence of meetings with the customer, the data scientists choose his own way to make the top the more efficient possible with the data provided. In our case, we choose a Bayesian model to adapt it and we have to justify our choice of set of bayesian parameters in this model.

## Justification of the choice to let the same set of Bayesian Parameters for each season

The decision to apply identical Bayesian parameters (kb, kpop, gamma) across all four seasons for each recipe type is justified by the stability in review distribution patterns observed in the file `distribution_saisonniere_par_type.csv`. Analysis of this file reveals that review volumes are nearly uniformly distributed across seasons: main dishes show 23.71-26.96% per season (±1.6% from the mean), desserts show 23.45-26.39% (±1.5%), and beverages 19.54-28.76% (higher variance but representing only 1.2% of total reviews, thus limited statistical impact). This balanced distribution indicates that user engagement and rating behavior remain fundamentally consistent throughout the year, with no season dominating the dataset or exhibiting drastically different review dynamics.

Furthermore, examination of `top_100_reviews_by_type_season.csv` shows that median review counts for top recipes maintain proportional stability across seasons: main dishes range from 87-114 reviews (±13% variation), desserts from 61.5-78 reviews (±12% variation), and beverages from 6-8 reviews (±14% variation). While absolute numbers vary moderately, the relative scale and rating reliability remain consistent—a recipe with 100 reviews in Spring is statistically comparable to one with 100 reviews in Fall. The Bayesian Q-Score formula already accounts for seasonal context through the season_avg , which dynamically adjusts for each type-season combination without requiring parameter recalibration. Using different parameters per season would introduce unnecessary complexity, risk overfitting to seasonal noise rather than capturing genuine quality signals, and compromise cross-seasonal comparability. 

This uniform approach ensures that scoring rigor remains consistent while the season_avg mechanism preserves necessary seasonal adaptation.

Then, we have to settle 3 set of parameters by type of recipes

# Justification of the set of Bayesian parameters by type of recipes

For the justification, it is important to analyze after computing the app the two files described up and to understand the review. This analyse is personal and can be changed when the size of the dataset increases or where the customers want a top of recipes with different criteria of selection.

## kb justification 

The parameter **kb** (Bayesian pseudo-reviews) represents the number of virtual reviews at the seasonal average rating that are added to each recipe's actual reviews. It acts as a conservative "prior" that pulls recipes with few reviews toward the baseline average, preventing inflated scores from limited data. A higher kb means stronger regression toward the mean, requiring more actual reviews to deviate from the seasonal baseline. The choice of kb values reflects the inherent variability and rating reliability observed in each recipe type.

For main dishes (plats), we set kb = 65 to balance conservatism with responsiveness. Main dishes show moderate rating variability (median top 100: 90-114 reviews per season). A kb of 65 ensures recipes need substantial evidence (roughly 65+ reviews) to significantly outweigh the seasonal average, filtering out one-hit wonders while allowing genuinely popular dishes to rise. For **desserts**, we use kb = 60, reflecting their slightly lower median review counts (60-78 reviews) and higher rating consistency—desserts tend to cluster around 4.5-4.8 stars with less variance than savory dishes. The moderate kb allows well-loved desserts to emerge without being overly penalized by the prior. Finally, **beverages(boisson)** receive kb = 20 due to their dramatically lower review volumes (median: 5-8 reviews) and exceptionally high rating stability (often 4.7-4.9 stars). A low kb is necessary because beverages rarely accumulate many reviews; a higher value would render the Bayesian score meaningless by anchoring too strongly to the prior, preventing any beverage from distinguishing itself despite consistent high ratings.

## kpop justification

The parameter **kpop** serves as the scaling factor in the popularity weight formula, controlling how quickly the popularity effect saturates as the number of reviews increases. It determines the threshold at which additional reviews have diminishing returns on the popularity weight. A lower kpop value causes the popularity weight to rise rapidly with just a few reviews, while a higher kpop value spreads the effect over a larger range of review counts, requiring more reviews for the popularity weight to approach its maximum.

The selection of kpop values is based on identifying a review count threshold that typically appears between the 30th and 50th ranked recipes in the top 100 for each type-season combination, corresponding to a popularity weight (Pop_Weight) of approximately 0.9. This calibration ensures that recipes ranking in the top 30-50 range have already achieved 90% of the maximum popularity contribution, meaning they are recognized as sufficiently popular without being penalized relative to the absolute top performers.

After anaylisis of the top `top_100_reviews_by_type_season.csv`, the thresold for dishes is set at 105 for dishes, 90 for dessert and 9 for beverages.

The kpop are then calculated thanks to the formulas of Pop_Weight(2) with a wpop=0.9.

Then,

for **dishes(plat)** : kpop = 45
for **dessert** : kpop = 40
for **beverages(boisson)** : kpop = 4

## gamma justification

The parameter **gamma** acts as an amplification exponent in the popularity weight formula, controlling how aggressively the system rewards popularity. The choice of gamma reflects how much we want popularity to dominate the final ranking versus allowing quality ratings to play a more balanced role.

For **main dishes (plats)** and **desserts**, we set gamma = 1.2, applying moderate amplification to reward recipes that have achieved broad popularity. In these categories, review volumes can vary significantly (dishes: 60-500 reviews, desserts: 40-370 reviews), and a gamma > 1 helps distinguish genuinely crowd-favorite recipes from those with modest but respectable engagement. The value of 1.2 strikes a balance: it's high enough to create meaningful separation in the top 20 rankings, but not so high as to completely overshadow quality ratings.

For **beverages (boissons)**, we use gamma = 0.7, applying a dampening effect that compresses popularity differences. Beverages exhibit dramatically lower review volumes (typically 5-20 reviews for top recipes) and much higher rating homogeneity. With such limited variation, a gamma > 1 would create arbitrary ranking distinctions based on small review count differences (12 vs 11 reviews), which may not reflect true quality differences. By setting gamma < 1, we ensure that the popularity weight rises more gradually, preventing the system from over-prioritizing recipes that happen to have a few extra reviews while still rewarding those with consistently strong engagement. 





