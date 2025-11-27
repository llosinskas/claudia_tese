import streamlit as st 
import pandas as pd
import numpy as np
from models.Solar import Solar
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

st.set_page_config(
    page_title="Gerador Solar", 
    page_icon=":sun_with_face:", 
    layout="wide"
)

if "gerador_solar" not in st.session_state:
    st.session_state["gerador_solar"] = Solar(10, [], None)
gerador = Solar(0, [], None)
gerador = st.session_state['gerador_solar']


st.session_state["arquivo_irradiacao"] = None
st.title("Gerador Solar")
potencia = st.text_input("Potência nominal instalada (kWp)", value=gerador.potencia)

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

if st.button("Salvar"):
    curva_gerador = st.session_state['arquivo_irradiacao']
    gerador = Solar(potencia,curva_gerador,  curva_irradiacao)

if st.button("Cancelar"):
    del st.session_state['gerador_solar']
    st.rerun()
# area = st.text_input("Área do painel (m²)")
# curva = st.file_uploader("Curva de eficiência (%)", type=["csv", "xlsx", "xls"])
# emissao = st.text_input("Emissão de CO2 (g/kWh)")
# custo_instalacao = st.text_input("Custo de instalação (R$/kWp)")

