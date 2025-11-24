import streamlit as st
from database.database_config import Configure
# from database.CRUD import ORM

from models.Microrrede import CriarMircrorrede, Microrrede

from models.Bateria import CriarBateria, BancoBateria
from models.Biogas import CriarBiogas, Biogas
from models.Carga import CriarCarga, Carga
from models.Concessionaria import CriarConcessionaria, Concessionaria
from models.Diesel import CriarDiesel, Diesel
from models.Solar import CriarSolar, Solar

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

if st.button("Criar Banco de Dados"):
    CriarBateria()
    CriarBiogas()
    CriarCarga()
    CriarConcessionaria()
    CriarDiesel()
    CriarSolar()
    CriarMircrorrede() 