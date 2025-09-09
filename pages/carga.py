import pandas as pd 
import streamlit as st

st.set_page_config(
    page_title="Carga", 
    page_icon=":fuelpump:", 
    layout="wide"
)
def exportar_carga(potencia, perfil, select):
    tempo = []
    aux = 0
    while aux < 1440:
        tempo.append(aux)
        aux += 15
        
    if select == "Carga fixa":
        df = pd.DataFrame({"tempo (min)":tempo, "Potência (kW)": float(potencia)})
        
        df = df[["tempo (min)", "Potência (kW)"]]
        # df.set_index("tempo (min)", inplace=True)
    if select == "Carga variável":
        if perfil is not None:
            df = pd.read_csv(perfil) if perfil.name.endswith('.csv') else pd.read_excel(perfil)
    return df


st.title("Carga")

select = st.selectbox("Selecione o tipo de carga", ["Carga fixa", "Carga variável"])

potencia = None
perfil = None
if select == "Carga fixa":
    potencia = st.text_input("Potência da carga (kW)", value=st.session_state["potencia"])

if select == "Carga variável":
    perfil = st.file_uploader("Perfil de carga (kW)", type=["csv", "xlsx", "xls"])

if st.button("Exportar carga"):
    df = exportar_carga(potencia, perfil, select)
    
    st.line_chart(data=df, x="tempo (min)", y="Potência (kW)")
    st.write(df)
    
    st.session_state["potencia"] = potencia
    st.session_state["carga"] = df

if st.button("Adicionar carga"):
    carga1 = st.text_input("potência da carga (kW)")
    tempo_liga = st.text_input("tempo que a carga liga (min)")
    tempo_desliga = st.text_input("tempo que a carga desliga (min)")