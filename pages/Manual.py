import streamlit as st 
import graphviz
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
from streamlit_flow.layouts import TreeLayout, RadialLayout

st.set_page_config(
    page_title="Manual do Usuário", 
    page_icon=":book:", 
    layout="wide"
)
st.title("Manual do Usuário")


st.header("Otimização de microrredes de energia")
graph = graphviz.Digraph()

graph.node("A", "Cadastro da microrrede", shape="box")
graph.node("B", "Lê parâmetros de energia ()", shape="box")



graph.edge("A", "Lê demandas de energia")
graph.edge("Lê demandas de energia", "Analisa recursos energéticos disponíveis na microrrede")
graph.edge("Analisa recursos energéticos disponíveis na microrrede", "Realiza otimização energética")




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



st.graphviz_chart(graph)