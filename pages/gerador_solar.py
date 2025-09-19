import streamlit as st 
import pandas as pd
from scipy.interpolate import interp1d
import numpy as np

st.set_page_config(
    page_title="Gerador Solar", 
    page_icon=":sun_with_face:", 
    layout="wide"
)

st.session_state["arquivo_irradiacao"] = None
st.title("Gerador Solar")
potencia = st.text_input("Potência nominal instalada (kWp)")
consumo = st.text_input("Consumo específico (kWh/m²)")

curva_irradiacao = st.file_uploader("Curva de irradiação (kW/m²)", type=["csv", "xlsx", "xls"])
st.session_state["arquivo_irradiacao"] = curva_irradiacao

if not curva_irradiacao:
    st.warning("Por favor, carregue um arquivo de curva de irradiação.")
else:
    df = pd.read_excel(curva_irradiacao) if curva_irradiacao.name.endswith(('.xlsx', '.xls')) else pd.read_csv(curva_irradiacao)   

    irradicao = df["irradiacao"]
    curva_interpolada = []
    irr_min = 0 
    irr_max= 0
    for i,irr in enumerate(irradicao):
        passo = (irr-irr_min)/60
        valor=irr_min
        for aux in range(60):
            valor+=passo            
            curva_interpolada.append(valor)
        irr_min = irr

    df2 = pd.DataFrame({"tempo (min)":np.arange(len(curva_interpolada)), "Potência":curva_interpolada})
    st.line_chart(curva_interpolada)
    st.session_state["arquivo_irradiacao"] = df2

area = st.text_input("Área do painel (m²)")
curva = st.file_uploader("Curva de eficiência (%)", type=["csv", "xlsx", "xls"])
emissao = st.text_input("Emissão de CO2 (g/kWh)")
custo_instalacao = st.text_input("Custo de instalação (R$/kWp)")
tempo_resposta = st.text_input("Tempo de resposta (s)")

class Solar:
    def __init__(self, potencia, curva):
        self.potencia = potencia
        self.curva = curva