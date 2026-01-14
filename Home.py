import streamlit as st
from database.database_config import Configure
import pandas as pd
from numpy.random import default_rng as rng
import plotly.graph_objects as go 
from models.Microrrede import CriarMircrorrede, Microrrede
from models.Bateria import CriarBateria, Bateria
from models.Biogas import CriarBiogas, Biogas
from models.Carga import CriarCarga, Carga
from models.Concessionaria import CriarConcessionaria, Concessionaria
from models.Diesel import CriarDiesel, Diesel
from models.Solar import CriarSolar, Solar

from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
from streamlit_flow.layouts import TreeLayout, RadialLayout
from uuid import uuid4


nodes = ["Diesel", "Bateria", "Concessionária", "Biogás", "Solar", "Carga", "Venda"]
links = {
    "source": [0,0,2,3,4,5,6], 
    "target": [6,5,6,6,6,6],
    "value":  [10,12,6,0,1,1]
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
st.plotly_chart(fig, width=True)

DATABASE_URL, engine, SessionLocal, Base = Configure()
st.set_page_config(
    layout="wide", 
    page_title="Página principal"
)
st.title("Microrredes")
#microrredes = session.query(Microrrede).all()
#for microrrede in microrredes:
#    st.write(f"Microrrede: {microrrede.nome} - Coordenadas: ({microrrede.coordenadas_x}, {microrrede.coordenadas_y})")

# Interface das análises
st.subheader("Microrredes")

nodes = [StreamlitFlowNode("1", (0, 0), {'content': 'Microrrede 1'}, 'input', 'right'),
        StreamlitFlowNode("2", (1, 0), {'content': 'Microrrede 2'}, 'default', 'right', 'left'),
        StreamlitFlowNode("3", (2, 0), {'content': 'Microrrede 3'}, 'default', 'right', 'left'),
        ]

edges = [StreamlitFlowEdge("1-2", "1", "2", animated=True, marker_start={}, marker_end={'type': 'arrow'}),
        StreamlitFlowEdge("1-3", "1", "3", animated=True),
        ]

if 'curr_state' not in st.session_state:
    st.session_state.curr_state = StreamlitFlowState(nodes=nodes, edges=edges)
st.session_state.curr_page = streamlit_flow(
    "Microrredes", 
    st.session_state.curr_state, 
    layout=TreeLayout(direction="right"), 
    fit_view=True, 
    height=600,
    enable_node_menu=True, 
    enable_edge_menu=True, 
    enable_pane_menu=True, 
    get_edge_on_click=True, 
    get_node_on_click=True, 
    show_minimap=True, 
    allow_new_edges=True, 
    min_zoom=0.1   
    )

st.header("Análises")
st.subheader("Microrrede 1")
df = pd.DataFrame({
    "Solar": list(range(1, 11)),
    "Diesel": rng().integers(1, 20, size=10), 
    "Biogás": rng().integers(1, 15, size=10), 
    "rede": list(range(5, 15))
}
)
st.area_chart(df)
st.write("Balanço energético da microrrede 1 ao longo do tempo.")
st.write("Valor total energia comprada Rede: R$ xx,xx")
st.write("Valor total energia vendida Rede: R$ xx,xx")

st.subheader("Microrrede 2")


if st.button("Criar Banco de Dados"):
    CriarBateria()
    CriarBiogas()
    CriarCarga()
    CriarConcessionaria()
    CriarDiesel()
    CriarSolar()
    
    CriarMircrorrede() 