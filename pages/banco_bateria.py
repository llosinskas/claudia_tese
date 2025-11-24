import streamlit as st
from models.Bateria import BancoBateria
from database.database_config import Configure
from database.CRUD import criar
DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()
st.set_page_config(
    page_title="Banco de Baterias",
    page_icon=":battery:",
    layout="wide",
)
#if "banco_bateria" not in st.session_state:
# st.session_state['banco_bateria'] = BancoBateria(0, 0, 0, 0, 0)

#banco = BancoBateria(0, 0, 0, 0, 0)
#banco = st.session_state['banco_bateria']

st.title("Banco de Baterias")
st.text("O sistema BESS (Battery Energy Storage System)")

#if "banco_bateria"  not in st.session_state:
#    st.session_state['banco_bateria'] = BancoBateria(0,0,0,0,0)

#banco = BancoBateria(0,0,0,0,0)
#banco = st.session_state['banco_bateria']

#capacidade = st.text_input("Capacidade nominal (kWh)", value=banco.capacidade)
#potencia = st.text_input("Potência nominal (kW)", value=banco.potencia)
# bateria = st.text_input("Tipo de bateria (Li-ion, Pb-acido, etc.)")
#eficiencia = st.text_input("Eficiência de carga/descarga (%)", value=banco.eficiencia)
#profundidade = st.text_input("Profundidade de descarga (DoD) (%)",value=banco.capacidade_min)

capacidade_max = st.number_input("Capacidade máxima de carga (%)", value=0.0)
capacidade = st.number_input("Capacidade nominal (kWh)", value=0.0)
potencia = st.number_input("Potência nominal (kW)", value=0.0)
bateria = st.number_input("Tipo de bateria (Li-ion, Pb-acido, etc.)", value=0.0)
eficiencia = st.number_input("Eficiência de carga/descarga (%)", value=0.0)
profundidade = st.number_input("Profundidade de descarga (DoD) (%)", value=0.0)
capacidade_min = st.number_input("Capacidade miníma kWh", value=0.0)


if st.button("Salvar"):
    dados = {
        "potencia":potencia, 
        "capacidade":capacidade, 
        "nivel": 100.0, 
        "eficiencia":eficiencia, 
        "capacidade_min":capacidade_min, 
        "capacidade_max":capacidade_max
    }
    criar(session, BancoBateria, dados)
    st.rerun()


if st.button("Cancelar"):
    pass
