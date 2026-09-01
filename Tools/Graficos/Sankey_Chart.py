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
            pad = 20,
            thickness = 25,
            line = dict(color = "black", width = 1),
            label = [f"<b>{n}</b>" for n in nodes],
            color = ["#A9A9A9", "#32CD32", "#4169E1", "#8B4513", "#FFD700", "#FF4500", "#636EFA"]
        ),
        link = dict(
            source = links["source"],
            target = links["target"],
            value = links["value"],
            color = "rgba(160, 160, 160, 0.4)",
            hovertemplate = "<b>%{source.label} ➔ %{target.label}</b><br>Energia: %{value:,.2f} kWh<extra></extra>",
        )
    )])
    fig.update_layout(
        font=dict(size=15, color="black", family="Arial, sans-serif"),
        height=420,
        margin=dict(l=25, r=25, t=30, b=25)
    )
    
    st.plotly_chart(fig, config={"displayModeBar": True}, width='stretch', key=key)