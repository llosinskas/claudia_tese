# Banco de dados
from sqlalchemy import MetaData
from models import init_db
from database.database_config import Configure
from models.Microrrede import Microrrede, Concessionaria, Solar, Biogas, Bateria, Diesel
from models.CRUD import  Ler, Deletar, Ler_Objeto
from database.database_config import Configure
#Interface
import streamlit as st
import plotly.graph_objects as go 
import pydeck as pdk
# Tools
import numpy as np
import pandas as pd
from numpy.random import default_rng as rng
import json
from Tools.GerarCurvaCarga import Curva_carga
from Tools.PrecoConcessionaria import array_valores_acumulado
from Tools.geradorSolar import Valor_solar
from GerenciadorMicrorrede.Gerenciador import Gerenciador


# Configuração do banco de dados
DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()
st.set_page_config(
    layout="wide", 
    page_title="Página principal"
)

st.title("Análises de Microrredes")

coordenadas = []
try:
    
    microrredes = Ler(Microrrede)

    if microrredes is None:
        st.subheader("Cadastre as microrredes!")
        st.write(microrredes)
    else:
        with st.container():
            st.subheader("Microrredes cadastradas")
            microrredes = Ler(Microrrede)
            for microrrede in microrredes:
                st.header(f"Microrrede: {microrrede.nome}",width="stretch", text_alignment="center", divider=True)
                
                col1, col2 = st.columns([5,5], border=True)
                col1.text(f"Localização geográfica: lat:{microrrede.coordenada_x}, lon:{microrrede.coordenada_y}", width="stretch", text_alignment='center')
                cargas = microrrede.carga.cargaFixa
                col1.subheader("Curva de carga:", text_alignment='center', width='stretch')
                curva_carga = np.zeros(1440)
                cargas_nome = []
                cargas_potencia = []
                tempos_liga = []
                tempos_desliga = []
                for carga in cargas:   
                    cargas_nome.append(carga.nome)
                    cargas_potencia.append(carga.potencia)
                    tempos_liga.append(carga.tempo_liga)
                    tempos_desliga.append(carga.tempo_desliga)
                    curva_carga += np.array(Curva_carga(carga.potencia, carga.tempo_liga, carga.tempo_desliga))
                df_cargas = pd.DataFrame({"Carga": cargas_nome, "Potência (kW)": cargas_potencia, "Tempo liga (min)":tempos_liga, "Tempo desliga (min)":tempos_desliga})
                col1.line_chart(curva_carga, width='stretch', x_label="Tempo (min)", y_label="Potência (kW)")
                col1.dataframe(df_cargas, hide_index=True)
                
                
                col1.subheader("Concessionária:")
            
                col1.text(f"Nome: {microrrede.concessionaria.nome}\nTarifa: R$ {microrrede.concessionaria.tarifa:,.2f}\nGrupo: {microrrede.concessionaria.grupo}", text_alignment='justify', width='stretch')
                coordenadas.append((microrrede.coordenada_x, microrrede.coordenada_y))
                    
                solar = Ler_Objeto(Solar, microrrede.solar.id)
                if microrrede.solar == None:
                    col1.write("Não tem gerador solar")
                else:
                    col2.subheader("Solar:")
                    col2.text(f"Potência: {microrrede.solar.potencia:,.2f} kW")
                    col2.text(f"Custo por kWh: R$ {microrrede.solar.custo_kwh:,.2f}")
                    curva_solar = np.array(json.loads(microrrede.solar.curva_geracao))
                    df = pd.DataFrame({
                        "Solar": curva_solar, 
                        "Carga":curva_carga
                    })
                    col2.subheader("Curva de cargas da microrrede e Geração")
                    col2.area_chart(df,
                                    x_label="Tempo (min)",
                                    y_label="Demanda (kWh)", 
                                    width='stretch')
                    
                    
                if microrrede.biogas == None:
                    col2.write("Não possui gerador a Biogas")
                else:
                    col2.subheader("Biogás:")   
                    col2.text(f"Potência: {microrrede.biogas.potencia:,.2f} kW\nTanque: {microrrede.biogas.tanque:,.2f} m³\nGeração diária: {microrrede.biogas.geracao:,.2f} m³/dia\nConsumo a 50% {microrrede.biogas.consumo_50:,.2f} m³/kWh\nConsumo 75% {microrrede.biogas.consumo_75:,.2f} m³/kWh\nConsumo 100% {microrrede.biogas.consumo_100:,.2f} m³/kWh\nCusto por kWh: {microrrede.biogas.custo_por_kWh:,.2f} R$/kWh")
                
                if microrrede.diesel == None:
                    col1.write("Não Possui Gerador Diesel")
                else:
                    col1.subheader("Diesel:")
                    col1.text(f"Potência: {microrrede.diesel.potencia:,.2f} kW\nTanque: {microrrede.diesel.tanque:,.2f} l\nConsumo a 50% {microrrede.diesel.consumo_50:,.2f} l/kWh\nConsumo 75% {microrrede.diesel.consumo_75:,.2f} l/kWh\nConsumo 100% {microrrede.diesel.consumo_100:,.2f} l/kWh\nCusto por kWh: {microrrede.diesel.custo_por_kWh:,.2f} R$/kWh")
                
                if microrrede.bateria == None:
                    col1.write("Não Possui Bateria")
                else: 
                    col2.subheader("Baterias")
                    col2.text(f"Potência: {microrrede.bateria.potencia:,.2f} kW\nCapacidade {microrrede.bateria.capacidade:,.2f} kWh\nTecnologia da bateria: {microrrede.bateria.bateria}\nEficiência: {microrrede.bateria.eficiencia} %\nCapacidade máxima: {microrrede.bateria.capacidade_max} %\nCapacidade mínima: {microrrede.bateria.capacidade_min} %\nCusto por kWh: {microrrede.bateria.custo_kwh} R$/kWh")
                
                if col2.button("Deletar", key=f"deletar_{microrrede.id}"):
                    Deletar(Microrrede, microrrede.id)
                    st.rerun()

                
                st.divider()
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")

df = pd.DataFrame(
    coordenadas,
    columns=["lat", "lon"],
)

st.pydeck_chart(
    pdk.Deck(
        map_style=None,  # Use Streamlit theme to pick map style
        initial_view_state=pdk.ViewState(
            latitude=df['lat'].mean(),
            longitude=df['lon'].mean(),
            zoom=7,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position="[lon, lat]",
                get_color="[200, 30, 0, 160]",
                get_radius=3000,
            ),
        ],
    )
)
    
# Sidebar for database management
st.sidebar.title("Gerenciamento do Banco de Dados")
if st.sidebar.button("Excluir Todo o Banco de Dados"):
    try:

        
# Obter todas as tabelas do banco de dados
        meta = MetaData()
        meta.reflect(bind=engine)

# Limpar os dados de todas as tabelas
        for table in reversed(meta.sorted_tables):  # Reverso para respeitar dependências
            session.execute(table.delete())

# Confirmar as alterações
        session.commit()

        Base.metadata.drop_all(engine)  # Exclui todas as tabelas
        st.sidebar.success("Todas as tabelas foram excluídas com sucesso!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Erro ao excluir o banco de dados: {e}")