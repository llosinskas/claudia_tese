import streamlit as st
from models.Microrrede import Microrrede
from database.database_config import Configure


DATABASE_URL, engine, SessionLocal, Base = Configure()
st.set_page_config(
    page_title="Microrredes", 
    page_icon=":sun_with_face:", 
    layout="wide"
)


st.title("Microrredes")
nome = st.text_input("Nome da microrrede")
coordenada_x = st.text_input("Coordenada x")
coordenada_y = st.text_input("Coordenada y")

if st.button("Salvar"):
    dados = {
        "nome" : nome, 
        "coordenada_x": coordenada_x, 
        "coordenada_y":coordenada_y
    }
    ORM.criar(session =SessionLocal,model_class =Microrrede, dados=dados)
