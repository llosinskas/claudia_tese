import streamlit as st
from database.database_config import Configure

from models.Microrrede import CriarMircrorrede, Microrrede

from models.Bateria import CriarBateria, BancoBateria
from models.Biogas import CriarBiogas, Biogas
from models.Carga import CriarCarga, Carga
from models.Concessionaria import CriarConcessionaria, Concessionaria
from models.Diesel import CriarDiesel, Diesel
from models.Solar import CriarSolar, Solar

from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
from streamlit_flow.layouts import TreeLayout, RadialLayout
import random
from uuid import uuid4

DATABASE_URL, engine, SessionLocal, Base = Configure()
st.set_page_config(
    layout="wide", 
    page_title="Página principal"
)
st.title("Microrredes")
try:
    session = SessionLocal()
#microrredes = session.query(Microrrede).all()
#for microrrede in microrredes:
#    st.write(f"Microrrede: {microrrede.nome} - Coordenadas: ({microrrede.coordenadas_x}, {microrrede.coordenadas_y})")
    st.subheader("Bancos de Baterias")
    with st.container():
        baterias = session.query(BancoBateria).all()
        for bateria in baterias:
            col1, col2, col3 = st.columns([3,3,1])
            col1.write(f"Potência: {bateria.potencia} kW")
            col2.write(f"Capacidade: {bateria.capacidade} kWh")
  
            if col3.button("Deletar", key=f"deletar_{bateria.id}"):
                session.delete(bateria)
                session.commit()
except Exception as e:
    st.error(f"Erro ao conectar ao banco de dados: {e}")

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



if st.button("Criar Banco de Dados"):
    CriarBateria()
    CriarBiogas()
    CriarCarga()
    CriarConcessionaria()
    CriarDiesel()
    CriarSolar()
    CriarMircrorrede() 