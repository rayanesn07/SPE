import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# 1. Chargement des données
# =========================
@st.cache_data
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
            font-size: 28px !important;
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
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(" Total commandes", total_cmds)
    col2.metric(" Confirmées", confirmed)
    col3.metric(" Annulées", cancelled)
    col4.metric(" En confirmation", pending)

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
    # 9. Graphiques d’évolution (avec filtre global)
    # =========================
    if "Date_Creation" in df.columns:
        df["Annee"] = df["Date_Creation"].dt.year
        df["Mois"] = df["Date_Creation"].dt.to_period("M").astype(str)

        st.subheader(" Évolution des commandes")

        mode = st.radio("Type d’analyse :", ["Mensuelle", "Annuelle"], horizontal=True)

        # ===== Mode Mensuel =====
        if mode == "Mensuelle":
            mois_dispo = sorted(df["Mois"].unique())
            mois_select = st.selectbox("Choisir un mois :", mois_dispo, key="mois_global")

            df_mois = df[df["Mois"] == mois_select]

            evo_col1, evo_col2 = st.columns(2)

            # Graphe total (gauche)
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

            # Graphe livrées (droite)
            with evo_col2:
                df_grouped2 = df_mois.groupby(
                    [df_mois["Date_Creation"].dt.day, "Etat_Livraison"]
                ).size().reset_index(name="Nombre De Commandes")
                df_grouped2.rename(columns={"Date_Creation": "Jour"}, inplace=True)

                fig_livrees = px.bar(
                    df_grouped2,
                    x="Jour",
                    y="Nombre De Commandes",
                    color="Etat_Livraison",
                    title=f"Commandes livrées - {mois_select}",
                    barmode="stack",
                    category_orders={"Etat_Livraison": ["Livrée", "Preparation Stock", "Retour"]},
                    color_discrete_map={
                        "Livrée": "#00DA36",
                        "Preparation Stock": "#A7A7A7",
                        "Retour": "#E70000",
                        "En livraison": "#E79E00"
                    }
                )
                fig_livrees.update_layout(height=450)
                st.plotly_chart(fig_livrees, use_container_width=True)

        # ===== Mode Annuel =====
        else:
            annees_dispo = sorted(df["Annee"].unique())
            annee_select = st.selectbox("Choisir une année :", annees_dispo, key="annee_global")

            df_annee = df[df["Annee"] == annee_select]

            evo_col1, evo_col2 = st.columns(2)

            # Graphe total (gauche)
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

            # Graphe livrées (droite)
            with evo_col2:
                df_grouped2 = df_annee.groupby(
                    [df_annee["Date_Creation"].dt.month, "Etat_Livraison"]
                ).size().reset_index(name="Nombre De Commandes")
                df_grouped2.rename(columns={"Date_Creation": "Mois"}, inplace=True)

                fig_livrees = px.bar(
                    df_grouped2,
                    x="Mois",
                    y="Nombre De Commandes",
                    color="Etat_Livraison",
                    title=f"Commandes livrées - {annee_select}",
                    barmode="stack",
                    category_orders={"Etat_Livraison": ["Livrée", "Preparation Stock", "Retour"]},
                    color_discrete_map={
                        "Livrée": "#00DA36",
                        "Preparation Stock": "#A7A7A7",
                        "Retour": "#E70000",
                        "En livraison": "#E79E00"
                    }
                )
                fig_livrees.update_layout(height=450)
                st.plotly_chart(fig_livrees, use_container_width=True)

# =========================
# 10. Contenu de la page Livraison et Stock
# =========================
elif st.session_state.page == 'livraison':
    st.title("Dashboard Livraison et Stock")
    st.info("Cette page est en cours de développement. Revenez bientôt!")
    
    # Vous pouvez ajouter ici le contenu de votre futur dashboard
    st.write("Contenu du dashboard livraison et stock à venir...")