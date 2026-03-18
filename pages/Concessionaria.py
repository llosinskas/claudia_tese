import streamlit as st
from models.Microrrede import Concessionaria
from models.CRUD import Criar, Ler, Deletar, Atualizar
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

st.set_page_config(
    page_title="Dados da concessionária", 
    page_icon=":house:", 
    layout="wide"
)



st.title("Dados da concessionária")
nome_input = st.text_input("Nome da concessionária")
tarifa_input = st.text_input("Tarifa de energia elétrica (R$/kWh)")
demanda_input = st.text_input("Demanda contratada (kW)")
grupo_input = st.text_input("Grupo tarifário (A, B)")

col1, col2 = st.columns(2)

if col1.button("Adicionar tarifa"):
    concessionaria = Concessionaria(
        tarifa=float(tarifa_input),
        nome=str(nome_input),
        demanda=float(demanda_input),
        grupo=str(grupo_input)
    )
    Criar(concessionaria)
    st.success("Tarifa da concessionária salva com sucesso!")
    
if col2.button("Cancelar"):
    st.rerun()

try: 
    st.subheader("Concessionárias cadastradas")
    with st.container():
        concessionarias = Ler(Concessionaria)
        for concessionaria in concessionarias:
            col1, col2, col3, col4 = st.columns([3,3,1,1])
            col1.write(f"Nome: {concessionaria.nome}")
            col2.write(f"Tarifa: {concessionaria.tarifa} R$/kWh")

            if col3.button("Deletar", key=f"deletar_{concessionaria.id}"):
                Deletar(concessionaria.id)
                st.rerun()
            if col4.button("Atualizar", key=f"atualizar_{concessionaria.id}"):
                pass
                # atualizar_concessionaria(concessionaria)
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
# A função abaixo calcula o valor da fatura de energia elétrica onde 0,25 é o valor do tempo medido que é 1 minutos ou 25% de uma hora.
def fatura_energia(consumo_kWh, tarifa_kWh):
    valor  = consumo_kWh * tarifa_kWh/60
    return valor 

