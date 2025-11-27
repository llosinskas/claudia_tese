import streamlit as st 
import graphviz

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



st.graphviz_chart(graph)