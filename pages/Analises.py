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
st.text("Uso exclusivo de apenas uma fonte de energia durante o dia")
if st.button("Analise 1"): 
    for microrrede in microrredes:
        with st.container(border=True):
            st.header(f"{microrrede}", divider=True, width='stretch', text_alignment="center")
        
            total_carga, total_concessionaria, alerta_bateria, total_bateria, alerta_solar, total_solar, alerta_diesel, total_diesel, alerta_biogas, total_biogas, resultado_microrrede = analise_1(microrrede)
            col1, col2 = st.columns([5,5])

            col1.subheader("Consumo Concessionária")
            col1.text(f"Consumo total diário {total_carga:,.2f} kWh \n Custo de operar apenas pela rede R$ {total_concessionaria:,.2f}")
            
            col1.subheader("Consumo Bateria")
            col1.text(alerta_bateria)
            col1.text(f"Custo de operar apenas com a bateria R${total_bateria:,.2f}")
            
            col2.subheader("Consumo Solar")
            col2.text(alerta_solar)
            col2.text(f"Custo de operar apenas com Gerador Solar R${total_solar:,.2f}")
            
            col2.subheader("Consumo Diesel")
            col2.text(alerta_diesel)
            col2.text(f"Custo Diesel com apenas Gerador Diesel R${total_diesel:,.2f}")

            col2.subheader("Consumo Biogas")
            col2.text(alerta_biogas)
            col2.text(f"Custo Biogas com apenas uso do gerador Biogas R${total_biogas:,.2f}")

            st.dataframe(resultado_microrrede, hide_index=True)
            dataframe = pd.DataFrame({
                "Concessionaria": resultado_microrrede["Concessionaria"], 
                "Solar": resultado_microrrede['Solar'], 
                "Diesel": resultado_microrrede["Diesel"],
                "Biogas": resultado_microrrede["Biogas"], 
                "Bateria":resultado_microrrede["Bateria"]
            })
            st.line_chart(dataframe, x_label="Tempo (min)", y_label="Valor (R$)")
            

st.text("Uso otimizado das Fontes da microrrede")
if st.button("Analise 2"):
    #analise2(microrredes)
    for microrrede in microrredes:
        with st.container(border=True):
            custo_kwh_ordenado, total_uso_diesel, total_uso_bateria, total_uso_concessionaria, total_uso_biogas, total_uso_solar, total_sobra, total_carga, total, uso_energia, niveis_tanque, custo_total, custo_total_instantaneo = analise_2(microrrede)
            st.subheader(f"{microrrede}", divider=True, width='stretch', text_alignment='center')
            st.dataframe(custo_kwh_ordenado)
            st.text("Fluxo de energia (kWh)")
            sankey_chart(uso_diesel=total_uso_diesel, uso_bateria=total_uso_bateria, uso_concessionaria=total_uso_concessionaria, uso_biogas=total_uso_biogas, uso_solar=total_uso_solar, sobra=total_sobra, carga=total_carga)
            st.dataframe(total.style.format("{:,.2f} kWh"))

            st.line_chart(uso_energia, x_label="Tempo (min)", y_label="Potência (kW)")
            st.line_chart(niveis_tanque,x_label="Tempo (min)", y_label="Potência (kW)")
            st.subheader("Custo de energia da microrrede para operar")
            st.write(f"Custo total da microrrede: R$ {custo_total:,.2f}")
            st.line_chart(custo_total_instantaneo)

st.text("Uso otimizado das fontes e controle de cargas microrrede")
if st.button("Analise 3"):
    analise3(microrredes)
    analise4(microrredes)
st.text("Uso otimizado das redes com a compra e venda de energia entre as micorredes com a filosofia de eficiencia da microrrede")
if st.button("Analise 4"):
    analise4(microrredes)
st.text("Uso otimizado das redes com a compra e venda de energia entre as microrredes com a filosofia de eficiencia global")
if st.button("Análise 5"):
    analise5(microrredes) 
