import streamlit as st
from models.Biogas import Biogas, Criar, Atualizar, Ler, Deletar
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

st.set_page_config(
    page_title="Banco de Baterias",
    page_icon=":battery:",
    layout="wide",
)

def atualizar_biogas_banco(biogas_id, potencia, tanque,nivel, geracao, consumo_50, consumo_75, consumo_100, custo_por_kWh):    
    biogas = session.query(Biogas).filter(Biogas.id == biogas_id).first()
    biogas.potencia = potencia
    biogas.tanque = tanque
    biogas.geracao = geracao
    biogas.consumo_50 = consumo_50
    biogas.consumo_75 = consumo_75
    biogas.consumo_100 = consumo_100
    biogas.custo_por_kWh = custo_por_kWh
    session.commit()
    
@st.dialog("Atualizar Gerador Biogás")
def atualizar_biogas(biogas):
    potencia_atualizar = st.text_input("Potência nominal (kW)", value=str(biogas.potencia))
    tanque_atualizar = st.text_input("Capacidade do tanque (m³)", value=str(biogas.tanque))
    geracao_atualizar =st.text_input("Geração diária de biogás (m³/dia)", value=str(biogas.geracao))
    custo_por_kWh_input = st.text_input("Custo de operação do biogás (R$/m³)", value=str(biogas.custo_m3))
    consumo50_atualizar = st.text_input("Consumo de biogás a 50% da carga nominal (kW)", value=str(biogas.consumo_50))
    consumo75_atualizar = st.text_input("Consumo de biogás a 75% da carga nominal (kW)", value=str(biogas.consumo_75))
    consumo100_atualizar = st.text_input("Consumo de biogás a 100% da carga nominal (kW)", value=str(biogas.consumo_100))
    st.button(
        "Salvar Alterações", 
        on_click=atualizar_biogas_banco, 
        args=(
            biogas.id, 
            potencia_atualizar, 
            tanque_atualizar,
            100.0,  
            geracao_atualizar, 
            consumo50_atualizar, 
            consumo75_atualizar, 
            consumo100_atualizar, 
            custo_por_kWh_input))
    
st.title("Gerador de Biogás")

potencia_input = st.text_input("Potência nominal (kW)")
tanque_input = st.text_input("Capacidade do tanque (m³)")
geracao_input = st.text_input("Geração diária de biogás (m³/dia)")
custo_por_kWh_input = st.text_input("Custo de operação do biogás (R$/m³)")
consumo50_input = st.text_input("Consumo de biogás a 50% da carga nominal (m³/kWh)")
consumo75_input = st.text_input("Consumo de biogás a 75% da carga nominal (m³/kWh)")
consumo100_input = st.text_input("Consumo de biogás a 100% da carga nominal (m³/kWh)")

col1, col2 = st.columns(2)
if col1.button("Salvar"):
    biogas = Biogas(
        potencia=float(potencia_input),
        tanque=float(tanque_input),
        nivel = float(100), 
        geracao=float(geracao_input),
        custo_por_kWh=float(custo_por_kWh_input),
        consumo_50=float(consumo50_input),
        consumo_75=float(consumo75_input),
        consumo_100=float(consumo100_input)
    )
    session = SessionLocal()
    Criar(biogas)
  
    st.success("Gerador de biogás salvo com sucesso!")


if col2.button("Limpar"):
    st.rerun()
try:
    session = SessionLocal()

    st.subheader("Biogás")
    with st.container():
        
        biogases = Ler()
        for biogas in biogases:
            col1, col2, col3, col4 = st.columns([3,3,1,1])
            col1.write(f"Potência: {biogas.potencia} kW")
            col2.write(f"Capacidade: {biogas.tanque} m³")

            if col3.button("Deletar", key=f"deletar_{biogas.id}"):
                Deletar(biogas.id)
                st.rerun()
            if col4.button("Atualizar", key=f"atualizar_{biogas.id}"):
                atualizar_biogas(biogas)
                                
except Exception as e:
    st.error(f"Erro ao conectar ao banco de dados: {e}")

