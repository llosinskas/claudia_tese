import streamlit as st
import pandas as pd 
from pages.concessionaria import fatura_energia
from models.Bateria import BancoBateria
from models.Carga import Carga
from models.Concessionaria import Concessionaria
from models.Diesel import Diesel
from models.Solar import Solar
from Logicas import Uso_rede, Uso_diesel, Otimizacao1, Otimizacao2

st.set_page_config(
    page_title="Gerenciador de Energia", 
    page_icon=":fuelpump:", 
    layout="wide"
)

st.title("Gerenciador de Energia")
nome_analise = st.text_input("Nome da análise")


# Diesel 
if "Diesel" not in st.session_state:
    st.session_state["Diesel"] = Diesel(0,0,0,0,0,0)

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
            
    st.write(f"Valor da fatura de energia elétrica: R$ {valor_cativa:.2f}")

# Gerador solar
if "curva_irradiacao" not in st.session_state:
    st.session_state["curva_irradiacao"] = pd.DataFrame()
curva_irradiacao = pd.DataFrame(st.session_state["curva_irradiacao"])
if "arquivo_irradiacao" not in st.session_state:
    st.session_state["arquivo_irradiacao"] = pd.DataFrame()
curva_producao = pd.DataFrame(st.session_state["arquivo_irradiacao"])
# curva_producao = st.session_state["arquivo_irradiacao"]
if not curva_producao.empty:
    st.line_chart(curva_producao, x="tempo (min)", y="Potência")


if not carga.empty:
    st.line_chart(carga, x="tempo (min)", y="Potência (kW)")

if not curva_irradiacao.empty and pot_carga is not None:
    
    st.write(carga)
    df_combinado = curva_irradiacao
    df_combinado["Potência (kW)"] = carga["Potência (kW)"]
    
    st.line_chart(df_combinado,  y=["irradiacao", "Potência (kW)"])

st.header("Otimização 1 - Prioriza o uso do gerador solar e bateria e rede")
st.subheader("SOC")
st.subheader("Uso fonte sendo usada")
st.subheader("Custo da concessionária")
st.subheader("Custo apenas por gerador Diesel")

st.header("Otimização 2 - Prioriza o custo")
st.subheader("SOC")
st.subheader("Uso fonte sendo usada")
st.subheader("Custo da concessionária")
st.subheader("Custo apenas por gerador Diesel")

if not carga.empty and tarifa is not None:
    st.header("Uso apenas da rede")
    st.subheader("Custo da concessionária")
    valor_rede, curva_carga1=Uso_rede(carga["Potência (kW)"], Concessionaria(tarifa,0,"B"))
    valor_total_rede = sum(valor_rede)
    st.write(f"Valor total da fatura de energia elétrica: R$ {valor_total_rede:.2f}")
    st.line_chart(valor_rede)
    st.line_chart(curva_carga1)
    
if not carga.empty and "Diesel" in st.session_state:
    st.header("Uso apenas do gerador Diesel")
    st.subheader("Custo apenas por gerador Diesel")
    valor_diesel, curva_carga2, consumo_diesel = Uso_diesel(st.session_state["Diesel"], carga["Potência (kW)"])
    valor_total_diesel = sum(valor_diesel)
    st.write(f"Valor total da fatura de energia elétrica: R$ {valor_total_diesel:.2f}")
    st.line_chart(valor_diesel)
    st.line_chart(curva_carga2)

# Micro rede priorizando o gerador solar
# def micro_rede_solar(pot_carga, curva_irradiacao, pot_diesel):


# Função para calcular os custo operacionais
# tempo de vida útil em meses 
# def custos(tarifa_rede, custo_combustivel, vida_util_solar ,custo_instalacao_gerador, vida_util_bateria, custo_instalacao_bateria):
#     custo_solar = custo_instalacao_gerador/vida_util_solar
#     custo_bateria = (custo_instalacao_bateria/vida_util_bateria)
#     df = pd.DataFrame()
#     df["Indice"] = ["Tarifa da Rede (R$/kWh)", "Custo do Combustível (R$/kWh)", "Custo do Gerador Solar (R$/kWh)", "Custo da Bateria (R$/kWh)"]
#     df["Custo (R$)"] = [tarifa_rede, custo_combustivel, custo_solar, custo_bateria]
#     return df


# def Dia(consumo_carga, solar, concessionaria, diesel, bateria):
#     curva_solar = solar.curva
#     nivel_bateria = bateria.Nivel
#     nivel_diesel = diesel.nivel
#     for  i, consumo in enumerate(consumo_carga["Potência"]):
#         pot_solar =solar[i]["Potência"] 
#         if consumo<pot_solar:
#             if bateria.Nivel<bateria.capacidade_max:
#                 bateria.Carrega(pot_solar-consumo)
#             else: 
#                 print("Vende para rede")
#         else:
#             valor_diesel = diesel.Preco_diesel(consumo)
#             valor_rede = concessionaria.Preco(consumo)
#             if valor_rede>valor_diesel:
#                 diesel.Consumo(consumo )


# st.button("Rodar Simulação")
# st.button("Exportar Resultados")
if st.button("Cancelar"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()