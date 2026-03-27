import streamlit as st
import plotly.graph_objects as go
from models.Microrrede import Microrrede, Concessionaria, Solar, Biogas, Bateria, Diesel, Carga

def sankey_chart(uso_diesel, uso_bateria, uso_concessionaria, uso_biogas, uso_solar, sobra, carga):

    nodes = ["Diesel", "Bateria", "Concessionária", "Biogás", "Solar",  "Venda", "Microrrede",]
    links = {
        "source": [0,1,2,3,4,6], 
        "target": [6,6,6,6,6,5],
        "value":  [uso_diesel, uso_bateria, uso_concessionaria, uso_biogas, uso_solar, sobra, carga]
    }
    fig = go.Figure(data=[go.Sankey(
        node = dict(
        pad = 15,
        thickness = 20,
        line = dict(color = "black", width = 0.5),
        label = nodes,
        color = "blue"
        ),
        link = dict(
        source = links["source"],
        target = links["target"],
        value = links["value"]
    ))])
    
    st.plotly_chart(fig, config={"displayModeBar": True}, use_container_width=True)