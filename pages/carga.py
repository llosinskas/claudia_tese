import pandas as pd 
import streamlit as st
import numpy as np

from database.database_config import Configure
from models.Carga import Carga 

DATABASE_URL, engine, SessionLocal, Base = Configure()

st.set_page_config(
    page_title="Carga", 
    page_icon=":fuelpump:", 
    layout="wide"
)



def exportar_carga(potencia, perfil, select):
    tempo = []
    aux = 0
    while aux < 1440:
        tempo.append(aux)
        aux += 1
        
    if select == "Carga fixa":
        df = pd.DataFrame({"tempo (min)":tempo, "Potência (kW)": float(potencia)})
        df = df[["tempo (min)", "Potência (kW)"]]
        
    if select == "Carga variável":
        if perfil is not None:
            df = pd.read_csv(perfil) if perfil.name.endswith('.csv') else pd.read_excel(perfil)
    return df

if 'fields' not in st.session_state:
    st.session_state['fields'] = []

def adicionar_carga():
    for i, fields in enumerate(st.session_state['fields']):
        col1, col2, col3 = st.columns([3,3,1])

st.title("Carga")

select = st.selectbox("Selecione o tipo de carga", ["Carga fixa", "Carga variável"])

potencia = None
perfil = None
if select == "Carga fixa":
    potencia = st.text_input("Potência da carga (kW)")

if select == "Carga variável":
    perfil = st.file_uploader("Perfil de carga (kW)", type=["csv", "xlsx", "xls"])

if st.button("Adicionar carga"):
    adicionar_carga()



if st.button("Exportar carga"):
    df = exportar_carga(potencia, perfil, select)
    
    st.line_chart(data=df, x="tempo (min)", y="Potência (kW)")
    st.write(df)
    
    session = SessionLocal()
    carga = Carga(curva=df["Potência (kW)"].tolist())
    session.add(carga)
    session.commit()    
    st.success("Carga salva no banco de dados.")
    


