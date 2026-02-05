import streamlit as st
from models.Microrrede import Microrrede, Bateria, Biogas,Diesel, Carga, Solar, Concessionaria 
from database.database_config import Configure
 
import pydeck as pdk
from numpy.random import default_rng as rng
import pandas as pd 

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()
st.set_page_config(
    page_title="Microrredes", 
    page_icon=":sun_with_face:", 
    layout="wide"
)

biogases = session.query(Biogas).all()
diesels = session.query(Diesel).all()
cargas = session.query(Carga).all() 
concessionarias = session.query(Concessionaria).all()
solares = session.query(Solar).all()
baterias = session.query(Bateria).all()
try:
    session = SessionLocal()
except:
    pass

st.title("Microrredes")
nome_input = st.text_input("Nome da microrrede")
coordenada_x_input = st.text_input("Coordenada x")
coordenada_y_input = st.text_input("Coordenada y")

biogas_input = st.selectbox(
    "Biogás (kW)",
    options=[biogas for biogas in biogases] + ["Nenhum"])
diesel_input = st.selectbox("Diesel (kW)", options=[diesel for diesel in diesels] + ["Nenhum"])
carga_input = st.selectbox("Carga (kW)", options=[carga for carga in cargas] + ["Nenhum"])
solar_input = st.selectbox("Solar (kW)", options=[solar for solar in solares] + ["Nenhum"])
bateria_input = st.selectbox("Banco de bateria", options=[bateria for bateria in baterias] + ["Nenhum"])
concessionaria_input = st.selectbox("Concessionária (kW)", options=[concessionaria for concessionaria in concessionarias] + ["Nenhum"])

if st.button("Salvar"):
    Microrrede_ = Microrrede(
        nome=nome_input,
        coordenada_x=coordenada_x_input,
        coordenada_y=coordenada_y_input,    
        biogas=biogas_input if biogas_input != "Nenhum" else None,
        diesel=diesel_input if diesel_input != "Nenhum" else None,
        carga=carga_input if carga_input != "Nenhum" else None,
        solar=solar_input if solar_input != "Nenhum" else None,
        bateria=bateria_input if bateria_input != "Nenhum" else None,
        concessionaria=concessionaria_input if concessionaria_input != "Nenhum" else None
    )
    session.add(Microrrede_)    
    session.commit()
    st.success("Microrrede salva com sucesso!")

df = pd.DataFrame(
    rng(0).standard_normal((5, 2)) / [50, 50] + [-31.19, -54],
    columns=["lat", "lon"],
)

st.pydeck_chart(
    pdk.Deck(
        map_style=None,  # Use Streamlit theme to pick map style
        initial_view_state=pdk.ViewState(
            latitude=-31.19,
            longitude=-54,
            zoom=11,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                "HexagonLayer",
                data=df,
                get_position="[lon, lat]",
                radius=200,
                elevation_scale=4,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
            ),
            pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position="[lon, lat]",
                get_color="[200, 30, 0, 160]",
                get_radius=200,
            ),
        ],
    )
)