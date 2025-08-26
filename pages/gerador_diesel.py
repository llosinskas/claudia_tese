import streamlit as st 

st.set_page_config(
    page_title="Gerador Diesel", 
    page_icon=":fuelpump:", 
    layout="wide"
)

st.title("Gerador Diesel")
potencia = st.text_input("Potência nominal (kW)")
consumo = st.text_input("Consumo específico (l/kWh)")
capacidade = st.text_input("Capacidade do tanque (l)")
curva = st.file_uploader("Curva de eficiência (%)", type=["csv", "xlsx", "xls"])
emissao = st.text_input("Emissão de CO2 (g/kWh)")
custo_combustivel = st.text_input("Custo do combustível (R$/l)")
tempo_resposta = st.text_input("Tempo de resposta (s)")
