"""Unified Streamlit application.

This file replaces conflicted merge versions, providing a clean, resilient
dashboard for recipe classification analysis.
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px


st.markdown(
    """
    <style>
        .stApp {background-color:#1e1e1e;color:#ffffff;font-family:'Segoe UI',sans-serif;}
        .main-header {font-size:2.4rem;font-weight:600;text-align:center;margin-bottom:1.5rem;border-bottom:2px solid #444;padding-bottom:.75rem;}
        .section-header {font-size:1.6rem;font-weight:500;margin-top:1.5rem;margin-bottom:.75rem;border-left:4px solid #0078d4;padding-left:.75rem;}
        .description-text {font-size:.95rem;line-height:1.55;color:#cccccc;margin-bottom:1.2rem;}
        .home-card,.metric-card {background:#2d2d2d;border:1px solid #444;border-radius:10px;padding:1.25rem;margin:.75rem 0;}
        .metric-card {border-left:4px solid #0078d4;}
        div[data-testid="stSidebar"] .stButton>button {background:#2d2d2d;border:1px solid #4A4A4A;border-radius:8px;padding:10px 14px;margin:4px 0;color:#fff;font-weight:500;transition:.25s all;width:100%;text-align:left;}
        div[data-testid="stSidebar"] .stButton>button:hover {background:#0078d4;border-color:#0078d4;transform:translateX(4px);}
        div[data-testid="stSidebar"] .element-container:first-of-type .stButton>button {background:linear-gradient(135deg,#d13438,#b12a35);border:2px solid #d13438;border-radius:50%;width:60px;height:60px;font-size:24px;margin:0 auto 16px;display:block;}
        .nav-header {font-size:19px;font-weight:600;margin-bottom:16px;text-align:center;border-bottom:2px solid #0078d4;padding-bottom:8px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Page configuration
st.set_page_config(
    page_title="Recipe Classification Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    return df

@st.cache_data(show_spinner=False)
def load_data():
    # Main classified recipes dataset.
    df = _safe_read_csv("data/interim/recipes_classified.csv")
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
            tmp['recipe_type'] = rtype
            ranking_dfs.append(tmp)
    if ranking_dfs:
        top20_df = pd.concat(ranking_dfs, ignore_index=True)
    else:
        st.warning("No ranking files loaded; Seasonal Rankings page will be empty.")
        top20_df = pd.DataFrame(columns=['Ranking','Recipe_ID','Name','Bayesian_Score','Season_Reviews','Season','recipe_type'])

    top20_df = _standardize_top20_columns(top20_df)
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
    ("🔍", "Recipe Lookup", "Search individual recipes")
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
    <p class="description-text">
        This pie chart shows the proportional distribution of recipe types in the dataset.
        Each segment represents the percentage of recipes in each category (plat, dessert, boisson).
    </p>
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
        <p class="description-text">
            This analysis examines the confidence levels of the classification algorithm.
            Higher confidence scores indicate greater certainty in type assignments.
        </p>
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
    <p class="description-text">
        This analysis reveals how recipe publication patterns have evolved over time. 
        The stacked bar chart shows growth trends, seasonal preferences, and publication volume variations 
        that may correlate with food trends or external events.
    </p>
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
    <p class="description-text">
        Explore the highest-rated recipes by season and type using our Bayesian scoring system. 
        Rankings consider review quality, quantity, and seasonal relevance to identify top performers.
    </p>
    """, unsafe_allow_html=True)

    # Selection filters
    col3, col4 = st.columns(2)
    with col3:
        season = st.selectbox("Select Season:", top20_df['Season'].unique())
    with col4:
        recipe_type = st.selectbox("Select Recipe Type:", ["plat", "dessert", "boisson"])

    # Filter data
    top20_filtered = top20_df[(top20_df['Season'] == season) & (top20_df['recipe_type'] == recipe_type)]

    # Display results
    if not top20_filtered.empty:
        st.subheader(f"Top 20 {top20_filtered['recipe_type'].iloc[0]} recipes in {season}")
        
        display_columns = ['Ranking', 'Recipe_ID', 'Name', 'Bayesian_Score', 'Season_Reviews']
        
        st.dataframe(
            top20_filtered[display_columns].sort_values(by='Bayesian_Score', ascending=False), 
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
    <p class="description-text">
        Search for specific recipes by ID to view detailed classification information, 
        confidence scores, and metadata. Useful for verifying classification results 
        and understanding algorithm decisions.
    </p>
    """, unsafe_allow_html=True)

    recipe_id = st.text_input("Enter Recipe ID:")

    if recipe_id:
        try:
            recipe_id_int = int(recipe_id)
            recipe_found = df[df['ID'] == recipe_id_int]
            
            if not recipe_found.empty:
                recipe_info = recipe_found.iloc[0]
                st.success(f"Recipe found: {recipe_info.get('Name', 'Name not available')}")
                
                # Display information in cards
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
            st.error("Please enter a valid numeric ID")