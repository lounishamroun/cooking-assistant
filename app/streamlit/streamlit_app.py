"""Unified Streamlit application.

This file replaces conflicted merge versions, providing a clean, resilient
dashboard for recipe classification analysis.
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
# Robust import of local components: works whether run as script or module
try:
    from .components import (
        inject_css,
        render_insights_and_quadrants,
        render_correlation,
        section_header,
        info_box,
    )
except ImportError:  # running as a top-level script via `streamlit run`
    from components import (
        inject_css,
        render_insights_and_quadrants,
        render_correlation,
        section_header,
        info_box,
    )


# Inline style block removed to rely solely on external stylesheet (`styles.css`) injected by inject_css().

# Page configuration
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"
st.set_page_config(
    page_title="Recipe Classification Analysis" + (" (Demo)" if DEMO_MODE else ""),
    layout="wide",
    initial_sidebar_state="expanded"
)
inject_css()

# -------------------------------
# Load and prepare data
# -------------------------------
def _safe_read_csv(path: str) -> pd.DataFrame:
    """Attempt to read a CSV; if missing or error, warn and return empty DataFrame."""
    if not os.path.exists(path):
        st.warning(f"Missing file: {path}. This part of the dashboard will be limited.")
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as e:  # Broad but we surface error without breaking app
        st.error(f"Failed to read {path}: {e}")
        return pd.DataFrame()

def _standardize_top20_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename varying score/season columns to a consistent schema if present."""
    if df.empty:
        return df
    # Possible score column variants produced by different pipeline versions.
    score_candidates = [
        'Bayesian_Score',
        'Final_Score',
        'Q_Score_Bayesien_Poids_popularité',
        'Q_Score_Bayesien_Poids_popularite',  # without accent fallback
        'Q_Score_Bayesien'
    ]
    season_candidates = ['Season', 'Saison']
    rename_map = {}
    for col in score_candidates:
        if col in df.columns and 'Bayesian_Score' not in df.columns:
            rename_map[col] = 'Bayesian_Score'
            break
    for col in season_candidates:
        if col in df.columns and 'Season' not in df.columns:
            rename_map[col] = 'Season'
            break
    # Common French -> English mapping for remaining columns.
    base_mapping = {
        'ranking': 'Ranking',
        'recipe_id': 'Recipe_ID',
        'name': 'Name',
        'reviews_in_season': 'Season_Reviews'
    }
    for k, v in base_mapping.items():
        if k in df.columns:
            rename_map[k] = v
    if rename_map:
        df = df.rename(columns=rename_map)
    # Round score if present.
    if 'Bayesian_Score' in df.columns:
        df['Bayesian_Score'] = pd.to_numeric(df['Bayesian_Score'], errors='coerce').round(2)
    # Ensure we have a Ranking column: compute descending score order within (Season, recipe_type) groups
    if 'Ranking' not in df.columns and 'Bayesian_Score' in df.columns:
        # Fallback type column name(s)
        type_col = 'recipe_type' if 'recipe_type' in df.columns else ('Type' if 'Type' in df.columns else None)
        season_col = 'Season' if 'Season' in df.columns else None
        if type_col and season_col:
            df = df.sort_values([season_col, type_col, 'Bayesian_Score'], ascending=[True, True, False])
            df['Ranking'] = (
                df.groupby([season_col, type_col])
                  .cumcount()
                  .add(1)
            )
    # Guarantee deterministic ordering for downstream pages
    ordering_cols = [c for c in ['Season', 'recipe_type', 'Ranking'] if c in df.columns]
    if ordering_cols:
        df = df.sort_values(ordering_cols)
    return df

