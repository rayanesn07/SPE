import streamlit as st
import pandas as pd
import plotly.express as px
import joblib
from sklearn.preprocessing import OrdinalEncoder
import os
import numpy as np


# =========================
# 1. Chargement des données (VERSION CORRIGÉE)
# =========================
@st.cache_data(ttl=60)  # Cache expire après 60 secondes
def load_data():
    df = pd.read_excel("data.xlsx")
    if "Date_Creation" in df.columns:
        df["Date_Creation"] = pd.to_datetime(df["Date_Creation"])
    return df

df = load_data()



# =========================
# 2. Configuration de la page
# =========================
st.set_page_config(
    page_title="Dashboard Commandes", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Supprimer espace inutile en haut
# =========================
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# =========================
# 3. Dictionnaire pour labels jolis
# =========================
pretty_labels = {
    "Date_Creation": "Date De Creation",
    "Etat_Commande": "État De Commande",
    "Societe_Livraison": "Société De Livraison"
}

def prettify(col):
    return pretty_labels.get(col, col.replace("_", " "))

# =========================
# 4. Navigation dans la sidebar native
# =========================

# Initialiser l'état de la page dans session_state
if 'page' not in st.session_state:
    st.session_state.page = 'confirmation'

# Utiliser la sidebar native de Streamlit
with st.sidebar:
    st.header("Navigation")
    
    # Ajouter du CSS personnalisé pour changer les couleurs
    st.markdown("""
        <style>
        /* Style pour tous les boutons - avec une spécificité plus élevée */
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div.stButton > button,
        div.stButton > button {
            background-color: white !important;
            color: black !important;
            font-weight: 800 !important;
            border: 1px solid #ddd !important;
        }
        
        /* Style pour le bouton au survol */
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div.stButton > button:hover,
        div.stButton > button:hover {
            background-color: #e0e0e0 !important;
            color: black !important;
            font-weight: 800 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Boutons de navigation
    if st.button("Dashboard Confirmation", use_container_width=True):
        st.session_state.page = 'confirmation'

    if st.button("Dashboard Livraison et Stock", use_container_width=True):
        st.session_state.page = 'livraison'
    
    if st.button("Prédiction de fausses commandes", use_container_width=True):
        st.session_state.page = 'prediction'

# =========================
# 5. Fonctions utilitaires réutilisables
# =========================
def chart_card(df, col_name, title=""):
    with st.container():
        fig = px.pie(
            df,
            names=col_name,
            title="",
            hole=0.4
        )
        fig.update_layout(
            height=450,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            legend_title=prettify(col_name)
        )

        st.markdown(
            f"""
            <div style="
                border:1px solid #ddd;
                border-radius:12px;
                padding:15px;
                margin:10px 0;
                box-shadow:2px 2px 8px rgba(0,0,0,0.08);
                background-color:white;
            ">
            <h4 style="text-align:center; color:#333;">{title}</h4>
            """,
            unsafe_allow_html=True
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# =========================
# 6. Contenu de la page Confirmation (page par défaut)
# =========================
if st.session_state.page == 'confirmation':
    st.title("Dashboard Confirmation")
    
    # KPIs globaux
    total_cmds = len(df)
    confirmed = len(df[df["Etat_Commande"] == "Confirmée"])
    cancelled = len(df[df["Etat_Commande"] == "Annulée"])
    pending = len(df[df["Etat_Commande"] == "En confirmation"])
    
    st.markdown(
        """
        <style>
        div[data-testid="stMetricValue"] {
            font-size: 36px;
            font-weight: bold;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 22px;
        }
        div[data-testid="stMetric"] {
            text-align: center;
            background-color: #1E1E1E;
            padding: 12px;
            border-radius: 12px;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.4);
        }
        div[data-testid="stMetric"] label, 
        div[data-testid="stMetric"] p, 
        div[data-testid="stMetricLabel"], 
        div[data-testid="stMetricLabel"] span {
            font-size: 20px !important;
            font-weight: 700 !important;
            color: white !important;
            text-align: center !important;
            display: block !important;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"], 
        div[data-testid="stMetricValue"] span {
            font-size: 42px !important;
            font-weight: bold !important;
            color: white !important;
            text-align: center !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    confirmed = len(df[df["Etat_Commande"] == "Confirmée"])
    cancelled = len(df[df["Etat_Commande"] == "Annulée"])
    taux_confirmation = confirmed / (confirmed + cancelled) 

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(" Total commandes", total_cmds)
    col2.metric(" Confirmées", confirmed)
    col3.metric(" Annulées", cancelled)
    col4.metric(" En confirmation", pending)
    col5.metric(" Taux confirmation", f"{taux_confirmation:.1%}")

    # =========================
    # 7. Fonction carte avec filtre date global (pour pie charts)
    # =========================

    # Définir le filtre global pour les pie charts
    if "Date_Creation" in df.columns:
        min_date = df["Date_Creation"].min()
        max_date = df["Date_Creation"].max()
        pie_date_range = st.date_input(
            "Choisir la période :",
            [min_date, max_date],
            key="pie_filter"
        )
        if len(pie_date_range) == 2:
            df_pie = df[
                (df["Date_Creation"] >= pd.to_datetime(pie_date_range[0])) &
                (df["Date_Creation"] <= pd.to_datetime(pie_date_range[1]))
            ]
        else:
            df_pie = df.copy()
    else:
        df_pie = df.copy()

    # =========================
    # 8. Organisation des cartes (2x2)
    # =========================
    row1_col1, row1_col2 = st.columns(2)  
    row2_col1, row2_col2 = st.columns(2)

    with row1_col1:
        chart_card(df, "Etat_Commande", "État des commandes")
    with row1_col2:
        chart_card(df, "Boutique", "Commandes par boutique")

    col1, col2 = st.columns(2)

    with col1:
        # Répartition des commandes par Source
        if "Source" in df_pie.columns:
            chart_card(df_pie, "Source", title="Répartition des commandes par Source")

    with col2:
        # Répartition des commandes Confirmées par Shift
        if "Shift" in df_pie.columns and "Etat_Commande" in df_pie.columns:
            df_conf_shift = df_pie[df_pie["Etat_Commande"] == "Confirmée"].copy()
            if not df_conf_shift.empty:
                chart_card(df_conf_shift, "Shift", title="Confirmées : Matin vs Soir")

    # =========================
    # 9. Graphiques d'évolution (avec filtre global)
    # =========================

    if "Date_Creation" in df.columns:
        df["Annee"] = df["Date_Creation"].dt.year
        df["Mois"] = df["Date_Creation"].dt.to_period("M").astype(str)

        st.subheader("Évolution des commandes")

        mode = st.radio("Type d'analyse :", ["Mensuelle", "Annuelle"], horizontal=True)

        # ===== Mode Mensuel =====
        if mode == "Mensuelle":
            mois_dispo = sorted(df["Mois"].unique())
            mois_select = st.selectbox("Choisir un mois :", mois_dispo, key="mois_global")

            df_mois = df[df["Mois"] == mois_select]

            # Créer deux colonnes pour les graphiques
            evo_col1, evo_col2 = st.columns(2)

            # Graphique d'évolution des commandes (gauche)
            with evo_col1:
                df_grouped = df_mois.groupby(
                    [df_mois["Date_Creation"].dt.day, "Etat_Commande"]
                ).size().reset_index(name="Nombre De Commandes")
                df_grouped.rename(columns={"Date_Creation": "Jour"}, inplace=True)

                fig_total = px.bar(
                    df_grouped,
                    x="Jour",
                    y="Nombre De Commandes",
                    color="Etat_Commande",
                    title=f"Évolution des commandes - {mois_select}",
                    barmode="stack",
                    category_orders={"Etat_Commande": ["Confirmée", "En confirmation", "Annulée"]},
                    color_discrete_map={
                        "Confirmée": "#4DA6FF",
                        "En confirmation": "#FFD966",
                        "Annulée": "#FF4C4C"
                    }
                )
                fig_total.update_layout(height=450)
                st.plotly_chart(fig_total, use_container_width=True)

            # Graphique des fausses commandes par source (droite)
            with evo_col2:
                # Vérifier si la colonne existe avant de filtrer
                if "Fausse_Commande" in df_mois.columns:
                    # Filtrer seulement les fausses commandes
                    df_fausses = df_mois[df_mois["Fausse_Commande"] == 1].copy()
                    
                    if not df_fausses.empty and "Source" in df_fausses.columns:
                        df_fausses_grouped = df_fausses.groupby(
                            [df_fausses["Date_Creation"].dt.day, "Source"]
                        ).size().reset_index(name="Nombre De Fausses Commandes")
                        df_fausses_grouped.rename(columns={"Date_Creation": "Jour"}, inplace=True)

                        fig_fausses = px.bar(
                            df_fausses_grouped,
                            x="Jour",
                            y="Nombre De Fausses Commandes",
                            color="Source",
                            title=f"Fausses commandes par Source - {mois_select}",
                            barmode="stack"
                        )
                        fig_fausses.update_layout(height=450)
                        st.plotly_chart(fig_fausses, use_container_width=True)
                    else:
                        st.info("Aucune fausse commande trouvée pour cette période")
                else:
                    st.info("Colonne 'Fausse_Commande' non disponible")

        # ===== Mode Annuel =====
        else:
            annees_dispo = sorted(df["Annee"].unique())
            annee_select = st.selectbox("Choisir une année :", annees_dispo, key="annee_global")

            df_annee = df[df["Annee"] == annee_select]

            # Créer deux colonnes pour les graphiques
            evo_col1, evo_col2 = st.columns(2)

            # Graphique d'évolution des commandes (gauche)
            with evo_col1:
                df_grouped = df_annee.groupby(
                    [df_annee["Date_Creation"].dt.month, "Etat_Commande"]
                ).size().reset_index(name="Nombre De Commandes")
                df_grouped.rename(columns={"Date_Creation": "Mois"}, inplace=True)

                fig_total = px.bar(
                    df_grouped,
                    x="Mois",
                    y="Nombre De Commandes",
                    color="Etat_Commande",
                    title=f"Évolution des commandes - {annee_select}",
                    barmode="stack",
                    category_orders={"Etat_Commande": ["Confirmée", "En confirmation", "Annulée"]},
                    color_discrete_map={
                        "Confirmée": "#4DA6FF",
                        "En confirmation": "#FFD966",
                        "Annulée": "#FF4C4C"
                    }
                )
                fig_total.update_layout(height=450)
                st.plotly_chart(fig_total, use_container_width=True)

            # Graphique des fausses commandes par source (droite)
            with evo_col2:
                # Vérifier si la colonne existe avant de filtrer
                if "Fausse_Commande" in df_annee.columns:
                    # Filtrer seulement les fausses commandes
                    df_fausses = df_annee[df_annee["Fausse_Commande"] == 1].copy()
                    
                    if not df_fausses.empty and "Source" in df_fausses.columns:
                        df_fausses_grouped = df_fausses.groupby(
                            [df_fausses["Date_Creation"].dt.month, "Source"]
                        ).size().reset_index(name="Nombre De Fausses Commandes")
                        df_fausses_grouped.rename(columns={"Date_Creation": "Mois"}, inplace=True)

                        fig_fausses = px.bar(
                            df_fausses_grouped,
                            x="Mois",
                            y="Nombre De Fausses Commandes",
                            color="Source",
                            title=f"Fausses commandes par Source - {annee_select}",
                            barmode="stack"
                        )
                        fig_fausses.update_layout(height=450)
                        st.plotly_chart(fig_fausses, use_container_width=True)
                    else:
                        st.info("Aucune fausse commande trouvée pour cette période")
                else:
                    st.info("Colonne 'Fausse_Commande' non disponible")

# ==============================================================================================================================================
# 10. Contenu de la page Livraison et Stock
# ==============================================================================================================================================
elif st.session_state.page == 'livraison':
    st.title("Dashboard Livraison et Stock")
    
    # KPIs pour la livraison
    livree = len(df[df["Etat_Livraison"] == "Livrée"])
    expediee = len(df[df["Etat_Stock"] == "Expédiée"])
    retour = len(df[df["Etat_Livraison"] == "Retour"])
    en_livraison = len(df[df["Etat_Livraison"] == "En livraison"])
    preparation_stock = len(df[df["Etat_Livraison"] == "Preparation Stock"])
    
    # Calcul du taux de livraison
    taux_livraison = livree / (livree + retour) if (livree + retour) > 0 else 0

    st.markdown(
        """
        <style>
        div[data-testid="stMetricValue"] {
            font-size: 36px;
            font-weight: bold;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 22px;
        }
        div[data-testid="stMetric"] {
            text-align: center;
            background-color: #1E1E1E;
            padding: 12px;
            border-radius: 12px;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.4);
        }
        div[data-testid="stMetric"] label, 
        div[data-testid="stMetric"] p, 
        div[data-testid="stMetricLabel"], 
        div[data-testid="stMetricLabel"] span {
            font-size: 20px !important;
            font-weight: 700 !important;
            color: white !important;
            text-align: center !important;
            display: block !important;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"], 
        div[data-testid="stMetricValue"] span {
            font-size: 42px !important;
            font-weight: bold !important;
            color: white !important;
            text-align: center !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Expédiées", expediee)
    col2.metric("Livrées", livree)
    col3.metric("Retours", retour)
    col4.metric("En Livraison", en_livraison)
    col5.metric("Taux Livraison", f"{taux_livraison:.1%}")

    # =========================
    # Filtre date global pour les pie charts
    # =========================
    if "Date_Creation" in df.columns:
        min_date = df["Date_Creation"].min()
        max_date = df["Date_Creation"].max()
        pie_date_range = st.date_input(
            "Choisir la période :",
            [min_date, max_date],
            key="pie_livraison"
        )
        if len(pie_date_range) == 2:
            df_pie = df[
                (df["Date_Creation"] >= pd.to_datetime(pie_date_range[0])) &
                (df["Date_Creation"] <= pd.to_datetime(pie_date_range[1]))
            ]
        else:
            df_pie = df.copy()
    else:
        df_pie = df.copy()

    # =========================
    # Matrice 2x2 - Graphiques camembert
    # =========================
    row1_col1, row1_col2 = st.columns(2)
    
    with row1_col1:
    # Pie chart État des commandes stock
        if "Etat_Livraison" in df_pie.columns:
        # Filtrer les lignes où Etat_Livraison n'est pas vide
             df_filtered = df_pie[df_pie["Etat_Livraison"].notna() & (df_pie["Etat_Livraison"] != "")]
             chart_card(df_filtered, "Etat_Livraison", "État des commandes stock")
    
    with row1_col2:
        # Pie chart Sociétés de livraison (commandes livrées)
        if "Societe_Livraison" in df_pie.columns and "Etat_Livraison" in df_pie.columns:
            commandes_livrees = df_pie[df_pie["Etat_Livraison"] == "Livrée"]
            if not commandes_livrees.empty:
                chart_card(commandes_livrees, "Societe_Livraison", "Livraisons par société")

    # =========================
    # Graphiques d'évolution
    # =========================
    if "Date_Creation" in df.columns:
        df["Annee"] = df["Date_Creation"].dt.year
        df["Mois"] = df["Date_Creation"].dt.to_period("M").astype(str)

        st.subheader("Évolution des livraisons")

        mode = st.radio("Type d'analyse :", ["Mensuelle", "Annuelle"], horizontal=True, key="mode_livraison")

        # ===== Mode Mensuel =====
        if mode == "Mensuelle":
            mois_dispo = sorted(df["Mois"].unique())
            mois_select = st.selectbox("Choisir un mois :", mois_dispo, key="mois_livraison")

            df_mois = df[df["Mois"] == mois_select]

            # Créer deux colonnes pour les graphiques
            evo_col1, evo_col2 = st.columns(2)

            # Graphique empilé des états de livraison (gauche)
            with evo_col1:
                if "Etat_Livraison" in df_mois.columns:
                    df_grouped = df_mois.groupby(
                        [df_mois["Date_Creation"].dt.day, "Etat_Livraison"]
                    ).size().reset_index(name="Nombre De Commandes")
                    df_grouped.rename(columns={"Date_Creation": "Jour"}, inplace=True)

                    fig_empile = px.bar(
                        df_grouped,
                        x="Jour",
                        y="Nombre De Commandes",
                        color="Etat_Livraison",
                        title=f"Évolution des livraisons - {mois_select}",
                        barmode="stack"
                    )
                    fig_empile.update_layout(height=450)
                    st.plotly_chart(fig_empile, use_container_width=True)

            # Graphique des retours par société (droite)
            with evo_col2:
                if "Societe_Livraison" in df_mois.columns and "Etat_Livraison" in df_mois.columns:
                    retours_data = df_mois[df_mois["Etat_Livraison"] == "Retour"]
                    if not retours_data.empty:
                        df_retours_grouped = retours_data.groupby(
                            [retours_data["Date_Creation"].dt.day, "Societe_Livraison"]
                        ).size().reset_index(name="Nombre De Retours")
                        df_retours_grouped.rename(columns={"Date_Creation": "Jour"}, inplace=True)

                        fig_retours = px.bar(
                            df_retours_grouped,
                            x="Jour",
                            y="Nombre De Retours",
                            color="Societe_Livraison",
                            title=f"Retours par société - {mois_select}",
                            barmode="stack"
                        )
                        fig_retours.update_layout(height=450)
                        st.plotly_chart(fig_retours, use_container_width=True)

        # ===== Mode Annuel =====
        else:
            annees_dispo = sorted(df["Annee"].unique())
            annee_select = st.selectbox("Choisir une année :", annees_dispo, key="annee_livraison")

            df_annee = df[df["Annee"] == annee_select]

            # Créer deux colonnes pour les graphiques
            evo_col1, evo_col2 = st.columns(2)

            # Graphique empilé des états de livraison (gauche)
            with evo_col1:
                if "Etat_Livraison" in df_annee.columns:
                    df_grouped = df_annee.groupby(
                        [df_annee["Date_Creation"].dt.month, "Etat_Livraison"]
                    ).size().reset_index(name="Nombre De Commandes")
                    df_grouped.rename(columns={"Date_Creation": "Mois"}, inplace=True)

                    fig_empile = px.bar(
                        df_grouped,
                        x="Mois",
                        y="Nombre De Commandes",
                        color="Etat_Livraison",
                        title=f"Évolution des livraisons - {annee_select}",
                        barmode="stack"
                    )
                    fig_empile.update_layout(height=450)
                    st.plotly_chart(fig_empile, use_container_width=True)

            # Graphique des retours par société (droite)
            with evo_col2:
                if "Societe_Livraison" in df_annee.columns and "Etat_Livraison" in df_annee.columns:
                    retours_data = df_annee[df_annee["Etat_Livraison"] == "Retour"]
                    if not retours_data.empty:
                        df_retours_grouped = retours_data.groupby(
                            [retours_data["Date_Creation"].dt.month, "Societe_Livraison"]
                        ).size().reset_index(name="Nombre De Retours")
                        df_retours_grouped.rename(columns={"Date_Creation": "Mois"}, inplace=True)

                        fig_retours = px.bar(
                            df_retours_grouped,
                            x="Mois",
                            y="Nombre De Retours",
                            color="Societe_Livraison",
                            title=f"Retours par société - {annee_select}",
                            barmode="group"
                        )
                        fig_retours.update_layout(height=450)
                        st.plotly_chart(fig_retours, use_container_width=True)

    # =========================
    # Carte de l'Algérie pour les retours
    # =========================
    st.subheader("Carte des retours par wilaya")
    
    # Filtre spécifique pour la carte
    if "Date_Creation" in df.columns:
        min_date_map = df["Date_Creation"].min()
        max_date_map = df["Date_Creation"].max()
        map_date_range = st.date_input(
            "Choisir la période pour la carte :",
            [min_date_map, max_date_map],
            key="map_livraison"
        )
        if len(map_date_range) == 2:
            df_map = df[
                (df["Date_Creation"] >= pd.to_datetime(map_date_range[0])) &
                (df["Date_Creation"] <= pd.to_datetime(map_date_range[1]))
            ]
        else:
            df_map = df.copy()
    else:
        df_map = df.copy()

    # Fonction pour créer la carte des retours
    def create_algeria_map_retours(df_map):
        wilaya_coordinates = {
            'Alger': [36.7525, 3.0420], 'Oran': [35.6971, -0.6337], 'Constantine': [36.3650, 6.6147],
            'Annaba': [36.9000, 7.7667], 'Blida': [36.4722, 2.8333], 'Batna': [35.5550, 6.1741],
            'Sétif': [36.1900, 5.4100], 'Tlemcen': [34.8828, -1.3167], 'Béjaïa': [36.7500, 5.0667],
            'Skikda': [36.8667, 6.9000], 'Tizi Ouzou': [36.7167, 4.0500], 'Mostaganem': [35.9333, 0.0833],
            'Msila': [35.6667, 4.5500], 'Sidi Bel Abbès': [35.2000, -0.6333], 'Tiaret': [35.3667, 1.3167],
            'Béchar': [31.6167, -2.2167], 'Tamanrasset': [22.7850, 5.5228], 'Ouargla': [31.9500, 5.3167],
            'Ghardaïa': [32.4833, 3.6667], 'Adrar': [27.8742, -0.2939]
        }
        
        if 'Wilaya' in df_map.columns and 'Etat_Livraison' in df_map.columns:
            retours_map = df_map[df_map["Etat_Livraison"] == "Retour"]
            wilaya_retours = retours_map['Wilaya'].value_counts().reset_index()
            wilaya_retours.columns = ['Wilaya', 'Nombre_Retours']
            
            map_data = []
            for wilaya, count in wilaya_retours.values:
                if wilaya in wilaya_coordinates:
                    lat, lon = wilaya_coordinates[wilaya]
                    map_data.append({
                        'Wilaya': wilaya,
                        'Nombre_Retours': count,
                        'Latitude': lat,
                        'Longitude': lon
                    })
            
            if map_data:
                map_df = pd.DataFrame(map_data)
                fig = px.scatter_mapbox(
                    map_df,
                    lat="Latitude",
                    lon="Longitude",
                    size="Nombre_Retours",
                    color="Nombre_Retours",
                    hover_name="Wilaya",
                    hover_data={"Nombre_Retours": True},
                    size_max=30,
                    zoom=5,
                    height=400,
                    title="Répartition des retours par wilaya",
                    color_continuous_scale=px.colors.sequential.Reds
                )
                fig.update_layout(
                    mapbox_style="open-street-map",
                    margin={"r":0,"t":40,"l":0,"b":0}
                )
                return fig
        return None

    algeria_map_retours = create_algeria_map_retours(df_map)
    if algeria_map_retours:
        st.plotly_chart(algeria_map_retours, use_container_width=True)
    else:
        st.info("Pour afficher la carte des retours, assurez-vous d'avoir les colonnes 'Wilaya' et 'Etat_Livraison' dans vos données.")




# ==============================================================================================================================================# 11. Contenu de la page Prédiction de fausses commandes
# =============================================================================================================================================

elif st.session_state.page == 'prediction':
    st.title("Prédiction de fausses commandes")
    st.write("Importez un fichier Excel contenant les colonnes nécessaires pour obtenir une prédiction.")

    uploaded_file = st.file_uploader("📂 Joindre un fichier Excel", type=["xlsx"])

    if uploaded_file is not None:
        df_uploaded = pd.read_excel(uploaded_file)

        # Colonnes attendues (dans le fichier utilisateur)
        colonnes_attendues = [
            "@ Ip du client",
            "date de creation",
            "nom prenom",
            "numero de telephone",
            "Qte",
            "Wilaya",
            "Commune",
            "SKU d'article",
            "Boutique",
            "montant total"
        ]

        # Mapping vers les colonnes du modèle
        mapping_colonnes = {
            "@ Ip du client": "@_Ip_du_client",
            "nom prenom": "nom_prenom",
            "SKU d'article": "SKU_d_article",   # correction ici
            "date de creation": "date_de_creation",
            "numero de telephone": "numero_de_telephone",
            "montant total": "montant_total"
        }

        if set(df_uploaded.columns) == set(colonnes_attendues):
            st.success("Fichier valide. Prêt pour la prédiction.")

            if st.button("Prédire"):
                try:
                    # Charger modèle + encodeur````````
                    model = joblib.load("lgb_model.joblib")
                    encoder = None
                    if os.path.exists("ordinal_encoder.joblib"):
                        encoder = joblib.load("ordinal_encoder.joblib")

                    # Renommer les colonnes selon le mapping
                    X_new = df_uploaded.rename(columns=mapping_colonnes).copy()

                    # -------- Prétraitement identique à l’entraînement --------
                    # Gérer la colonne date
                    date_cols = [c for c in X_new.columns if "date" in c.lower() or "creation" in c.lower()]
                    if len(date_cols) > 0:
                        date_col = date_cols[0]
                        X_new[date_col] = pd.to_datetime(X_new[date_col], errors="coerce")
                        X_new["year"] = X_new[date_col].dt.year.fillna(-1).astype(int)
                        X_new["month"] = X_new[date_col].dt.month.fillna(-1).astype(int)
                        X_new["day"] = X_new[date_col].dt.day.fillna(-1).astype(int)
                        X_new["hour"] = X_new[date_col].dt.hour.fillna(-1).astype(int)
                        X_new["minute"] = X_new[date_col].dt.minute.fillna(-1).astype(int)
                        X_new["dayofweek"] = X_new[date_col].dt.dayofweek.fillna(-1).astype(int)
                        X_new["ts"] = X_new[date_col].astype("int64").fillna(-1) // 10**9
                        X_new = X_new.drop(columns=[date_col])

                    # Gérer NaN
                    num_cols = X_new.select_dtypes(include=[np.number]).columns.tolist()
                    cat_cols = X_new.select_dtypes(include=["object", "category"]).columns.tolist()
                    X_new[num_cols] = X_new[num_cols].fillna(-999)
                    X_new[cat_cols] = X_new[cat_cols].fillna("NA")

                    # Encoder les colonnes catégorielles
                    if encoder is not None and len(cat_cols) > 0:
                        X_new[cat_cols] = encoder.transform(X_new[cat_cols])

                    # S’assurer que tout est numérique
                    X_new = X_new.astype(float)
                    # Aligner les colonnes avec le modèle (exactement celles de l'entraînement)
                    expected_features = model.booster_.feature_name()

                    X_new = X_new.reindex(columns=expected_features, fill_value=-999)

                    # -------- Prédiction --------
                    y_proba = model.predict_proba(X_new)[:, 1]
                    y_pred = (y_proba >= 0.5).astype(int)

                    # Ajouter la colonne résultat
                    df_uploaded["Fausse_commande_predite"] = y_pred

                    st.success("Prédictions effectuées avec succès.")
                    st.dataframe(df_uploaded)

                    # Option de téléchargement
                    output_path = "predictions_result.xlsx"
                    df_uploaded.to_excel(output_path, index=False)
                    with open(output_path, "rb") as f:
                        st.download_button("📥 Télécharger le fichier avec prédictions", f, file_name="predictions_result.xlsx")

                except Exception as e:
                    st.error(f"❌ Erreur lors de la prédiction : {e}")

        else:
            st.error("❌ Le fichier n'est pas valide. Colonnes incorrectes.")
            st.write("Colonnes attendues :", colonnes_attendues)
            st.write("Colonnes trouvées :", list(df_uploaded.columns))



