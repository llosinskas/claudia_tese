import pandas as pd 
import streamlit as st
import numpy as np

from database.database_config import Configure
from models.Microrrede import Carga, CargaFixa
from models.CRUD import Criar, Ler, Deletar, Atualizar

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

st.set_page_config(
    page_title="Carga", 
    page_icon=":fuelpump:", 
    layout="wide"
)

def AddCarga(tipo, nomes, potencias, tempos_liga, tempos_desliga, prioridades):
    carga = Carga(
        tipo = tipo, 
    )
    cargasFixas = []
    
    for i in range(len(potencias)): 
        cargaFixa = CargaFixa(
            nome = nomes[i], 
            tempo_liga = tempos_liga[i], 
            tempo_desliga = tempos_desliga[i], 
            potencia = potencias[i], 
            prioridade = prioridades[i]
        )
        cargasFixas.append(cargaFixa)        
        curvas_array = Curva_carga(potencia=potencias[i], tempo_liga=tempos_liga[i], tempo_desliga = tempos_desliga[i])
        array = []
        for curva_array in enumerate(curvas_array):
            array.append(curva_array)
        
        cargasFixas.curva = array
    carga.carga_fixa_id = cargasFixas
    session.add(carga)
    session.commit()

def AddCargaFixa(nome, tempo_liga, tempo_desliga, potencia, prioridade):
    # Validar entradas
    if not tempo_liga or not str(tempo_liga).isdigit():
        raise ValueError("O campo 'tempo_liga' deve ser preenchido com um número válido.")
    if not tempo_desliga or not str(tempo_desliga).isdigit():
        raise ValueError("O campo 'tempo_desliga' deve ser preenchido com um número válido.")
    if not potencia or not str(potencia).replace('.', '', 1).isdigit():
        raise ValueError("O campo 'potencia' deve ser preenchido com um número válido.")
    if not prioridade or not str(prioridade).isdigit():
        raise ValueError("O campo 'prioridade' deve ser preenchido com um número válido.")

    cargafixa = CargaFixa(
        nome=nome,
        tempo_liga=int(tempo_liga),
        tempo_desliga=int(tempo_desliga),
        potencia=float(potencia),
        prioridade=int(prioridade)
    )
#    CriarCargaFixa(cargafixa)

def GerarCurva(carga_array, CargaFixa_id):
    for carga in range(carga_array):
        curva_carga = Curva_carga(
            valor = carga, 
            curva = CargaFixa_id
        )
        session.add(curva_carga)
        session.commit()

def Curva_carga(potencia, tempo_liga, tempo_desliga, min_dia=1440):
    carga_array = []
    for minuto in range(min_dia):
        if int(tempo_liga) <= minuto < int(tempo_desliga):
            carga_array.append(potencia)
        else:
            carga_array.append(0)
   
    return carga_array

def Somar_cargas(cargas_listas):
    min_dia = 1440
    carga_total = [0] * min_dia
    for carga_array in cargas_listas:
        for i in range(len(carga_array)):
            carga_total[i]+=carga_array
    return carga_total

def exportar_carga(potencia, perfil, select):
    tempo = []
    aux = 0
    while aux < 1440:
        tempo.append(aux)
        aux += 1
        
    if select == "Carga fixa":
        df = pd.DataFrame({"tempo (min)":tempo, "Potência (kW)": float(potencia)})
        df = df[["tempo (min)", "Potência (kW)"]]
        
    if select == "Carga variável":
        if perfil is not None:
            df = pd.read_csv(perfil) if perfil.name.endswith('.csv') else pd.read_excel(perfil)
    return df

if 'fields' not in st.session_state:
    st.session_state['fields'] = []
    st.session_state['count'] = 0

st.title("Carga")

select = st.selectbox("Selecione o tipo de carga", ["Carga fixa","Carga variável"])

nome_input = []
potencia_input = []
tempo_liga_input = []
tempo_desliga_input = []
prioridade_input = []

for i in range(st.session_state["count"]):
    col1, col2, col3 = st.columns([3,3,1])
    nome_input.append(col1.text_input(f"Nome da carga", key=f"nome_{i}"))
    potencia_input.append(col2.text_input(f"Potência da carga (kW) ", key=f"potencia_{i}"))
    tempo_liga_input.append(col3.text_input(f"Tempo (min) ", key=f"tempo_{i}"))
    tempo_desliga_input.append(col3.text_input(f"Tempo desligada (min) ", key=f"tempo_desliga_{i}"))
    prioridade_input.append(col1.selectbox(f"Prioridade (1-4) ", options=[1, 2, 3, 4], key=f"prioridade_{i}"))
if select == "Carga variável":
    perfil = st.file_uploader("Perfil de carga (kW)", type=["csv", "xlsx", "xls"])

col1, col2 = st.columns([1,1])
if col1.button("Adicionar carga"):
    st.session_state["count"] += 1  
    st.rerun()
   
    
if col2.button("Cancelar"):
    st.session_state["count"] = 0
    st.rerun()

col1, col2 = st.columns(2)
if col1.button("Salvar"):
    qdt_carga = st.session_state['count']
    for i in range(qdt_carga):
        nome_carga = nome_input[i]
        potencia_carga = potencia_input[i]
        tempo_liga_carga = tempo_liga_input[i]
        tempo_desliga_carga = tempo_desliga_input[i]
        prioridade_carga = prioridade_input[i]

        # Call AddCargaFixa for each set of values
        AddCargaFixa(nome_carga, tempo_liga_carga, tempo_desliga_carga, potencia_carga, prioridade_carga)

    st.success("Carga salva no banco de dados.")
   
try:
    st.subheader("Cargas Fixas Salvas")
    with st.container():
        cargas = Ler(CargaFixa)
        for carga in cargas:
            col21, col22, col23, col24 = st.columns([3,3,1,1])
            col21.write(f"Nome: {carga.nome}")
            col22.write(f"Potência: {carga.potencia} kW")
            col23.write(f"Tempo Ligada: {carga.tempo_liga} min")
            col24.write(f"Tempo Desligada: {carga.tempo_desliga} min")
        st.header("Adicionar Cargas a Microrrede")
        cargas_selecionadas = st.multiselect(
            "Selecione as cargas fixas para adicionar à microrrede:",
            options=[f"{carga.id} - {carga.nome}" for carga in cargas]
        )
        if st.button("Adicionar Cargas Selecionadas"):
            cargasid = [int(carga.split(" ")[0]) for 
                        carga in cargas_selecionadas]
            array_cargas = np.zeros(1440)
            
            for cargaid in cargasid:
                carga = session.query(CargaFixa).filter(CargaFixa.id == cargaid).first()
                for time in range(1440):
                    if time > carga.tempo_liga and time <= carga.tempo_desliga:
                        array_cargas[time] += carga.potencia
                
            st.line_chart(array_cargas)
           
            curva_demanda = Carga(
                demanda = array_cargas.tolist()
            )
            session.add(curva_demanda)
            session.commit()           
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")