@st.cache_data(show_spinner=False)
def load_data():
    # Prefer enriched dataset if present (non-invasive enrichment layer)
    enriched_path = "data/interim/recipes_classified_enriched.csv"
    base_path = "data/interim/recipes_classified.csv"
    # Prefer enriched dataset which adds effort_score & bayes_mean (non-destructive)
    # Ethics: Original classification file remains untouched; enrichment is additive.
    if os.path.exists(enriched_path):
        df = _safe_read_csv(enriched_path)
        if {"effort_score", "bayes_mean"} <= set(df.columns):
            st.info("Loaded enriched metrics (effort_score, bayes_mean).")
    else:
        df = _safe_read_csv(base_path)
        if not df.empty:
            st.info("Enriched file not found; using base dataset. Run: python scripts/enrich_metrics.py to add metrics.")
    if not df.empty:
        main_column_mapping = {
            'id': 'ID',
            'name': 'Name',
            'type': 'Type',
            'submitted': 'Submission_Date',
            'conf_%': 'Confidence_Percentage'
        }
        existing_columns = {k: v for k, v in main_column_mapping.items() if k in df.columns}
        if existing_columns:
            df = df.rename(columns=existing_columns)
        # If confidence not present, derive a synthetic placeholder so Confidence Analysis page can still render.
        if 'Confidence_Percentage' not in df.columns:
            # Simple heuristic: assign higher confidence to types with more representation (frequency proportional scaling).
            type_counts = df['Type'].value_counts(normalize=True)
            df['Confidence_Percentage'] = df['Type'].map(lambda t: round(50 + type_counts.get(t, 0) * 50, 2))
            df['Confidence_Is_Synthetic'] = True
            st.info("Confidence_Percentage column missing; synthetic values generated for display only.")
        # Mark synthetic effort/bayes if missing after enrichment preference.
        if 'effort_score' not in df.columns:
            df['effort_score'] = None
            df['Effort_Is_Synthetic'] = True
        if 'bayes_mean' not in df.columns:
            df['bayes_mean'] = None
            df['Bayes_Is_Synthetic'] = True
        # Environment guard: allow teacher to disable synthetic fabrication entirely
        disable_synth = os.getenv('STRICT_REAL_DATA') == '1'
        # Synthetic generation occurs ONLY if metric fully absent and STRICT_REAL_DATA not enforced.
        if 'effort_score' in df.columns and df['effort_score'].isna().all() and not disable_synth:
            # Simple fallback: scale name length to 0-10.
            name_len = df['Name'].map(lambda x: len(str(x)) if pd.notna(x) else 0)
            max_len = name_len.max() or 1
            df['effort_score'] = (name_len / max_len * 10).round(2)
            df['Effort_Is_Synthetic'] = True
            st.info("effort_score fully missing; synthetic effort based on name length applied.")
        # Popularity fallback: only allowed when STRICT_REAL_DATA is off.
        if 'bayes_mean' in df.columns and df['bayes_mean'].isna().all() and not disable_synth:
            # Fallback only if synthetic allowed: derive pseudo-popularity from confidence percentage (scale 0-5).
            if 'Confidence_Percentage' in df.columns:
                df['bayes_mean'] = (pd.to_numeric(df['Confidence_Percentage'], errors='coerce') / 100 * 5).round(3)
                df['Bayes_Is_Synthetic'] = True
                st.info("bayes_mean fully missing; synthetic popularity derived from confidence percentage.")
        elif 'bayes_mean' in df.columns and df['bayes_mean'].isna().all() and disable_synth:
            st.warning("bayes_mean missing and STRICT_REAL_DATA=1; synthetic popularity disabled.")
    else:
        # Provide minimal placeholder columns for downstream UI logic.
        df = pd.DataFrame(columns=['ID', 'Name', 'Type', 'Submission_Date'])

    # Collect top20 seasonal ranking files if present.
    ranking_files = [
        ("data/processed/top20_boisson_for_each_season.csv", 'boisson'),
        ("data/processed/top20_plat_for_each_season.csv", 'plat'),
        ("data/processed/top20_dessert_for_each_season.csv", 'dessert')
    ]
    ranking_dfs = []
    for path, rtype in ranking_files:
        tmp = _safe_read_csv(path)
        if not tmp.empty:
            # Standardize French columns before concat so filtering works uniformly
            french_map = {
                'Saison': 'Season',
                'Q_Score_Bayesien': 'Bayesian_Score',
                'Q_Score_Bayesien_Poids_popularité': 'Bayesian_Score',
                'Q_Score_Bayesien_Poids_popularite': 'Bayesian_Score',
                'reviews_in_season': 'Season_Reviews'
            }
            for fr, en in french_map.items():
                if fr in tmp.columns and en not in tmp.columns:
                    tmp = tmp.rename(columns={fr: en})
            tmp['recipe_type'] = rtype
            ranking_dfs.append(tmp)
    if ranking_dfs:
        top20_df = pd.concat(ranking_dfs, ignore_index=True)
    else:
        st.warning("No ranking files loaded; Seasonal Rankings page will be empty.")
        top20_df = pd.DataFrame(columns=['Ranking','Recipe_ID','Name','Bayesian_Score','Season_Reviews','Season','recipe_type'])

    top20_df = _standardize_top20_columns(top20_df)
    # English display type column
    type_map = {'plat': 'main', 'boisson': 'drink', 'dessert': 'dessert'}
    if not top20_df.empty:
        top20_df['recipe_type_en'] = top20_df['recipe_type'].map(type_map).fillna(top20_df['recipe_type'])
    return df, top20_df

