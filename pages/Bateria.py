import streamlit as st
from models.Bateria import Bateria, Criar, Atualizar, Ler, Deletar
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

st.set_page_config(
    page_title="Banco de Baterias",
    page_icon=":battery:",
    layout="wide",
)

def atualizar_bateria_banco(bateria_id, capacidade_max, capacidade, potencia, bateria_tipo, eficiencia, profundidade, capacidade_min):    
    bateria = session.query(Bateria).filter(Bateria.id == bateria_id).first()
    bateria.capacidade_max = capacidade_max
    bateria.capacidade = capacidade
    bateria.potencia = potencia
    bateria.bateria = bateria_tipo
    bateria.eficiencia = eficiencia
    bateria.profundidade = profundidade
    bateria.capacidade_min = capacidade_min
    session.commit()

@st.dialog("Atualizar Banco de Baterias")
def atualizar_bateria(bateria): 
    capacidade_max_atualizar = st.text_input("Capacidade máxima de carga (%)", value=str(bateria.capacidade_max))
    capacidade_atualizar = st.text_input("Capacidade nominal (kWh)", value=str(bateria.capacidade))
    potencia_atualizar = st.text_input("Potência nominal (kW)", value=str(bateria.potencia))
    bateria_atualizar = st.text_input("Tipo de bateria (Li-ion, Pb-acido, etc.)", value=str(bateria.bateria))
    eficiencia_atualizar = st.text_input("Eficiência de carga/descarga (%)", value=str(bateria.eficiencia))
    profundidade_atualizar = st.text_input("Profundidade de descarga (DoD) (%)", value=str(bateria.profundidade))
    capacidade_min_atualizar = st.text_input("Capacidade miníma kWh", value=str(bateria.capacidade_min))
    st.button(
        "Salvar Alterações", 
        on_click=atualizar_bateria_banco, 
        args=(
            bateria.id, 
            capacidade_max_atualizar, 
            capacidade_atualizar,
            potencia_atualizar, 
            bateria_atualizar, 
            eficiencia_atualizar, 
            profundidade_atualizar, 
            capacidade_min_atualizar))

st.title("Banco de Baterias")
st.text("O sistema BESS (Battery Energy Storage System)")

potencia_input = st.text_input("Potência nominal (kW)")
capacidade_input = st.text_input("Capacidade nominal (kWh)")
eficiencia_input = st.text_input("Eficiência de carga/descarga (%)")
bateria_input = st.text_input("Tipo de bateria (Li-ion, Pb-acido, etc.)")
capacidade_max_input = st.text_input("Capacidade máxima de carga (%)" )
capacidade_min_input = st.text_input("Capacidade miníma kWh")
custo_kwh_input = st.text_input("Custo por kWh (R$)")

col1, col2 = st.columns(2)
if col1.button("Salvar"):
    banco_bateria = Bateria(
    potencia = float(potencia_input),
    capacidade = float(capacidade_input), 
    bateria = str(bateria_input),
    nivel = float(100),
    eficiencia = float(eficiencia_input),
    capacidade_min = float(capacidade_min_input),
    capacidade_max = float(capacidade_max_input),
    custo_kwh = float(custo_kwh_input)
    )
    Criar(banco_bateria)
    st.success("Banco de bateria salvo com sucesso!") 
if col2.button("Limpar"):   
    st.rerun()

try: 
    st.subheader("Banco de Baterias")
    with st.container():
        
        baterias = Ler()
        for bateria in baterias:
            col1, col2, col3, col4 = st.columns([3,3,1,1])
            col1.write(f"Potência: {bateria.potencia} kW")
            col2.write(f"Capacidade: {bateria.capacidade} kWh")

            if col3.button("Deletar", key=f"deletar_{bateria.id}"):
                Deletar(bateria.id)
                st.rerun()
            if col4.button("Atualizar", key=f"atualizar_{bateria.id}"):
                atualizar_bateria(bateria)

except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
if st.button("Cancelar"):
    st.rerun()
