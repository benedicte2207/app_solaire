import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import tempfile

# ===========================
# CONFIGURATION DE LA PAGE
# ===========================
st.set_page_config(page_title="Analyse Site Solaire", layout="wide")
st.title("☀️ Tableau de bord - Site Solaire")

# Style global des graphiques Matplotlib
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({
    "figure.figsize": (8, 4),
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "legend.fontsize": 10,
    "font.family": "sans-serif",
    "font.sans-serif": "Arial"
})

# ===========================
# CHARGEMENT DES DONNÉES
# ===========================
uploaded_file = st.file_uploader("📂 Importer un fichier (CSV ou Excel)", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        data = pd.read_csv(uploaded_file, parse_dates=["Date"])
    else:
        data = pd.read_excel(uploaded_file, parse_dates=["Date"])

    colonnes_attendues = {"Date", "Site", "Type_Energie", "Production_kWh", "Consommation_kWh"}
    if not colonnes_attendues.issubset(data.columns):
        st.error(f"❌ Le fichier doit contenir les colonnes suivantes : {colonnes_attendues}")
        st.stop()

    data = data.sort_values("Date")

    # ===========================
    # BARRE LATÉRALE - FILTRES
    # ===========================
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

    mask = (
        (data["Date"].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))) &
        (data["Site"] == site_choice) &
        (data["Type_Energie"].isin(energy_types))
    )
    df_filtered = data.loc[mask]

    if df_filtered.empty:
        st.warning("⚠️ Aucune donnée disponible pour les filtres sélectionnés.")
    else:
        # ===========================
        # ONGLET PRINCIPAUX
        # ===========================
        tab1, tab2, tab3, tab4 = st.tabs([
            "⚡ Performance", 
            "📊 Consommation", 
            "📅 Comparaison", 
            "🛠 Maintenance"
        ])

        # ---------------------------
        # 🔹 ONGLET 1 : PERFORMANCE
        # ---------------------------
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
            ax.plot(df_filtered["Date"], df_filtered["Production_kWh"], 
                    color="#1f77b4", linewidth=2.5, label="Production solaire")
            ax.plot(df_filtered["Date"], df_filtered["Consommation_kWh"], 
                    color="#ff7f0e", linewidth=2.5, linestyle="--", label="Consommation énergétique")

            ax.set_title("Production vs Consommation d'énergie", fontsize=14, fontweight='bold')
            ax.set_xlabel("Date")
            ax.set_ylabel("Énergie (kWh)")
            ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="gray")
            ax.grid(True, linestyle="--", alpha=0.6)
            plt.tight_layout()
            st.pyplot(fig)

        # ---------------------------
        # 🔹 ONGLET 2 : CONSOMMATION
        # ---------------------------
        with tab2:
            st.subheader("Analyse de la consommation par type d’énergie")

            for etype in df_filtered["Type_Energie"].unique():
                subset = df_filtered[df_filtered["Type_Energie"] == etype]
                fig, ax = plt.subplots()
                ax.plot(subset["Date"], subset["Consommation_kWh"], linewidth=2.2, label=f"{etype}")
                ax.set_title(f"Consommation - {etype}")
                ax.set_xlabel("Date")
                ax.set_ylabel("Consommation (kWh)")
                ax.legend()
                st.pyplot(fig)

            st.markdown("### Répartition totale de la consommation par type d’énergie")
            df_sum = df_filtered.groupby("Type_Energie")["Consommation_kWh"].sum()
            fig, ax = plt.subplots()
            ax.bar(df_sum.index, df_sum.values, color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"])
            ax.set_ylabel("Consommation totale (kWh)")
            ax.set_xlabel("Type d’énergie")
            plt.xticks(rotation=15)
            plt.tight_layout()
            st.pyplot(fig)

        # ---------------------------
        # 🔹 ONGLET 3 : COMPARAISON
        # ---------------------------
        with tab3:
            st.subheader("Comparaison de périodes et de sites")

            periode = st.radio("Choisir la période :", ["Jour", "Semaine", "Mois"], horizontal=True)
            if periode == "Jour":
                df_grouped = df_filtered.groupby(df_filtered["Date"].dt.date).sum(numeric_only=True)
            elif periode == "Semaine":
                df_grouped = df_filtered.groupby(df_filtered["Date"].dt.isocalendar().week).sum(numeric_only=True)
            else:
                df_grouped = df_filtered.groupby(df_filtered["Date"].dt.to_period("M")).sum(numeric_only=True)

            fig, ax = plt.subplots()
            ax.plot(df_grouped.index.astype(str), df_grouped["Consommation_kWh"], color="#2ca02c", linewidth=2)
            ax.set_title("Comparaison de la consommation selon la période")
            ax.set_xlabel(periode)
            ax.set_ylabel("Consommation (kWh)")
            ax.grid(True, linestyle="--", alpha=0.6)
            plt.tight_layout()
            st.pyplot(fig)

            st.markdown("### Comparaison multi-sites")
            sites_selected = st.multiselect("Sélectionner les sites :", sites, default=sites)
            df_sites = data[data["Site"].isin(sites_selected)].groupby("Site")["Consommation_kWh"].sum()

            fig, ax = plt.subplots()
            ax.bar(df_sites.index, df_sites.values, color="#9467bd")
            ax.set_xlabel("Site")
            ax.set_ylabel("Consommation totale (kWh)")
            plt.xticks(rotation=10)
            plt.tight_layout()
            st.pyplot(fig)

        # ---------------------------
        # 🔹 ONGLET 4 : MAINTENANCE
        # ---------------------------
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

        # ---------------------------
        # 📥 EXPORT EXCEL
        # ---------------------------
        buffer = io.BytesIO()
        df_filtered.to_excel(buffer, index=False)
        st.download_button(
            label="📥 Télécharger les données en Excel",
            data=buffer,
            file_name="rapport_site_solaire.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # ---------------------------
        # 📑 EXPORT PDF
        # ---------------------------
        if st.button("📑 Générer rapport PDF"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                doc = SimpleDocTemplate(tmpfile.name)
                styles = getSampleStyleSheet()
                story = []

                story.append(Paragraph("Rapport - Analyse du site solaire", styles["Title"]))
                story.append(Spacer(1, 20))
                story.append(Paragraph(f"Production totale : {total_prod:.2f} kWh", styles["Normal"]))
                story.append(Paragraph(f"Consommation totale : {total_cons:.2f} kWh", styles["Normal"]))
                story.append(Paragraph(f"Rendement global : {rendement:.1f} %", styles["Normal"]))
                story.append(Spacer(1, 20))

                fig, ax = plt.subplots()
                ax.plot(df_filtered["Date"], df_filtered["Production_kWh"], color="#1f77b4", linewidth=2, label="Production")
                ax.plot(df_filtered["Date"], df_filtered["Consommation_kWh"], color="#ff7f0e", linewidth=2, linestyle="--", label="Consommation")
                ax.set_title("Production vs Consommation")
                ax.legend()
                plt.tight_layout()

                graph_path = tmpfile.name.replace(".pdf", ".png")
                fig.savefig(graph_path)
                plt.close(fig)

                story.append(Image(graph_path, width=400, height=200))
                doc.build(story)

                with open(tmpfile.name, "rb") as f:
                    st.download_button(
                        "📥 Télécharger rapport PDF",
                        f,
                        file_name="rapport_site_solaire.pdf",
                        mime="application/pdf"
                    )
