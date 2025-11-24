import streamlit as st
from models.Bateria import BancoBateria
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()
st.set_page_config(
    page_title="Banco de Baterias",
    page_icon=":battery:",
    layout="wide",
)

st.title("Banco de Baterias")
st.text("O sistema BESS (Battery Energy Storage System)")

if 'capacidade_max' not in st.session_state:
    st.session_state['capacidade_max'] = ''
if 'capacidade' not in st.session_state:
    st.session_state['capacidade'] = ''
if 'potencia' not in st.session_state:
    st.session_state['potencia'] = ''
if 'bateria' not in st.session_state:
    st.session_state['bateria'] = ''
if 'eficiencia' not in st.session_state:
    st.session_state['eficiencia'] = ''
if 'profundidade' not in st.session_state:
    st.session_state['profundidade'] = ''   
if 'capacidade_min' not in st.session_state:
    st.session_state['capacidade_min'] = ''

capacidade_max = st.session_state['capacidade_max'] 
capacidade = st.session_state['capacidade']
potencia = st.session_state['potencia']
bateria = st.session_state['bateria'] 
eficiencia = st.session_state['eficiencia'] 
profundidade = st.session_state['profundidade'] 
capacidade_min = st.session_state['capacidade_min']


capacidade_max_input = st.text_input("Capacidade máxima de carga (%)", value=capacidade_max)
capacidade_input = st.text_input("Capacidade nominal (kWh)",value=capacidade)
potencia_input = st.text_input("Potência nominal (kW)", value=potencia)
bateria_input = st.text_input("Tipo de bateria (Li-ion, Pb-acido, etc.)", value=bateria)
eficiencia_input = st.text_input("Eficiência de carga/descarga (%)", value=eficiencia)
profundidade_input = st.text_input("Profundidade de descarga (DoD) (%)", value=profundidade)
capacidade_min_input = st.text_input("Capacidade miníma kWh", value=capacidade_min)


if st.button("Salvar"):
    banco_bateria = BancoBateria(
        potencia=float(potencia_input),
        capacidade=float(capacidade_input),
        nivel=100.0,
        eficiencia=float(eficiencia_input),
        capacidade_min=float(capacidade_min_input),
        capacidade_max=float(capacidade_max_input)
    
    )
    session = SessionLocal()

    session.add(banco_bateria)
    session.commit()

    st.success("Banco de bateria salvo com sucesso!") 
    st.rerun()

def clean_all():
    st.session_state['capacidade_max'] = ''
    st.session_state['capacidade'] = ''
    st.session_state['potencia'] = ''
    st.session_state['bateria'] = ''
    st.session_state['eficiencia'] = ''
    st.session_state['profundidade'] = ''
    st.session_state['capacidade_min'] = ''

if st.button("Cancelar", on_click=clean_all):
    clean_all()
    st.rerun()
