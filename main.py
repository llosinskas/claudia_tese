import streamlit as st
import pandas as pd 
from numpy.random import default_rng as rng
from pages.concessionaria import fatura_energia

st.set_page_config(
    page_title="Gerenciador de Energia", 
    page_icon=":fuelpump:", 
    layout="wide"
)

# def Tomada_descisao(carga, curva_solar, concessionaria, bateria):

# Carga
if "carga" not in st.session_state:
    st.session_state["carga"] = pd.DataFrame()
if "potencia" not in st.session_state:
    st.session_state["potencia"] = None
carga  = pd.DataFrame(st.session_state["carga"])
pot_carga = st.session_state["potencia"]

# Concessionária
if "tarifa" not in st.session_state:
    st.session_state["tarifa"] = None
tarifa = st.session_state["tarifa"]
valor_cativa = 0
if not carga.empty:
    for carga1 in carga["Potência (kW)"]:
            valor_cativa += fatura_energia(carga1, tarifa) if tarifa is not None else 0
            print(valor_cativa)
    st.write(f"Valor da fatura de energia elétrica: R$ {valor_cativa:.2f}")

# Gerador solar
if "curva_irradiacao" not in st.session_state:
    st.session_state["curva_irradiacao"] = pd.DataFrame()
curva_irradiacao = pd.DataFrame(st.session_state["curva_irradiacao"])
st.session_state["arquivo_irradiacao"]
st.line_chart(curva_irradiacao)

st.title("Gerenciador de Energia")
nome_analise = st.text_input("Nome da análise")
if not carga.empty:
    st.line_chart(carga, x="tempo (min)", y="Potência (kW)")

if not curva_irradiacao.empty and pot_carga is not None:
    
    st.write(carga)
    df_combinado = curva_irradiacao
    df_combinado["Potência (kW)"] = carga["Potência (kW)"]
    
    st.line_chart(df_combinado,  y=["irradiacao", "Potência (kW)"])


# Micro rede priorizando o custo
# def micro_rede(pot_carga, pot_gerador, curva_irradiacao, pot_diesel):

# Micro rede priorizando o gerador solar
# def micro_rede_solar(pot_carga, curva_irradiacao, pot_diesel):


# Função para calcular os custo operacionais
# tempo de vida útil em meses 
def custos(tarifa_rede, custo_combustivel, vida_util_solar ,custo_instalacao_gerador, vida_util_bateria, custo_instalacao_bateria):
    custo_solar = custo_instalacao_gerador/vida_util_solar
    custo_bateria = (custo_instalacao_bateria/vida_util_bateria)
    df = pd.DataFrame()
    df["Indice"] = ["Tarifa da Rede (R$/kWh)", "Custo do Combustível (R$/kWh)", "Custo do Gerador Solar (R$/kWh)", "Custo da Bateria (R$/kWh)"]
    df["Custo (R$)"] = [tarifa_rede, custo_combustivel, custo_solar, custo_bateria]
    return df



st.button("Rodar Simulação")
st.button("Exportar Resultados")
if st.button("Cancelar"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()