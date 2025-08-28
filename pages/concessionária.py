import streamlit as st
st.set_page_config(
    page_title="Dados da concessionária", 
    page_icon=":house:", 
    layout="wide"
)

st.title("Dados da concessionária")
tipo_contrato = st.selectbox("Tipo de contrato", ["Comercial", "Residencial", "Industrial", "Rural"])
demanda = st.text_input("Demanda contratada (kW)")
tarifa_demanda = st.text_input("Tarifa de demanda (R$/kW)")
tarifa_consumo = st.text_input("Tarifa de consumo (R$/kWh)")
