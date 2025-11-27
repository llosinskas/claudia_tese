import streamlit as st 
from models.Diesel import Diesel

st.set_page_config(
    page_title="Gerador Diesel", 
    page_icon=":fuelpump:", 
    layout="wide"
)

if "Diesel" not in st.session_state:
    st.session_state["Diesel"] = Diesel(0,0,0,0,0,0) 
    
diesel = Diesel(0,0,0,0,0,0)
diesel = st.session_state["Diesel"]

st.title("Gerador Diesel")
potencia = st.text_input("Potência nominal (kW)", value = diesel.potencia)
custo = st.text_input("Custo R$/l", value=diesel.custo)
consumo_50 = st.text_input("Consumo a 50% da carga", value = diesel.consumo_50)
consumo_75 = st.text_input("Consumo a 75% da carga",value = diesel.consumo_75)
consumo_100 = st.text_input("Consumo a 100% da carga", diesel.consumo_100)
tanque = st.text_input("Capacidade do tanque (l)", value=diesel.tanque)

if st.button("Salvar"):
    diesel = Diesel(potencia, custo, consumo_50, consumo_75, consumo_100, tanque)
    st.session_state["Diesel"]=diesel

if st.button("Cancelar"):
    del st.session_state["Diesel"]
    st.rerun()


# select = st.selectbox("Curva de eficiência (%)", ["Valor fixo (%)", "Importar curva",])
# custo_combustivel = st.text_input("Custo do combustível (R$/l)")

# tempo_resposta = st.text_input("Tempo de resposta (s)")
# curva = st.file_uploader("Curva de eficiência (%)", type=["csv", "xlsx", "xls"])
# emissao = st.text_input("Emissão de CO2 (g/kWh)")
# consumo = st.text_input("Consumo específico (l/kWh)")
 
