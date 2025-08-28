import streamlit as st
import pandas as pd
from numpy.random import default_rng as rng


st.set_page_config(
    page_title="Gerenciador de Energia", 
    page_icon=":fuelpump:", 
    layout="wide"
)
st.title("Gerenciador de Energia")

df = pd.DataFrame(rng(0).standard_normal((20,1)), columns=["SOC"])
col1, col2, col3 = st.columns(3)
with col1:
    st.title("Demanda [kW]")
    st.line_chart(df)

    st.title("SOC da Bateria [kWh]")
    st.line_chart(df)
with col2:
    st.title("Curva da carga [kWh]")
    st.line_chart(df)
    st.title("Custo otimizado [R$]")
    st.line_chart(df)
with col3:
    st.title("Custo apenas da rede [R$]")
    st.line_chart(df)
    st.title("Custo apenas com gerador diesel [R$]")
    st.line_chart(df)
