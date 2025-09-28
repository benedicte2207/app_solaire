import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Analyse Site Solaire", layout="wide")

st.title("☀️ Tableau de bord - Site Solaire")

# --- Chargement des données ---
uploaded_file = st.file_uploader("📂 Importer un fichier CSV (production & consommation)", type="csv")

if uploaded_file:
    # Lecture et nettoyage
    data = pd.read_csv(uploaded_file)

    # Conversion forcée en datetime (évite 1970-01-01)
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce", dayfirst=True)
    data = data.dropna(subset=["Date"])  # supprime les dates invalides
    data = data.sort_values("Date").reset_index(drop=True)

    # -----------------------------
    # ⚙️ Filtres généraux (sidebar)
    # -----------------------------
    st.sidebar.header("⚙️ Filtres généraux")
    sites = data["Site"].unique()
    site_choice = st.sidebar.selectbox("Choisir un site :", sites)

    # Forcer une plage de dates par défaut
    default_start, default_end = data["Date"].min().date(), data["Date"].max().date()
    date_range = st.sidebar.date_input(
        "Sélectionner la période :",
        value=[default_start, default_end],
        min_value=default_start,
        max_value=default_end
    )

    # Gestion si l’utilisateur choisit une seule date
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range if date_range else default_start

    energy_types = st.sidebar.multiselect(
        "Types d’énergie :",
        options=data["Type_Energie"].unique(),
        default=data["Type_Energie"].unique()
    )

    # Application des filtres
    mask = (
        (data["Date"].dt.date.between(start_date, end_date)) &
        (data["Site"] == site_choice) &
        (data["Type_Energie"].isin(energy_types))
    )
    df_filtered = data.loc[mask]

    # -----------------------------
    # 📑 Onglets
    # -----------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚡ Performance",
        "📊 Consommation",
        "📅 Comparaison",
        "🛠 Maintenance"
    ])

    # --- Onglet 1 : Performance ---
    with tab1:
        st.subheader(f"Performance du site : {site_choice}")
        st.write(df_filtered.head())

        total_prod = df_filtered["Production_kWh"].sum()
        total_cons = df_filtered["Consommation_kWh"].sum()
        rendement = (total_cons / total_prod * 100) if total_prod > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Production totale", f"{total_prod:.2f} kWh")
        col2.metric("Consommation totale", f"{total_cons:.2f} kWh")
        col3.metric("Rendement global", f"{rendement:.1f} %")

        # ✅ Graphique production vs consommation (lissé par jour)
        if not df_filtered.empty:
            df_daily = (
                df_filtered.set_index("Date")
                .resample("D")
                .sum(numeric_only=True)
                .reset_index()
            )

            fig, ax = plt.subplots()
            ax.plot(df_daily["Date"], df_daily["Production_kWh"], label="Production")
            ax.plot(df_daily["Date"], df_daily["Consommation_kWh"], label="Consommation")
            ax.set_xlabel("Date")
            ax.set_ylabel("Énergie (kWh)")
            ax.legend()
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.warning("⚠️ Aucune donnée disponible pour les filtres sélectionnés.")

    # --- Onglet 2 : Consommation ---
    with tab2:
        st.subheader("Analyse de la consommation par type d’énergie")
        if not df_filtered.empty:
            for etype in df_filtered["Type_Energie"].unique():
                subset = df_filtered[df_filtered["Type_Energie"] == etype]
                st.line_chart(subset.set_index("Date")["Consommation_kWh"], height=200)

            st.bar_chart(
                df_filtered.groupby("Type_Energie")["Consommation_kWh"].sum()
            )
        else:
            st.info("Sélectionnez une période et un site pour voir les données.")

    # --- Onglet 3 : Comparaison ---
    with tab3:
        st.subheader("Comparaison de périodes et de sites")

        periode = st.radio("Choisir la période :", ["Jour", "Semaine", "Mois"], horizontal=True)

        if not df_filtered.empty:
            if periode == "Jour":
                df_grouped = df_filtered.groupby(df_filtered["Date"].dt.date).sum(numeric_only=True)
            elif periode == "Semaine":
                df_grouped = df_filtered.groupby(df_filtered["Date"].dt.isocalendar().week).sum(numeric_only=True)
            else:
                df_grouped = df_filtered.groupby(df_filtered["Date"].dt.to_period("M")).sum(numeric_only=True)

            st.line_chart(df_grouped["Consommation_kWh"])
        else:
            st.warning("⚠️ Pas de données pour la comparaison.")

        st.markdown("### Comparaison multi-sites")
        sites_selected = st.multiselect("Sélectionner les sites :", sites, default=sites)
        if sites_selected:
            df_sites = data[data["Site"].isin(sites_selected)].groupby("Site")["Consommation_kWh"].sum()
            st.bar_chart(df_sites)

    # --- Onglet 4 : Maintenance ---
    with tab4:
        st.subheader("Indicateurs de maintenance")
        seuil_rendement = 70
        if rendement < seuil_rendement:
            st.error(f"⚠️ Rendement faible : {rendement:.1f} % (seuil {seuil_rendement} %)")
        else:
            st.success("✅ Rendement satisfaisant")

        # Exemple d'alerte sur batteries
        if "Batterie" in df_filtered["Type_Energie"].values:
            bat_cons = df_filtered[df_filtered["Type_Energie"] == "Batterie"]["Consommation_kWh"].sum()
            if bat_cons > 0.8 * total_cons:
                st.warning("🔋 Les batteries supportent une forte charge de consommation. Vérifiez leur état de santé.")
st