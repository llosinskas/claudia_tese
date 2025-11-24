import streamlit as st
from database.database_config import Configure
# from database.CRUD import ORM

from models.Microrrede import CriarMircrorrede, Microrrede

from models.Bateria import CriarBateria
from models.Biogas import CriarBiogas
from models.Carga import CriarCarga
from models.Concessionaria import CriarConcessionaria
from models.Diesel import CriarDiesel   
from models.Solar import CriarSolar

DATABASE_URL, engine, SessionLocal, Base = Configure()
st.set_page_config(
    layout="wide", 
    page_title="Página principal"
)
st.title("Microrredes")

session = SessionLocal()
microrredes = session.query(Microrrede).all()
#for microrrede in microrredes:
#    st.write(f"Microrrede: {microrrede.nome} - Coordenadas: ({microrrede.coordenadas_x}, {microrrede.coordenadas_y})")

if st.button("Criar Banco de Dados"):
    CriarBateria()
    CriarBiogas()
    CriarCarga()
    CriarConcessionaria()
    CriarDiesel()
    CriarSolar()
    CriarMircrorrede() 