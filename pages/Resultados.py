import streamlit as st
import pandas as pd 
import numpy as np 
from models.CRUD import Ler, Ler_Objeto
from models.Microrrede import Microrrede
import json

st.set_page_config(
    page_title="Resultados", 
    page_icon="chart_with_upwards_trend", 
    layout="wide"
)
st.title("Resultados")

