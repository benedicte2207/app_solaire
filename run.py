import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("📊 Analyse de performance d’un site solaire")

# Chargement des données
uploaded_file = st.file_uploader("Importer un fichier CSV de production", type="csv")

if uploaded_file:
    data = pd.read_csv(uploaded_file)
    st.write("Aperçu des données :", data.head())

    # Exemple : graphique de la production
    st.subheader("Production solaire (kWh)")
    fig, ax = plt.subplots()
    ax.plot(data["Date"], data["Production_kWh"], label="Production réelle")
    ax.set_xlabel("Date")
    ax.set_ylabel("Énergie (kWh)")
    ax.legend()
    st.pyplot(fig)

    # Indicateurs simples
    st.subheader("Indicateurs de performance")
    total_prod = data["Production_kWh"].sum()
    st.metric("Production totale", f"{total_prod:.2f} kWh")
