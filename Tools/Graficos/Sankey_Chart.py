import streamlit as st
import plotly.graph_objects as go
from models.Microrrede import Microrrede, Concessionaria, Solar, Biogas, Bateria, Diesel, Carga

def sankey_chart(uso_diesel, uso_bateria, uso_concessionaria, uso_biogas, uso_solar, sobra, carga, key=None):

    nodes = ["Diesel", "Bateria", "Concessionária", "Biogás", "Solar",  "Venda", "Microrrede",]
    links = {
        "source": [0,1,2,3,4,6], 
        "target": [6,6,6,6,6,5],
        "value":  [uso_diesel, uso_bateria, uso_concessionaria, uso_biogas, uso_solar, sobra, carga]
    }
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 25,
            thickness = 35,
            line = dict(color = "black", width = 2),
            label = [f"<b>{n}</b>" for n in nodes],
            color = ["#A9A9A9", "#32CD32", "#4169E1", "#8B4513", "#FFD700", "#FF4500", "#636EFA"]
        ),
        link = dict(
            source = links["source"],
            target = links["target"],
            value = links["value"],
            color = "rgba(160, 160, 160, 0.4)",
            hovertemplate = "<b>%{source.label} ➔ %{target.label}</b><br>Energia: %{value:,.2f} kWh<extra></extra>",
        ),
        textfont = dict(size=16, color="black", family="Arial Black, sans-serif"),
    )])
    fig.update_layout(
        font=dict(size=16, color="black", family="Arial Black, sans-serif"),
        height=550,
        margin=dict(l=30, r=30, t=35, b=30)
    )
    
    st.plotly_chart(fig, config={"displayModeBar": True}, width='stretch', key=key)