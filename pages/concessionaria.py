import streamlit as st

st.set_page_config(
    page_title="Dados da concessionária", 
    page_icon=":house:", 
    layout="wide"
)

tarifa_value = st.session_state.get("tarifa", None)

st.title("Dados da concessionária")
tipo_contrato = st.selectbox("Tipo de contrato", ["Comercial", "Residencial", "Industrial", "Rural"])
demanda = st.text_input("Demanda contratada (kW)")

grupo = st.selectbox("Grupo tarifário", ["B", "A"])
if grupo == "A":
    subgrupo = st.selectbox("Subgrupo", ["Azul", "Verde"])
    tarifa_demanda = st.text_input("Tarifa de demanda (R$/kW-mês)")
    tarifa_consumo = st.text_input("Tarifa de consumo (R$/kWh)")


elif grupo == "B":
    tarifa = st.text_input("Tarifa (R$/kWh)", value=tarifa_value if tarifa_value is not None else "")


if st.button("Adicionar tarifa"):
    st.session_state["tarifa"] = float(tarifa)


# A função abaixo calcula o valor da fatura de energia elétrica onde 0,25 é o valor do tempo medido que é 15 minutos ou 25% de uma hora.
def fatura_energia(consumo_kWh, tarifa_kWh):
    valor  = consumo_kWh * tarifa_kWh/60*15
    return valor 

class Concessionaria:
    def __init__(self, tarifa, demanda):
        self.tarifa = tarifa
        self.demanda = demanda