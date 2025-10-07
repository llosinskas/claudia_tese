import pandas as pd 
import streamlit as st
import numpy as np
st.set_page_config(
    page_title="Carga", 
    page_icon=":fuelpump:", 
    layout="wide"
)

if "cargas" not in st.session_state:
    st.session_state["cargas"] = []

def exportar_carga(potencia, perfil, select):
    tempo = []
    aux = 0
    while aux < 1440:
        tempo.append(aux)
        aux += 1
        
    if select == "Carga fixa":
        df = pd.DataFrame({"tempo (min)":tempo, "Potência (kW)": float(potencia)})
        
        df = df[["tempo (min)", "Potência (kW)"]]
        # df.set_index("tempo (min)", inplace=True)
    if select == "Carga variável":
        if perfil is not None:
            df = pd.read_csv(perfil) if perfil.name.endswith('.csv') else pd.read_excel(perfil)
    return df

def adicionar_carga():
    st.session_state["cargas"].append({"potencia": 0, "tempo_liga":0,"tempo_desliga":0})

st.title("Carga")

select = st.selectbox("Selecione o tipo de carga", ["Carga fixa", "Carga variável"])

potencia = None
perfil = None
if select == "Carga fixa":
    potencia = st.text_input("Potência da carga (kW)", value=st.session_state["potencia"])

if select == "Carga variável":
    perfil = st.file_uploader("Perfil de carga (kW)", type=["csv", "xlsx", "xls"])

if st.button("Adicionar carga"):
    adicionar_carga()

for i, carga in enumerate(st.session_state["cargas"]):
    st.write(f"Carga {i+1}")
    st.session_state["cargas"][i]["potencia"] = st.text_input(f"Potência da carga {i+1} kW", value=carga["potencia"], key=f"potencia_{i}")
    st.session_state["cargas"][i]["tempo_liga"] = st.text_input(f"Tempo em que liga a carga {i+1} (min)", value=carga["tempo_liga"], key=f"tempo_liga_{i}")
    st.session_state["cargas"][i]["tempo_desliga"] = st.text_input(f"Tempo em que desliga a carga {i+1} (min)", value=carga["tempo_desliga"], key=f"tempo_desliga_{i}")


if st.button("Exportar carga"):
    df = exportar_carga(potencia, perfil, select)
    
    for i, carga in enumerate(st.session_state["cargas"]):
        tempo_liga = int(st.session_state["cargas"][i]['tempo_liga'])
        tempo_desliga = int(st.session_state["cargas"][i]['tempo_desliga'])
        potencia = float(st.session_state["cargas"][i]['potencia'])
        tamanho = 1440
        df1 = pd.DataFrame({"tempo (min)":np.arange(tamanho), "Potência (kW)":np.zeros(tamanho)})
        df1.loc[tempo_liga:tempo_desliga, "Potência (kW)"]= potencia
        df["Potência (kW)"] = df["Potência (kW)"] + df1["Potência (kW)"]
    
    st.line_chart(data=df, x="tempo (min)", y="Potência (kW)")
    st.write(df)
    
    st.session_state["potencia"] = potencia
    st.session_state["carga"] = df

