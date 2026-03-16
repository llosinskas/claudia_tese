import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from analises.PrioridadeMicro import analise_1, analise_2, analise3, analise4 
from analises.PrioridadeGestor import analise5
from models.Microrrede import Microrrede
from models.CRUD import Ler
from Tools.Graficos.Sankey_Chart import sankey_chart


# Configuração da página
st.set_page_config(page_title="Simulador de Energia", layout="wide")
st.title("Simulador de Energia")
microrredes = Ler(Microrrede)
st.text("Uso exclusido de apenas uma fonte de enerigia durante o dia")
if st.button("Analise 1"):
    for microrrede in microrredes:
        st.write(f"Microrrede:{microrrede}" )
        
        
        total_carga, total_concessionaria, alerta_bateria, total_bateria, alerta_solar, total_solar, alerta_diesel, total_diesel, alerta_biogas, total_biogas, resultado_microrrede = analise_1(microrrede)
       
        st.write(f"Consumo total diário {total_carga:,.2f} kWh \n Custo de operar apenas pela rede R$ {total_concessionaria:,.2f}")
        
        st.write(alerta_bateria)
        st.write(f"Custo de operar apenas com a bateria R${total_bateria:,.2f}")
        
        st.write(alerta_solar)
        st.write(f"Custo de operar apenas com Gerador Solar R${total_solar:,.2f}")
        
        st.write(alerta_diesel)
        st.write(f"Custo Diesel com apenas Gerador Diesel R${total_diesel:,.2f}")

        st.write(alerta_biogas)
        st.write(f"Custo Biogas com apenas uso do gerador Biogas R${total_biogas:,.2f}")

        st.dataframe(resultado_microrrede)


st.text("Uso otimizado das Fontes da microrrede")
if st.button("Analise 2"):
    #analise2(microrredes)
    for microrrede in microrredes:
        custo_kwh_ordenado, total_uso_diesel, total_uso_bateria, total_uso_concessionaria, total_uso_biogas, total_uso_solar, total_sobra, total_carga = analise_2(microrrede)
        st.subheader(f"{microrrede}")
        st.dataframe(custo_kwh_ordenado)
        st.write("Fluxo de energia")
        sankey_chart(uso_diesel=total_uso_diesel, uso_bateria=total_uso_bateria, uso_concessionaria=total_uso_concessionaria, uso_biogas=total_uso_biogas, uso_solar=total_uso_solar, sobra=total_sobra, carga=total_carga)


st.text("Uso otimizado das fontes e controle de cargas microrrede")
if st.button("Analise 3"):
    analise3(microrredes)

st.text("Uso otimizado das redes com a compra e venda de energia entre as micorredes com a filosofia de enficiencia da microrrede")
if st.button("Analise 4"):
    analise4(microrredes)
st.text("Uso otimizado das redes com a compra e venda de energia entre as microrredes com a filosofia de eficiencia global")
if st.button("Análise 5"):
    analise5(microrredes) 



# Entrada de demanda
#st.sidebar.header("Configuração da Demanda")

    
#tipo_demanda = st.sidebar.selectbox("Como deseja fornecer a demanda?", ["Automática", "Manual", "Arquivo CSV"])

#if tipo_demanda == "Automática":
#    st.sidebar.write("Demanda alternando entre 1.0kW e 2.5kW a cada 30 minutos.")
#    demanda_por_minuto = [1.0 if i % 60 < 30 else 2.5 for i in range(1440)]

#elif tipo_demanda == "Manual":
#    demanda_fixa = st.sidebar.slider("Demanda fixa (kW):", min_value=0.5, max_value=10.0, value=2.0, step=0.1)
#    demanda_por_minuto = [demanda_fixa for _ in range(1440)]

#elif tipo_demanda == "Arquivo CSV":
#    arquivo = st.sidebar.file_uploader("Faça upload de um arquivo CSV com a demanda (1440 valores, 1 por minuto):", type="csv")
#    if arquivo is not None:
#        df = pd.read_csv(arquivo)
#        if len(df) == 1440:
#           demanda_por_minuto = df.iloc[:, 0].tolist()
#        else:
#            st.sidebar.error("O arquivo deve conter exatamente 1440 valores.")
#            st.stop()
#    else:
#        st.sidebar.warning("Aguardando upload do arquivo.")
#        st.stop()

# Executar simulação
#st.header("Resultados da Simulação")
#if st.button("Executar Simulação"):
#    simulador = SimuladorEnergia(demanda_por_minuto)
#    simulador.simular()

    # Exibir relatório
 #   st.subheader("Relatório da Simulação")
   # resultados_df = pd.DataFrame(simulador.resultados)
    #st.dataframe(resultados_df)

    # Gráficos
  #  st.subheader("Gráficos")

    # Gráfico de demanda
   # st.write("### Demanda ao longo do dia")
    #plt.figure(figsize=(10, 6))
    #plt.plot(resultados_df['tempo'], resultados_df['demanda'], label='Demanda (kW)', color='blue')
#    plt.xlabel('Tempo')
#    plt.ylabel('Demanda (kW)')
#    plt.title('Demanda ao longo do dia')
#    plt.xticks(rotation=45, fontsize=8)
#    plt.legend()
#    st.pyplot(plt)

    # Gráfico de custo
 #   st.write("### Custo por fonte ao longo do dia")
#    plt.figure(figsize=(10, 6))
 #   plt.plot(resultados_df['tempo'], resultados_df['custo'], label='Custo (R$/h)', color='green')
#    plt.xlabel('Tempo')
#    plt.ylabel('Custo (R$)')
#    plt.title('Custo por fonte ao longo do dia')
#    plt.xticks(rotation=45, fontsize=8)
#    plt.legend()
#    st.pyplot(plt)

    # Gráfico de uso de fontes
 #   st.write("### Uso de Fontes ao longo do dia")
#    plt.figure(figsize=(10, 6))
 #   plt.hist(resultados_df['fonte'], bins=len(set(resultados_df['fonte'])), color='orange', edgecolor='black')
#    plt.xlabel('Fonte de Energia')
#    plt.ylabel('Frequência de Uso')
#    plt.title('Uso de Fontes ao longo do dia')
#    plt.tight_layout()
#    st.pyplot(plt)

#else:
 #   st.info("Configure a demanda e clique em 'Executar Simulação' para começar.")