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
    st.subheader("Microrredes cadastradas")
    with st.container():
        microrredes = Ler(Microrrede)
        for microrrede in microrredes:
            col1, col2, col3, col4 = st.columns([3,3,1,1])
            col1.header(f"Nome: {microrrede.nome}") 
            col2.subheader(f"Coordenadas: ({microrrede.coordenada_x}, {microrrede.coordenada_y})")
            col2.subheader("Concessionária:")
            col2.write(f"Nome:{microrrede.concessionaria.nome}, tarifa: R$ {microrrede.concessionaria.tarifa}")
            coordenadas.append((microrrede.coordenada_x, microrrede.coordenada_y))
            cargas = microrrede.carga.cargaFixa
            col1.subheader("Cargas:")
            curva_carga = np.zeros(1440)
            for carga in cargas:   
                col1.write(f"Carga: {carga.nome} - Potência: {carga.potencia} kW")
                curva_carga += np.array(Curva_carga(carga.potencia, carga.tempo_liga, carga.tempo_desliga))
            col1.line_chart(curva_carga, use_container_width=True)
            
            col1.subheader("Análise apenas da microrrede")
            col1.write("Custo de operação apenas com uma fonte de energia")
            concessionaria = Ler_Objeto(Concessionaria, microrrede.concessionaria.id)
            valores, total = array_valores_acumulado(concessionaria=concessionaria, cargas=curva_carga)
            col1.write(f"O valor total usando apenas a concessionária é R${total}")
            
            solar = Ler_Objeto(Solar, microrrede.solar.id)
            if not solar:
                col1.write("Não tem gerador solar")
            else:
                col2.subheader("Solar:")
                col2.write(f"Potência: {microrrede.solar.potencia} kW")
                col2.write(f"Custo por kWh: R$ {microrrede.solar.custo_kwh}")
                curva_solar = np.array(json.loads(microrrede.solar.curva_geracao))
                col2.line_chart(curva_solar, use_container_width=True)
                alerta = ""
                valores_solar, total_solar, alerta, curva_solar = Valor_solar(solar, curva_carga)
                col2.write(f"{alerta}")
                col2.write(f"O valor total usando apenas solar é R${total_solar}")
                
            if not Biogas:
                col2.write("Não tem gerador a Biogas")
            else:
                col2.subheader("Biogás:")   
                col2.write(f"Potência: {microrrede.biogas.potencia} kW")
            
            if not Diesel:
                col1.write("Não Possui Gerador Diesel")
            else:
                col1.subheader("Diesel:")
                col1.write(f"Potência: {microrrede.diesel.potencia} kW")        

            if not Bateria:
                col1.write("Não Possui Bateria")
            else: 
                col2.subheader("Baterias")
                col2.write(f"Potência: {microrrede.bateria.potencia} kW")

            

            st.header("Análises")
            
            df = pd.DataFrame({
                "Carga":curva_carga, 
                "Solar": curva_solar,
                "Venda":rng().integers(1, 200, size=1440),
                "Compra":rng().integers(1, 200, size=1440),

                #"Diesel":  
                #"Biogás": rng().integers(1, 15, size=10),     
                })
            st.area_chart(df)
            st.write("Balanço energético da microrrede 1 ao longo do tempo.")
            st.write("Valor total energia comprada Rede: R$ xx,xx")
            st.write("Valor total energia vendida Rede: R$ xx,xx")
            st.subheader("Níveis do geradores e baterias")
            niveis = pd.DataFrame({
                "Bateria":curva_carga, 
                "Biogas": curva_solar,
                "Diesel":curva_solar,
                
                #"Diesel":  
                #"Biogás": rng().integers(1, 15, size=10),     
                })
            st.area_chart(niveis)

            if col3.button("Deletar", key=f"deletar_{microrrede.id}"):
                Deletar(Microrrede, microrrede.id)
                st.rerun()

            if col4.button("Atualizar", key=f"atualizar_{microrrede.id}"):
                pass
                # atualizar_microrrede(microrrede)

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

#analise1.gerenciador_microrrede()
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
st.plotly_chart(fig,width=800,height=400)

DATABASE_URL, engine, SessionLocal, Base = Configure()

#microrredes = session.query(Microrrede).all()
#for microrrede in microrredes:
#    st.write(f"Microrrede: {microrrede.nome} - Coordenadas: ({microrrede.coordenadas_x}, {microrrede.coordenadas_y})")




st.subheader("Microrrede 2")


if st.button("Criar Banco de Dados"): 
    #CriarBateria()
    #CriarBiogas()
    #CriarCarga()
    #CriarConcessionaria()
    #CriarDiesel()
    #CriarSolar()
    #CriarMircrorrede()
    init_db()
    st.success("Banco de dados criado com sucesso!")
    
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
    except Exception as e:
        st.sidebar.error(f"Erro ao excluir o banco de dados: {e}")