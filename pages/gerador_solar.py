import streamlit as st 

st.set_page_config(
    page_title="Gerador Solar", 
    page_icon=":sun_with_face:", 
    layout="wide"
)

st.title("Gerador Solar")
potencia = st.text_input("Potência nominal instalada (kWp)")
consumo = st.text_input("Consumo específico (kWh/m²)")
curva_irradiacao = st.file_uploader("Curva de irradiação (kW/m²)", type=["csv", "xlsx", "xls"])
area = st.text_input("Área do painel (m²)")
curva = st.file_uploader("Curva de eficiência (%)", type=["csv", "xlsx", "xls"])
emissao = st.text_input("Emissão de CO2 (g/kWh)")
custo_instalacao = st.text_input("Custo de instalação (R$/kWp)")
tempo_resposta = st.text_input("Tempo de resposta (s)")
