import streamlit as st
from models.Concessionaria import Concessionaria

st.set_page_config(
    page_title="Dados da concessionária", 
    page_icon=":house:", 
    layout="wide"
)

tarifa_value = st.session_state.get("tarifa", None)

if "concessionaria" not in st.session_state:
    st.session_state["concessionaria"] = Concessionaria(0,0,0)
concessionaria = Concessionaria(0,0,0)

concessionaria = st.session_state["concessionaria"]

st.title("Dados da concessionária")


demanda = st.text_input("Demanda contratada (kW)", value = concessionaria.demanda if concessionaria.demanda==0 else concessionaria.demanda)

grupo = st.selectbox("Grupo tarifário", ["B", "A"])
if grupo == "A":
    subgrupo = st.selectbox("Subgrupo", ["Azul", "Verde"])
    tarifa_demanda = st.text_input("Tarifa de demanda (R$/kW-mês)")
    tarifa_consumo = st.text_input("Tarifa de consumo (R$/kWh)")

# tipo_contrato = st.selectbox("Tipo de contrato", ["Comercial", "Residencial", "Industrial", "Rural"])

elif grupo == "B":
    tarifa = st.text_input("Tarifa (R$/kWh)", value=concessionaria.tarifa if concessionaria.tarifa == 0  else concessionaria.tarifa)


if st.button("Adicionar tarifa"):
    st.session_state["tarifa"] = float(tarifa)
    concessionaria = Concessionaria(tarifa, demanda, grupo)
    st.session_state['concessionaria'] = concessionaria

if st.button("Cancelar"):
    del st.session_state["concessionaria"]
    st.rerun()

# A função abaixo calcula o valor da fatura de energia elétrica onde 0,25 é o valor do tempo medido que é 1 minutos ou 25% de uma hora.
def fatura_energia(consumo_kWh, tarifa_kWh):
    valor  = consumo_kWh * tarifa_kWh/60
    return valor 

