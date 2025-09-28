import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("⚡ Tableau de bord - Performance & Consommation Énergétique")

# --- Chargement des données ---
uploaded_file = st.file_uploader("Importer un fichier CSV (production & consommation)", type="csv")

if uploaded_file:
    data = pd.read_csv(uploaded_file, parse_dates=["Date"])

    # Filtres
    st.sidebar.header("⚙️ Filtres")
    date_range = st.sidebar.date_input("Sélectionner la période", 
                                       [data["Date"].min(), data["Date"].max()])
    energy_types = st.sidebar.multiselect("Type d’énergie :", 
                                          options=data["Type_Energie"].unique(),
                                          default=data["Type_Energie"].unique())
    site_choice = st.sidebar.selectbox("Choisir le site :", data["Site"].unique())

    # Application des filtres
    mask = (data["Date"].between(date_range[0], date_range[1])) & (data["Type_Energie"].isin(energy_types)) & (data["Site"] == site_choice)
    df_filtered = data.loc[mask]

    st.subheader(f"📊 Consommation du site {site_choice}")
    st.write(df_filtered.head())

    # --- Visualisation Consommation ---
    fig, ax = plt.subplots()
    for etype in df_filtered["Type_Energie"].unique():
        subset = df_filtered[df_filtered["Type_Energie"] == etype]
        ax.plot(subset["Date"], subset["Consommation_kWh"], label=etype)

    ax.set_xlabel("Date")
    ax.set_ylabel("Consommation (kWh)")
    ax.legend()
    st.pyplot(fig)

    # --- Comparaison par période ---
    st.subheader("📅 Comparaison des périodes")
    periode = st.radio("Choisir la période :", ["Jour", "Semaine", "Mois"])
    if periode == "Jour":
        df_grouped = df_filtered.groupby(df_filtered["Date"].dt.date).sum()
    elif periode == "Semaine":
        df_grouped = df_filtered.groupby(df_filtered["Date"].dt.isocalendar().week).sum()
    else:
        df_grouped = df_filtered.groupby(df_filtered["Date"].dt.to_period("M")).sum()

    st.bar_chart(df_grouped["Consommation_kWh"])

    # --- Comparaison multi-sites ---
    st.subheader("🏭 Comparaison avec d’autres sites")
    sites_selected = st.multiselect("Sélectionner les sites à comparer :", data["Site"].unique(), default=data["Site"].unique())
    df_sites = data[data["Site"].isin(sites_selected)].groupby("Site")["Consommation_kWh"].sum()

    st.bar_chart(df_sites)