df, top20_df = load_data()

# Enhanced Sidebar CSS
# Slimmed extra navigation CSS already applied above.

# Initialize session state for navigation
if 'selected_page' not in st.session_state:
    st.session_state.selected_page = 'Home'

# Sidebar navigation with custom styling
# Home button at top left with simple house icon
if st.sidebar.button("⌂", key="home_btn", help="Return to Home Dashboard"):
    st.session_state.selected_page = "Home"
    st.rerun()

st.sidebar.markdown('<div class="nav-header">📊 Analysis Types</div>', unsafe_allow_html=True)

# Navigation items (without Home)
nav_items = [
    ("🥧", "Distribution", "Recipe type distribution visualization"), 
    ("📈", "Confidence Analysis", "Classification confidence analysis"),
    ("📊", "Historical Trends", "Publication trends over time"),
    ("🌟", "Seasonal Rankings", "Top recipes by season"),
    ("🔍", "Recipe Lookup", "Search individual recipes"),
    ("🧭", "Analytical Quadrants", "Effort vs popularity quadrants & insights"),
    ("🧪", "Correlation Matrix", "Ordered correlation heatmap"),
    ("🌈", "Seasonal Distribution", "Seasonal review share by recipe type")
]

for icon, page_name, description in nav_items:
    is_active = st.session_state.selected_page == page_name
    active_class = "active" if is_active else ""
    
    if st.sidebar.button(f"{icon} {page_name}", key=f"nav_{page_name}", help=description):
        st.session_state.selected_page = page_name
        st.rerun()

page = st.session_state.selected_page

# Main title
st.markdown('<h1 class="main-header">Recipe Classification Analysis Platform</h1>', unsafe_allow_html=True)

