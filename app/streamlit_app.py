import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# -------------------------------
# 1️⃣ Charger les fichiers CSV
# -------------------------------
df = pd.read_csv("recipes_classified_final.csv")

# Récupération des top30 par type en ajoutant la colonne du type
top30_boissons_df = pd.read_csv("top_30_boissons_par_saison.csv") 
top30_boissons_df['type_df'] = 'boisson'
top30_plats_df = pd.read_csv("top_30_plats_par_saison.csv")  
top30_plats_df['type_df'] = 'plat'
top30_desserts_df = pd.read_csv("top_30_desserts_par_saison.csv")
top30_desserts_df['type_df'] = 'dessert'
# Concaténer tous les DataFrames des top 30 en un seul DataFrame
top30_df = pd.concat([top30_boissons_df, top30_plats_df, top30_desserts_df], ignore_index=True)

st.set_page_config(page_title="Mangetamain: Analyse des types de recettes publiées par les utilisateurs", layout="wide")
st.title("🍽 Analyse des types de recettes publiées par les utilisateurs")

# -------------------------------
# 2️⃣ Répartition des types et indices de confiance
# -------------------------------
st.header("Répartition totale des types de recettes")
type_counts = df['type'].value_counts().reset_index() # Comptage des occurences de chaque type
type_counts.columns = ['Type', 'Nombre']

# Création d'un graphique en camembert de la répartition des types
fig_pie = px.pie(type_counts, names='Type', values='Nombre',
                 color='Type',
                 color_discrete_map={'plat':'#636EFA', 'dessert':'#EF553B', 'boisson':'#00CC96'},
                 hole=0.4, 
                 title="Répartition des types de recettes")
fig_pie.update_layout(legend=dict(title="Type"))

# Calcul de la moyenne des indices de confiance par type
conf_means = df.groupby('type')['conf_%'].mean().reset_index() 
conf_means.columns = ['Type', 'Confiance moyenne (%)']

# Création d'un histogramme affichant la moyenne des indices de confiance par type
fig_hist = px.histogram(conf_means, x='Type', y='Confiance moyenne (%)',
                 color='Type',
                 color_discrete_map={'plat':'#636EFA', 'dessert':'#EF553B', 'boisson':'#00CC96'},
                 title="Moyenne des indices de confiance par type",
                 labels={'Confiance moyenne (%)': 'Indice de confiance moyen (%)'})
fig_hist.update_layout(bargap=0.2, yaxis_title='Indice de confiance moyen (%)')

# Affichage des deux graphiques côte à côte
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_pie, use_container_width=True)
with col2:
    st.plotly_chart(fig_hist, use_container_width=True)

# -------------------------------
# 3️⃣ Historique des types par année
# -------------------------------
st.header("Historique des types de recettes publiées par année")

# Conversion de la date en datetime dans une nouvelle colonne
df["year"] = pd.to_datetime(df["submitted"], errors="coerce", dayfirst=True)

# Extraire l’année
df["year"] = df["year"].dt.year

# Regrouper par année et type, puis compter les occurrences
count_by_year_type = df.groupby(['year', 'type']).size().unstack(fill_value=0)

# Création du graphique en barres empilées
fig_line = px.bar(count_by_year_type, 
                  x=count_by_year_type.index,
                  y=count_by_year_type.columns,
                  labels={'value':'Nombre de recettes publiées', 'year':'Année', 'variable':'Type de recette'},
                  title="Évolution du nombre de recettes par type au fil des années",
                  barmode = 'stack',
                  color_discrete_map={'plat':'#636EFA', 'dessert':'#EF553B', 'boisson':'#00CC96'})

st.plotly_chart(fig_line, use_container_width=True)

# -------------------------------
# 4️⃣ Recherche de recette par ID
# -------------------------------
st.header("🔎 Recherche d'une recette par ID")

recipe_id = st.text_input("Entrez l'ID de la recette :")

if recipe_id:
    try:
        recipe_id_int = int(recipe_id)
        recipe_found = df[df['id'] == recipe_id_int]
        
        if not recipe_found.empty:
            recipe_info = recipe_found.iloc[0]
            st.success(f"Recette trouvée : {recipe_info.get('name', 'Nom non disponible')}")
            
            # Affichage des informations de la recette
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Type :** {recipe_info.get('type', 'N/A')}")
                st.write(f"**ID :** {recipe_info.get('id', 'N/A')}")
                st.write(f"**Confiance :** {recipe_info.get('conf_%', 'N/A')}%")
            with col2:
                st.write(f"**Date de soumission :** {recipe_info.get('submitted', 'N/A')}")
                if 'description' in recipe_info.index:
                    st.write(f"**Description :** {recipe_info['description']}")
        else:
            st.error("Aucune recette trouvée avec cet ID")
            
    except ValueError:
        st.error("Veuillez entrer un ID valide (nombre entier)")
    

# -------------------------------
# 5️⃣ Top 30 par année et type avec graphique
# -------------------------------
st.header("🏆 Top 30 des recettes par année et type")

# Boutons de sélection pour la saison et le type recherchés
col3, col4 = st.columns(2)
with col3:
    season = st.selectbox("Sélectionnez la saison :", top30_df['Saison'].unique())
with col4:
    recipe_type = st.selectbox("Sélectionnez le type :", ["plat", "dessert", "boisson"])

# Sélection du type et du saison pour le top30 des recettes
top30_filtered = top30_df[(top30_df['Saison'] == season) & (top30_df['type_df'] == recipe_type)]

# Affichage du tableau du top 30
if not top30_filtered.empty:
    st.subheader(f"Top 30 des {top30_filtered['type_df'].iloc[0]} en {season}")
    st.dataframe(top30_filtered[['recipe_id','name', 'Nb_Reviews_Saison','Score_Final']].sort_values(by='Score_Final', ascending=False), hide_index=True,
                 use_container_width=True)
else:
    st.info("Aucune recette pour cette sélection.")