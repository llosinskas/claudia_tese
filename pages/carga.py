import streamlit as st 
import pandas as pd 


st.set_page_config(
    page_title="Carga", 
    page_icon=":house:", 
    layout="wide"
)

st.title("Carga [kWh]")

uploaded_file = st.file_uploader("Escolha um arquivo da curva de carga",  type=["csv", "xlsx", "xls"])