import streamlit as st 
from models.Microrrede import Diesel
from models.CRUD import Criar, Ler, Deletar, Atualizar
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

st.set_page_config(
    page_title="Gerador Diesel", 
    page_icon=":fuelpump:", 
    layout="wide"
)
st.title("Gerador Diesel")
potencia_input = st.text_input("Potência nominal (kW)")
custo_input = st.text_input("Custo (R$/l)") 
consumo_50_input = st.text_input("Consumo a 50% da carga (l/kWh)")
consumo_75_input = st.text_input("Consumo a 75% da carga (l/kWh)")
consumo_100_input = st.text_input("Consumo a 100% da carga (l/kWh)")
tanque_input = st.text_input("Capacidade do tanque (l)")

col1, col2 = st.columns([1,10])
if col1.button("Salvar"):
    diesel = Diesel(
        potencia = float(potencia_input), 
        custo = float(custo_input), 
        consumo_50 = float(consumo_50_input), 
        consumo_75 = float(consumo_75_input), 
        consumo_100 = float(consumo_100_input), 
        tanque = float(tanque_input), 
        nivel=float(100)
        )
    
    Criar(diesel)
    st.success("Gerador Diesel salvo com sucesso!")

if col2.button("Cancelar"):
    st.rerun()

try:
    st.subheader("Geradores Diesel cadastrados")
    with st.container():
        diesels = Ler()
        for diesel in diesels:
            col1, col2, col3, col4 = st.columns([3,3,1,1])
            col1.write(f"Potência nominal: {diesel.potencia} kW")
            col2.write(f"Custo: {diesel.custo} R$/l")

            if col3.button("Deletar", key=f"deletar_{diesel.id}"):
                Deletar(diesel.id)
                st.rerun()
            if col4.button("Atualizar", key=f"atualizar_{diesel.id}"):
                pass
                # atualizar_diesel(diesel)
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
# select = st.selectbox("Curva de eficiência (%)", ["Valor fixo (%)", "Importar curva",])
# custo_combustivel = st.text_input("Custo do combustível (R$/l)")

# tempo_resposta = st.text_input("Tempo de resposta (s)")
# curva = st.file_uploader("Curva de eficiência (%)", type=["csv", "xlsx", "xls"])
# emissao = st.text_input("Emissão de CO2 (g/kWh)")
# consumo = st.text_input("Consumo específico (l/kWh)")
 
