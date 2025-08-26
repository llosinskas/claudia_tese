import streamlit as st 

st.set_page_config(
    page_title="Banco de Baterias", 
    page_icon=":battery:", 
    layout="wide"
)
st.title("Banco de Baterias")
st.text("O sistema BESS (Battery Energy Storage System)")

capacidade = st.text_input("Capacidade nominal (kWh)")
potencia = st.text_input("Potência nominal (kW)")
bateria = st.text_input("Tipo de bateria (Li-ion, Pb-acido, etc.)")
eficiencia = st.text_input("Eficiência de carga/descarga (%)")
profundidade = st.text_input("Profundidade de descarga (DoD) (%)")
vida_util = st.text_input("Vida útil (anos)")
taxa_autodescarga = st.text_input("Taxa de autodescarga (%)")

st.title("Parâmetros Econômicos")
capex = st.text_input("CAPEX (R$)")
opex = st.text_input("OPEX (R$/ano)")   
emissao_evitada = st.text_input("Emissão evitada (kg CO2/kWh)")