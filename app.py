import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import tempfile

st.set_page_config(page_title="Analyse Site Solaire", layout="wide")
st.title("☀️ Tableau de bord - Site Solaire")

# --- Chargement des données ---
uploaded_file = st.file_uploader("📂 Importer un fichier (CSV ou Excel)", type=["csv", "xlsx"])

if uploaded_file:
    # Détection de l'extension
    if uploaded_file.name.endswith(".csv"):
        data = pd.read_csv(uploaded_file, parse_dates=["Date"])
    else:
        data = pd.read_excel(uploaded_file, parse_dates=["Date"])

    # Vérification des colonnes obligatoires
    colonnes_attendues = {"Date", "Site", "Type_Energie", "Production_kWh", "Consommation_kWh"}
    if not colonnes_attendues.issubset(data.columns):
        st.error(f"❌ Le fichier doit contenir les colonnes suivantes : {colonnes_attendues}")
        st.stop()

    # Tri par date
    data = data.sort_values("Date")

    # -----------------------------
    # ⚙️ Filtres généraux (sidebar)
    # -----------------------------
    st.sidebar.header("⚙️ Filtres généraux")
    sites = data["Site"].unique()
    site_choice = st.sidebar.selectbox("Choisir un site :", sites)
    date_range = st.sidebar.date_input(
        "Sélectionner la période :", 
        [data["Date"].min().date(), data["Date"].max().date()]
    )
    energy_types = st.sidebar.multiselect(
        "Types d’énergie :", 
        options=data["Type_Energie"].unique(),
        default=data["Type_Energie"].unique()
    )

    # Application des filtres
    mask = (
        (data["Date"].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))) &
        (data["Site"] == site_choice) &
        (data["Type_Energie"].isin(energy_types))
    )
    df_filtered = data.loc[mask]

    if df_filtered.empty:
        st.warning("⚠️ Aucune donnée disponible pour les filtres sélectionnés.")
    else:
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

            # Graphique production vs consommation
            fig, ax = plt.subplots()
            ax.plot(df_filtered["Date"], df_filtered["Production_kWh"], label="Production")
            ax.plot(df_filtered["Date"], df_filtered["Consommation_kWh"], label="Consommation")
            ax.set_xlabel("Date")
            ax.set_ylabel("Énergie (kWh)")
            ax.legend()
            st.pyplot(fig)

        # --- Onglet 2 : Consommation ---
        with tab2:
            st.subheader("Analyse de la consommation par type d’énergie")
            for etype in df_filtered["Type_Energie"].unique():
                subset = df_filtered[df_filtered["Type_Energie"] == etype]
                st.line_chart(subset.set_index("Date")["Consommation_kWh"], height=200)

            st.bar_chart(df_filtered.groupby("Type_Energie")["Consommation_kWh"].sum())

        # --- Onglet 3 : Comparaison ---
        with tab3:
            st.subheader("Comparaison de périodes et de sites")

            periode = st.radio("Choisir la période :", ["Jour", "Semaine", "Mois"], horizontal=True)
            if periode == "Jour":
                df_grouped = df_filtered.groupby(df_filtered["Date"].dt.date).sum(numeric_only=True)
            elif periode == "Semaine":
                df_grouped = df_filtered.groupby(df_filtered["Date"].dt.isocalendar().week).sum(numeric_only=True)
            else:
                df_grouped = df_filtered.groupby(df_filtered["Date"].dt.to_period("M")).sum(numeric_only=True)

            st.line_chart(df_grouped["Consommation_kWh"])

            st.markdown("### Comparaison multi-sites")
            sites_selected = st.multiselect("Sélectionner les sites :", sites, default=sites)
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

            if "Batterie" in df_filtered["Type_Energie"].values:
                bat_cons = df_filtered[df_filtered["Type_Energie"] == "Batterie"]["Consommation_kWh"].sum()
                if bat_cons > 0.8 * total_cons:
                    st.warning("🔋 Les batteries supportent une forte charge de consommation. Vérifiez leur état de santé.")

        # -----------------------------
        # 📥 Export Excel
        # -----------------------------
        buffer = io.BytesIO()
        df_filtered.to_excel(buffer, index=False)
        st.download_button(
            label="📥 Télécharger les données en Excel",
            data=buffer,
            file_name="rapport_site_solaire.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # -----------------------------
        # 📑 Export PDF
        # -----------------------------
        if st.button("📑 Générer rapport PDF"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                doc = SimpleDocTemplate(tmpfile.name)
                styles = getSampleStyleSheet()
                story = []

                # Titre
                story.append(Paragraph("Rapport - Analyse du site solaire", styles["Title"]))
                story.append(Spacer(1, 20))

                # Indicateurs
                story.append(Paragraph(f"Production totale : {total_prod:.2f} kWh", styles["Normal"]))
                story.append(Paragraph(f"Consommation totale : {total_cons:.2f} kWh", styles["Normal"]))
                story.append(Paragraph(f"Rendement global : {rendement:.1f} %", styles["Normal"]))
                story.append(Spacer(1, 20))

                # Graphique production vs consommation
                fig, ax = plt.subplots()
                ax.plot(df_filtered["Date"], df_filtered["Production_kWh"], label="Production")
                ax.plot(df_filtered["Date"], df_filtered["Consommation_kWh"], label="Consommation")
                ax.set_title("Production vs Consommation")
                ax.legend()

                # Sauvegarde du graphique
                graph_path = tmpfile.name.replace(".pdf", ".png")
                fig.savefig(graph_path)

                story.append(Image(graph_path, width=400, height=200))

                # Génération PDF
                doc.build(story)

                # Lecture du PDF généré
                with open(tmpfile.name, "rb") as f:
                    st.download_button(
                        "📥 Télécharger rapport PDF",
                        f,
                        file_name="rapport_site_solaire.pdf",
                        mime="application/pdf"
                    )
