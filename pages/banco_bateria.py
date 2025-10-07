import streamlit as st 
from models.Bateria import BancoBateria

st.set_page_config(
    page_title="Banco de Baterias", 
    page_icon=":battery:", 
    layout="wide"
)

if "banco_bateria"  not in st.session_state:
    st.session_state['banco_bateria'] = BancoBateria(0,0,0,0,0)

banco = BancoBateria(0,0,0,0,0)
banco = st.session_state['banco_bateria']


st.title("Banco de Baterias")
st.text("O sistema BESS (Battery Energy Storage System)")

capacidade = st.text_input("Capacidade nominal (kWh)", value=banco.capacidade)
potencia = st.text_input("Potência nominal (kW)", value=banco.potencia)
# bateria = st.text_input("Tipo de bateria (Li-ion, Pb-acido, etc.)")
eficiencia = st.text_input("Eficiência de carga/descarga (%)", value=banco.eficiencia)
profundidade = st.text_input("Profundidade de descarga (DoD) (%)",value=banco.capacidade_min)

capacidade_max = st.text_input("Capacidade máxima de carga (%)", value=banco.capacidade_max)

if st.button("Salvar"):
    banco_bateria = BancoBateria(potencia, capacidade,eficiencia, profundidade, capacidade_max)
    st.session_state['banco_bateria'] = banco_bateria

if st.button("Cancelar"):
    del st.session_state['banco_bateria']
    st.rerun()

# vida_util = st.text_input("Vida útil (anos)")
# taxa_autodescarga = st.text_input("Taxa de autodescarga (%)")



# st.title("Parâmetros Econômicos")
# capex = st.text_input("CAPEX (R$)")
# opex = st.text_input("OPEX (R$/ano)")   
# emissao_evitada = st.text_input("Emissão evitada (kg CO2/kWh)")

