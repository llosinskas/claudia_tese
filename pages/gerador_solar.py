import streamlit as st 
import pandas as pd

st.set_page_config(
    page_title="Gerador Solar", 
    page_icon=":sun_with_face:", 
    layout="wide"
)

st.session_state["arquivo_irradiacao"] = None
st.title("Gerador Solar")
potencia = st.text_input("Potência nominal instalada (kWp)")
consumo = st.text_input("Consumo específico (kWh/m²)")

curva_irradiacao = st.file_uploader("Curva de irradiação (kW/m²)", type=["csv", "xlsx", "xls"])
st.session_state["arquivo_irradiacao"] = curva_irradiacao

if not curva_irradiacao:
    st.warning("Por favor, carregue um arquivo de curva de irradiação.")
else:
    df = pd.read_excel(curva_irradiacao) if curva_irradiacao.name.endswith(('.xlsx', '.xls')) else pd.read_csv(curva_irradiacao)   

    if "Hora" in df.columns:
        try:
            df["Hora"] = pd.to_datetime(df["Hora"], format="%H:%M:%S")
            df = df.set_index("Hora")

            novo_indice = pd.date_range(df.index.min(), df.index.max(), freq="15T")
            tempo = []
            aux = 0
            while aux < 1390:
                tempo.append(aux)
                aux += 15
            df_15min = pd.DataFrame()
           
            df_interp = df.reindex(novo_indice)
            df_15min = df_interp.interpolate(method="linear")
            df_15min["tempo (min)"] = tempo
            df_15min.set_index("tempo (min)", inplace=True)

            
            st.write(df_15min)
        
            st.session_state["curva_irradiacao"] = df_15min
            
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
            st.error("Certifique-se de que o arquivo contém uma coluna 'Hora' com valores no formato HH:MM:SS")
    

area = st.text_input("Área do painel (m²)")
curva = st.file_uploader("Curva de eficiência (%)", type=["csv", "xlsx", "xls"])
emissao = st.text_input("Emissão de CO2 (g/kWh)")
custo_instalacao = st.text_input("Custo de instalação (R$/kWp)")
tempo_resposta = st.text_input("Tempo de resposta (s)")
