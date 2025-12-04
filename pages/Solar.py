import streamlit as st 
import pandas as pd
import numpy as np
from models.Solar import Solar, Criar, Atualizar, Ler, Deletar
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

st.set_page_config(
    page_title="Gerador Solar", 
    page_icon=":sun_with_face:", 
    layout="wide"
)

st.title("Gerador Solar")

curva_input = []
potencia_input = st.text_input("Potência nominal instalada (kWp)", value="")
custo_kwh_input = st.text_input("Custo do kWh para gerar energia (R$/kWh)")

tipo_input = st.selectbox("Selecione um tipo de input", options=["importar", "inserir manualmente"])

if tipo_input == "importar":
    endereco = st.file_uploader("Curva de irradiação (kW/m²)", type=["csv", "xlsx", "xls"])
    st.write("Formato do dados ['tempo (min)','Potencia (kWh)']")
    if not endereco:
        st.warning("Por favor, carregue um arquivo de curva de irradiação.")
    else:
        df = pd.read_excel(endereco) if endereco.name.endswith(('.xlsx', '.xls')) else pd.read_csv(endereco)   
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

elif tipo_input == "inserir manualmente":
    tempo = []
    potencia = []
    for t in range(24):
        tempo.append(t)
        potencia.append(0)
    data = {'Tempo (hora)':tempo,  'Potência gerada (kWh)': potencia}
    df = pd.DataFrame(data)
    df_solar = st.dataframe(df, hide_index=True)
   
col1,col2 = st.columns(2)
if col1.button("Salvar"):
    solar = Solar(
        file_path = endereco, 
        potencia = potencia_input, 
        custo_kwh = custo_kwh_input, 
        curva = curva_input
    )
if col2.button("Cancelar"):
    st.rerun()