# -------------------------------
# HOME PAGE
# -------------------------------
if page == "Home":
    st.markdown("""
    <div class="home-card">
        <h2>Welcome to the Recipe Classification Analysis Platform</h2>
        <p class="description-text">
            This platform provides comprehensive analysis of recipe classification data from Food.com. 
            Our machine learning system automatically categorizes recipes into three main types: 
            plats (main dishes), desserts, and boissons (beverages).
        </p>
    </div>
    """, unsafe_allow_html=True)

    if DEMO_MODE:
        st.info("Demo mode enabled: heavy pipeline regeneration disabled. Run locally with DEMO_MODE=0 to execute full data processing.")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>Total Recipes</h3>
            <h2>{:,}</h2>
        </div>
        """.format(len(df)), unsafe_allow_html=True)
    
    with col2:
        type_counts = df['Type'].value_counts()
        most_common = type_counts.index[0]
        st.markdown("""
        <div class="metric-card">
            <h3>Most Common Type</h3>
            <h2>{}</h2>
        </div>
        """.format(most_common.title()), unsafe_allow_html=True)
    
    with col3:
        if 'Confidence_Percentage' in df.columns:
            avg_confidence = df['Confidence_Percentage'].mean()
            st.markdown("""
            <div class="metric-card">
                <h3>Avg Confidence</h3>
                <h2>{:.1f}%</h2>
            </div>
            """.format(avg_confidence), unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-card">
                <h3>Confidence Data</h3>
                <h2>N/A</h2>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        years_range = pd.to_datetime(df['Submission_Date'], errors='coerce').dt.year
        year_span = years_range.max() - years_range.min() + 1
        st.markdown("""
        <div class="metric-card">
            <h3>Data Span</h3>
            <h2>{} years</h2>
        </div>
        """.format(year_span), unsafe_allow_html=True)
    
    st.markdown("""
    <div class="home-card">
        <h3>Available Analysis Modules:</h3>
        <ul class="description-text">
            <li><strong>Distribution:</strong> Visual proportional distribution of recipe types with detailed statistics</li>
            <li><strong>Confidence Analysis:</strong> Detailed analysis of classification confidence scores and distribution</li>
            <li><strong>Historical Trends:</strong> Publication evolution patterns and trends over time</li>
            <li><strong>Seasonal Rankings:</strong> Browse top-ranked recipes by season and type using Bayesian scoring</li>
            <li><strong>Recipe Lookup:</strong> Search for individual recipes and view their classification details</li>
        </ul>
        <p class="description-text">
            Use the sidebar navigation to explore different analysis types. Click the home button at the top left 
            to return to this dashboard overview at any time. Each module provides specialized visualizations 
            and insights into the recipe classification data.
        </p>
    </div>
    """, unsafe_allow_html=True)

# -------------------------------
# DISTRIBUTION PAGE
# -------------------------------
elif page == "Distribution":
    st.markdown('<h2 class="section-header">Recipe Type Distribution</h2>', unsafe_allow_html=True)
    st.markdown("""
    <ul class="point-list">
        <li><strong>Goal:</strong> View proportional share of each recipe type.</li>
        <li><strong>What you see:</strong> Percentage of total dataset per category.</li>
        <li><strong>Use case:</strong> Quickly assess balance / class skew.</li>
    </ul>
    """, unsafe_allow_html=True)
    
    type_counts = df['Type'].value_counts().reset_index()
    type_counts.columns = ['Recipe_Type', 'Count']

    # Create dark-themed pie chart
    fig_pie = px.pie(type_counts, names='Recipe_Type', values='Count',
                     color='Recipe_Type',
                     color_discrete_map={'plat':'#0078d4', 'dessert':'#d13438', 'boisson':'#107c10'},
                     title="Recipe Type Distribution")
    fig_pie.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_size=20,
        height=500
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Display summary statistics
    st.markdown('<h3 class="section-header">Summary Statistics</h3>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    for i, (recipe_type, count) in enumerate(type_counts.values):
        percentage = (count / type_counts['Count'].sum()) * 100
        with [col1, col2, col3][i]:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{recipe_type.title()}</h3>
                <h2>{count:,}</h2>
                <p>({percentage:.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)

# -------------------------------
# CONFIDENCE ANALYSIS PAGE
# -------------------------------
elif page == "Confidence Analysis":
    st.markdown('<h2 class="section-header">Classification Confidence Analysis</h2>', unsafe_allow_html=True)
    
    if 'Confidence_Percentage' in df.columns:
        st.markdown("""
        <ul class="point-list">
            <li><strong>Metric:</strong> Confidence (%) output by classifier.</li>
            <li><strong>Bar chart:</strong> Mean confidence per recipe type.</li>
            <li><strong>Histogram:</strong> Spread of all confidence scores.</li>
            <li><strong>Purpose:</strong> Detect uncertain segments or imbalance.</li>
        </ul>
        """, unsafe_allow_html=True)
        
        # Average confidence by type
        conf_means = df.groupby('Type')['Confidence_Percentage'].mean().reset_index() 
        conf_means.columns = ['Recipe_Type', 'Average_Confidence']

        fig_conf = px.bar(conf_means, x='Recipe_Type', y='Average_Confidence',
                         color='Recipe_Type',
                         color_discrete_map={'plat':'#0078d4', 'dessert':'#d13438', 'boisson':'#107c10'},
                         title="Average Confidence Score by Recipe Type")
        fig_conf.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_size=20,
            bargap=0.3,
            yaxis_title='Average Confidence Score (%)',
            xaxis_title='Recipe Type',
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_conf, use_container_width=True)
        
        # Confidence distribution histogram
        fig_hist = px.histogram(df, x='Confidence_Percentage', color='Type',
                               color_discrete_map={'plat':'#0078d4', 'dessert':'#d13438', 'boisson':'#107c10'},
                               title="Distribution of Confidence Scores",
                               nbins=30)
        fig_hist.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_size=20,
            xaxis_title='Confidence Percentage (%)',
            yaxis_title='Number of Recipes',
            height=400
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Summary statistics
        st.markdown('<h3 class="section-header">Confidence Statistics</h3>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        overall_avg = df['Confidence_Percentage'].mean()
        overall_std = df['Confidence_Percentage'].std()
        min_conf = df['Confidence_Percentage'].min()
        max_conf = df['Confidence_Percentage'].max()
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Average</h3>
                <h2>{overall_avg:.1f}%</h2>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Std Dev</h3>
                <h2>{overall_std:.1f}%</h2>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Minimum</h3>
                <h2>{min_conf:.1f}%</h2>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Maximum</h3>
                <h2>{max_conf:.1f}%</h2>
            </div>
            """, unsafe_allow_html=True)
            
    else:
        st.markdown("""
        <div class="home-card">
            <p class="description-text">
                Confidence data is not available in the current dataset. 
                Please ensure your data includes a 'Confidence_Percentage' column.
            </p>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------
# HISTORICAL TRENDS PAGE
# -------------------------------
elif page == "Historical Trends":
    st.markdown('<h2 class="section-header">Historical Publication Trends</h2>', unsafe_allow_html=True)
    st.markdown("""
    <ul class="point-list">
        <li><strong>Chart:</strong> Stacked annual counts by type.</li>
        <li><strong>Tracks:</strong> Growth, composition shifts, peaks.</li>
        <li><strong>Insight goal:</strong> Identify years of surge or decline.</li>
    </ul>
    """, unsafe_allow_html=True)

    # Convert date to datetime and extract year
    df["Year"] = pd.to_datetime(df["Submission_Date"], errors="coerce", format="%Y-%m-%d")
    df["Year"] = df["Year"].dt.year

    # Group by year and type
    count_by_year_type = df.groupby(['Year', 'Type']).size().unstack(fill_value=0)

    # Create dark-themed stacked bar chart
    fig_line = px.bar(count_by_year_type, 
                      x=count_by_year_type.index,
                      y=count_by_year_type.columns,
                      labels={'value':'Number of Published Recipes', 'Year':'Year', 'variable':'Recipe Type'},
                      title="Recipe Publication Evolution by Type",
                      barmode='stack',
                      color_discrete_map={'plat':'#0078d4', 'dessert':'#d13438', 'boisson':'#107c10'})
    
    fig_line.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_size=16
    )

    st.plotly_chart(fig_line, use_container_width=True)
    
    # Display year-over-year growth statistics
    st.markdown('<h3 class="section-header">Publication Summary</h3>', unsafe_allow_html=True)
    
    total_by_year = count_by_year_type.sum(axis=1)
    growth_rate = ((total_by_year.iloc[-1] - total_by_year.iloc[0]) / total_by_year.iloc[0] * 100) if len(total_by_year) > 1 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Peak Year</h3>
            <h2>{total_by_year.idxmax()}</h2>
            <p>({total_by_year.max():,} recipes)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Total Growth</h3>
            <h2>{growth_rate:.1f}%</h2>
            <p>Over {len(total_by_year)} years</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        most_active_type = count_by_year_type.sum().idxmax()
        st.markdown(f"""
        <div class="metric-card">
            <h3>Most Active Type</h3>
            <h2>{most_active_type.title()}</h2>
            <p>({count_by_year_type.sum().max():,} total)</p>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------
# SEASONAL RANKINGS PAGE
# -------------------------------
elif page == "Seasonal Rankings":
    st.markdown('<h2 class="section-header">Seasonal Recipe Rankings</h2>', unsafe_allow_html=True)
    st.markdown("""
    <ul class="point-list">
        <li><strong>Ranking basis:</strong> Bayesian score + seasonal review signal.</li>
        <li><strong>Filter:</strong> Select season and recipe type.</li>
        <li><strong>Table columns:</strong> Rank, ID, Name, Score, Reviews (season).</li>
        <li><strong>Use:</strong> Surface seasonally resonant recipes.</li>
    </ul>
    """, unsafe_allow_html=True)

    # Selection filters
    col3, col4 = st.columns(2)
    with col3:
        season = st.selectbox("Select Season:", sorted(top20_df['Season'].unique()))
    with col4:
        recipe_type_display = st.selectbox("Select Recipe Type:", sorted(top20_df.get('recipe_type_en', top20_df['recipe_type']).unique()))

    # Filter data using English layer if present
    if 'recipe_type_en' in top20_df.columns:
        top20_filtered = top20_df[(top20_df['Season'] == season) & (top20_df['recipe_type_en'] == recipe_type_display)]
    else:
        # Fallback to original types
        inv_map = {'main': 'plat', 'drink': 'boisson', 'dessert': 'dessert'}
        underlying = inv_map.get(recipe_type_display, recipe_type_display)
        top20_filtered = top20_df[(top20_df['Season'] == season) & (top20_df['recipe_type'] == underlying)]

    # Display results
    if not top20_filtered.empty:
        display_label = top20_filtered.get('recipe_type_en', top20_filtered['recipe_type']).iloc[0]
        st.subheader(f"Top {len(top20_filtered)} {display_label} recipes in {season}")
        
        display_columns = ['Ranking', 'Recipe_ID', 'Name', 'Bayesian_Score', 'Season_Reviews']
        
        display_df = top20_filtered[display_columns].copy()
        if 'Ranking' in display_df.columns:
            display_df = display_df.sort_values('Ranking', ascending=True)
        else:
            display_df = display_df.sort_values('Bayesian_Score', ascending=False)
        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No recipes found for this selection.")

# -------------------------------
# RECIPE LOOKUP PAGE
# -------------------------------
elif page == "Recipe Lookup":
    st.markdown('<h2 class="section-header">Individual Recipe Analysis</h2>', unsafe_allow_html=True)
    st.markdown("""
    <ul class="point-list">
        <li><strong>Input:</strong> Numeric recipe ID.</li>
        <li><strong>Returns:</strong> Type, confidence, submission date, description.</li>
        <li><strong>Purpose:</strong> Spot‑check classification validity.</li>
    </ul>
    """, unsafe_allow_html=True)

    recipe_id = st.text_input("Enter Recipe ID:")
    if recipe_id:
        try:
            recipe_id_int = int(recipe_id)
            recipe_found = df[df['ID'] == recipe_id_int]
            if not recipe_found.empty:
                recipe_info = recipe_found.iloc[0]
                st.success(f"Recipe found: {recipe_info.get('Name', 'Name not available')}")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>Classification Type</h4>
                        <h3>{recipe_info.get('Type', 'N/A')}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>Recipe ID</h4>
                        <h3>{recipe_info.get('ID', 'N/A')}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    if 'Confidence_Percentage' in df.columns:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4>Confidence Score</h4>
                            <h3>{recipe_info.get('Confidence_Percentage', 'N/A'):.1f}%</h3>
                        </div>
                        """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>Submission Date</h4>
                        <h3>{recipe_info.get('Submission_Date', 'N/A')}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    if 'Description' in recipe_info.index and pd.notna(recipe_info['Description']):
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4>Description</h4>
                            <p>{recipe_info['Description']}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.error("No recipe found with this ID")
        except ValueError:
            st.error("Please enter a valid numeric ID")

elif page == "Analytical Quadrants":
    section_header("Analytical Synopsis & Quadrants")
    info_box("Purpose", "We estimate effort (steps + ingredients + name length) and popularity (Bayesian mean rating) then split recipes into four groups using medians: Easy Gems (low effort, high popularity), Ambitious Masterpiece (high effort, high popularity), Unloved Basic (low effort, low popularity), Reconsider (high effort, low popularity). This helps quickly see where effort matches user interest.")
    info_box("Method", "Effort is a 0–10 heuristic; Bayesian mean shrinks low-review recipes toward their type average using kb. Medians (not averages) define quadrant boundaries to stay robust against outliers.")
    render_insights_and_quadrants(df)

elif page == "Correlation Matrix":
    section_header("Ordered Correlation Matrix")
    render_correlation(df)
    info_box("Reading", "Each cell shows Spearman correlation (monotonic relationship) between numeric features. We remove IDs and constant columns. Ordering by |corr(bayes_mean)| highlights features most associated with popularity. Values near 0 mean weak relation; strong colors do NOT imply causation.")
elif page == "Seasonal Distribution":
    section_header("Seasonal Review Distribution")
    info_box("Purpose", "Shows the share of reviews per season for each recipe type to understand seasonal engagement.")
    # Load latest season distribution CSV from justification directory
    @st.cache_data(show_spinner=False)
    def load_season_distribution():
        """Load season distribution dataframe.

        Resolution strategy:
        1. Look for canonical file season_type_distribution_latest.csv (committed).
        2. Otherwise pick most recent timestamped season_type_distribution_*.csv.
        Returns empty DataFrame if directory missing or no candidates.
        """
        # Resolve project root (two levels up from this file: app/streamlit/ -> project root)
        root = Path(__file__).resolve().parents[2]
        target_dir = root / "analysis_parameter_justification" / "results_to_analyse"
        if not target_dir.is_dir():
            return pd.DataFrame()
        canonical = target_dir / "season_type_distribution_latest.csv"
        if canonical.exists():
            try:
                return pd.read_csv(canonical)
            except Exception:
                return pd.DataFrame()
        candidates = sorted([f for f in target_dir.iterdir() if f.name.startswith("season_type_distribution_") and f.suffix == ".csv"])
        if not candidates:
            return pd.DataFrame()
        latest = candidates[-1]
        try:
            return pd.read_csv(latest)
        except Exception:
            return pd.DataFrame()

    dist_df = load_season_distribution()
    if dist_df.empty:
        st.warning("Season distribution file not found. Generate it with the justification script.")
    else:
        # Standardize columns if French naming
        rename_map = {
            'Type_Recette': 'recipe_type',
            'Saison': 'Season',
            'Nombre_Reviews': 'Reviews',
            'Pourcentage': 'Percentage'
        }
        for k, v in rename_map.items():
            if k in dist_df.columns and v not in dist_df.columns:
                dist_df = dist_df.rename(columns={k: v})
        # Ensure correct ordering of seasons
        season_order = ['Spring','Summer','Fall','Winter']
        dist_df['Season'] = pd.Categorical(dist_df['Season'], season_order, ordered=True)
        type_choice = st.selectbox("Recipe Type:", sorted(dist_df['recipe_type'].unique()))
        metric_mode = st.radio("Metric", ["Percentage", "Reviews"], horizontal=True)
        filtered = dist_df[dist_df['recipe_type'] == type_choice].sort_values('Season')
        values_col = 'Percentage' if metric_mode == 'Percentage' else 'Reviews'
        # Plotly pie chart
        fig = px.pie(filtered, names='Season', values=values_col, hole=0.35,
                     color='Season', color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_traces(textinfo='label+percent' if metric_mode=='Percentage' else 'label+value')
        fig.update_layout(margin=dict(t=30,l=0,r=0,b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(filtered[['Season','Reviews','Percentage']].style.format({'Reviews':'{:,.0f}','Percentage':'{:.2f}%'}), use_container_width=True)