# Design Rationale

This document explains the UI/UX and visual design decisions for the Cooking Assistant Streamlit application.

## Objectives
- Present analytical insights (Bayesian score, effort score, quadrants, correlations) clearly and accessibly.
- Maintain high contrast and legibility for diverse lighting conditions.
- Ensure consistency and avoid inline style drift.
- Communicate ethical stance (real data vs synthetic) transparently.

## Core Principles
1. Accessibility first: readable font sizes, sufficient contrast, focus states.
2. Consistency: one `styles.css` controlling theme variables.
3. Hierarchy: semantic grouping using info boxes & bullet lists vs large paragraphs.
4. Explainability: immediate plain-language interpretation accompanying each chart.

## Typography
- Base font size slightly increased from Streamlit default (16px → ~17-18px for body) for readability.
- Headings rely on Streamlit defaults to preserve recognizable structure.
- Monospace blocks reserved for formulas and parameter snippets.
- Line-height > 1.4 to reduce dense text fatigue.

## Color Palette (Variables in `app/streamlit/styles.css`)
| Variable | Purpose |
|----------|---------|
| `--bg-gradient-start` / `--bg-gradient-end` | Soft neutral gradient background; lowers visual noise vs solid white |
| `--accent` | Primary accent for tags & emphasis (recipes quadrant tags) |
| `--accent-alt` | Secondary accent for hover and interactive states |
| `--border-soft` | Subtle borders around info boxes (contrast without harsh lines) |
| `--text-primary` | Default text color (near-black for AAA contrast) |
| `--text-muted` | Secondary descriptive copy |
| `--info-bg` | Background for info/insight panels |
| `--warning-bg` | Reserved for any cautionary / data authenticity flags |

Contrast ratios were selected to exceed WCAG AA or AA Large thresholds.

## Layout & Components
- Bullet lists used for methodology and interpretation sections to optimize scan-ability.
- Info boxes encapsulate critical formulas and parameter rationale.
- Quadrant visualization accompanied by a legend describing each quadrant semantics (High Quality / Low Effort, etc.).
- Correlation panel orders features by absolute correlation with `bayes_mean` to orient user to strongest relationships first.

## Iconography & Tags
- Tags (CSS class `.quadrant-tag`) provide immediate secondary encoding for quadrant classification beyond the scatter plot position.

## Ethical Transparency
- `STRICT_REAL_DATA` flag documented and surfaced in UI context sections. When active, suppresses synthetic fallback metrics and labels sections explicitly as “Real Data Only”.
- Avoids misleading high scores from recipes lacking sufficient interaction evidence.

## Responsive & Failure Modes
- Styles designed to degrade gracefully if custom CSS fails to load (Streamlit defaults still usable).
- If data is missing for a given chart, an explanatory message replaces the visualization rather than leaving empty space.

## Future Improvements
- Add color-blind safe alternative palette layer (e.g., CSS class `.cb-mode` toggling a distinct set of variables).
- Integrate dynamic font scaling control (user selectable size).
- Provide downloadable accessibility statement.
- Add ARIA roles for non-semantic wrappers if Streamlit components expanded.

## Rationale Summary
Design choices emphasize clarity, interpretability, and accessibility for an analytical teaching context while enabling quick evolution. Centralizing styling reduces maintenance cost and ensures unified visual language across expanding feature set.
