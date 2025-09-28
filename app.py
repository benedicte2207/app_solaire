import streamlit as st

st.title("Ma première app Streamlit")
st.write("Hello, voici une application simple avec Streamlit !")

# Entrée utilisateur
name = st.text_input("Entre ton nom :")
if name:
    st.success(f"Bonjour {name} 👋")

# Slider
age = st.slider("Ton âge :", 1, 100, 25)
st.write(f"Tu as {age} ans.")
