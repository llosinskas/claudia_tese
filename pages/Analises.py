import streamlit as st
import pandas as pd

from analises.PrioridadeMicro import Analise1, Analise2, Analise3, Analise4, analise_5_milp_multi, analise_5_milp, analise_6_pso, analise_6_pso_multi
from models.Microrrede import Microrrede
from models.CRUD import Ler
from otmizadores.exemplo_milp import exemplo_2_multiplas_microrredes
import numpy as np
from Tools.Graficos.BarChart import Grafico_barra 
from Tools.Graficos.Sankey_Chart import sankey_chart
from Tools.Graficos.LineChartMath import Grafico_linha


# Configuração da página
st.set_page_config(page_title="Simulador de Energia", layout="wide")
st.title("Simulador de Energia")
microrredes = Ler(Microrrede)
st.text("Uso exclusivo de apenas uma fonte de energia durante o dia")
if st.button("Analise 1"): 
    for microrrede in microrredes:
        with st.container(border=True):
            st.header(f"{microrrede}", divider=True, width='stretch', text_alignment="center")
        
            total_carga, total_concessionaria, alerta_bateria, total_bateria, alerta_solar, total_solar, alerta_diesel, total_diesel, alerta_biogas, total_biogas, resultado_microrrede = Analise1.analise_1(microrrede)
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

            fig = Grafico_linha(dataframe, "Tempo (min)", "Custo (R$)", "Custo do uso da fonte de energia (R$)")
            st.plotly_chart(fig)
            #fig2= Grafico_barra(dataframe, xlabel="Tempo (min)", ylabel="Carga (kW)",title="Carregamento da bateria (SOC)")
            #st.plotly_chart(fig2)

st.text("Uso otimizado das Fontes da microrrede")
if st.button("Analise 2"):
    for microrrede in microrredes:
        with st.container(border=True):
            custo_kwh_ordenado, total_uso_diesel, total_uso_bateria, total_uso_concessionaria, total_uso_biogas, total_uso_solar, total_sobra, total_carga, total, uso_energia, niveis_tanque, custo_total, custo_total_instantaneo = Analise2.analise_2(microrrede)
            st.subheader(f"{microrrede}", divider=True, width='stretch', text_alignment='center')
            st.dataframe(custo_kwh_ordenado)
            st.text("Fluxo de energia (kWh)")
            sankey_chart(uso_diesel=total_uso_diesel, uso_bateria=total_uso_bateria, uso_concessionaria=total_uso_concessionaria, uso_biogas=total_uso_biogas, uso_solar=total_uso_solar, sobra=total_sobra, carga=total_carga)
            st.dataframe(total.style.format("{:,.2f} kWh"))

            fig1 = Grafico_linha(uso_energia, "Tempo (min)", "Potência (kW)", "Uso da energia por fonte")
            st.plotly_chart(fig1)
            
            fig2 = Grafico_linha(niveis_tanque, xlabel="Tempo(min)", ylabel="Energia (kWh)", title = "Níveis de energia armazenados")
            st.plotly_chart(fig2)

            st.subheader("Custo de energia da microrrede para operar")
            st.write(f"Custo total da microrrede: R$ {custo_total:,.2f}")
            custo_total_instantaneo_df = pd.DataFrame({"Custo total instantaneo":custo_total_instantaneo })
            fig3 = Grafico_linha(custo_total_instantaneo_df,xlabel="Tempo (min)", ylabel="Custo (R$)", title="Custo total instâneo de operação (R$)")
            st.plotly_chart(fig3)

            #st.line_chart(custo_total_instantaneo)

st.text("Uso otimizado das fontes e controle de cargas microrrede")
if st.button("Analise 3"):
    for microrrede in microrredes:
        with st.container(border=True):
            st.subheader(f"{microrrede}", divider=True, width='stretch', text_alignment='center')
            custo_kwh_ordenado, total_uso_diesel, total_uso_bateria, total_uso_concessionaria, total_uso_biogas, total_uso_solar, total_sobra, total_carga,uso_solar, uso_bateria, uso_biogas, uso_diesel, uso_concessionaria, curva_carga,nivel_bateria, nivel_biogas, nivel_diesel,custo_total_instantaneo = Analise3.analise_3(microrrede)
            st.write("Custo por kWh de cada fonte de energia:")
            st.dataframe(custo_kwh_ordenado, hide_index=True)
            sankey_chart(uso_diesel=total_uso_diesel, uso_bateria=total_uso_bateria, uso_concessionaria=total_uso_concessionaria, uso_biogas=total_uso_biogas, uso_solar=total_uso_solar, sobra=total_sobra, carga=total_carga)
            total = pd.DataFrame({
                "Solar": total_uso_solar, 
                "Bateria": total_uso_bateria,
                "Biogas": total_uso_biogas,
                "Diesel": total_uso_diesel,
                "Concessionaria": total_uso_concessionaria,
                "Sobra": total_sobra
                }, index=[0])
            st.dataframe(total.style.format("{:,.2f} kWh"))

            uso_energia = pd.DataFrame({
                "Solar": uso_solar, 
                "Bateria": uso_bateria,
                "Biogas": uso_biogas,
                "Diesel": uso_diesel,
                "Concessionaria": uso_concessionaria,
                "Carga": curva_carga
                })
            fig1 = Grafico_linha(uso_energia, xlabel="Tempo (min)", ylabel="Potência (kW)", title="Uso da energia")
            st.plotly_chart(fig1)
            
            niveis_tanques = pd.DataFrame({
                "Bateria": nivel_bateria, 
                "Biogas": nivel_biogas,
                "Diesel": nivel_diesel,
                })
            
            fig2 = Grafico_linha(niveis_tanques, xlabel="Tempo (min)", ylabel="Energia (kWh)", title="Nível de Energia Armazenada")
            st.plotly_chart(fig2)
            
            custo_total = custo_total_instantaneo.sum()
            st.subheader("Custo de energia da microrrede para operar")
            st.write(f"Custo total da microrrede: R$ {custo_total:,.2f}")
            custo_total_instantaneo_df = pd.DataFrame({"Custo (R$)":custo_total_instantaneo})
            fig3 = Grafico_linha(custo_total_instantaneo_df, xlabel="Tempo (min)", ylabel="Custo (R$)", title="Custo de energia da microrrede para operar")
            st.plotly_chart(fig3)
            
    #Analise3.analise_3(microrredes)
    #Analise4.analise4(microrredes)
st.text("Comparação entre Análise 3 (Heurística) e Análise 5 (MILP)")
if st.button("Comparação de Custos"):
    for microrrede in microrredes:
        with st.container(border=True):
            st.subheader(f"{microrrede} - Comparação de Custos", divider=True, width='stretch', text_alignment='center')
            
            # Executar Análise 3
            with st.spinner("Executando Análise 3 (Heurística)..."):
                custo_kwh_ordenado_a3, total_uso_diesel_a3, total_uso_bateria_a3, total_uso_concessionaria_a3, total_uso_biogas_a3, total_uso_solar_a3, total_sobra_a3, total_carga_a3, uso_solar_a3, uso_bateria_a3, uso_biogas_a3, uso_diesel_a3, uso_concessionaria_a3, curva_carga_a3, nivel_bateria_a3, nivel_biogas_a3, nivel_diesel_a3, custo_total_instantaneo_a3 = Analise3.analise_3(microrrede)
            
            custo_total_a3 = custo_total_instantaneo_a3.sum()
            
            # Executar Análise 5
            with st.spinner("Executando Análise 5 (MILP)..."):
                from otmizadores.milp_controle_microrrede import analise_milp as analise_milp_func
                df_resultado_a5, custos_a5, solucao_a5 = analise_milp_func(microrrede)
            
            if df_resultado_a5 is None:
                st.error("❌ Não foi possível resolver MILP")
                continue
            
            custo_total_a5 = custos_a5.get('Total', 0)
            
            # ===== COMPARAÇÃO DE CUSTOS =====
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💰 Análise 3 (Heurística)", f"R$ {custo_total_a3:,.2f}")
            with col2:
                st.metric("🎯 Análise 5 (MILP)", f"R$ {custo_total_a5:,.2f}")
            with col3:
                economia = custo_total_a3 - custo_total_a5
                percentual = (economia / custo_total_a3 * 100) if custo_total_a3 > 0 else 0
                if economia >= 0:
                    st.metric("✅ Economia MILP", f"R$ {economia:,.2f}", f"{percentual:.1f}%", delta_color="inverse")
                else:
                    st.metric("⚠️ Custo Adicional", f"R$ {abs(economia):,.2f}", f"{abs(percentual):.1f}%")
            
            # ===== GRÁFICO DE CURVA DE CUSTO =====
            st.subheader("📈 Curva de Custo Acumulado")
            
            # Calcular custo acumulado para Análise 3
            custo_acumulado_a3 = np.cumsum(custo_total_instantaneo_a3)
            
            # Calcular custo instantâneo para MILP
            bateria = microrrede.bateria
            diesel = microrrede.diesel
            biogas = microrrede.biogas
            solar = microrrede.solar
            concessionaria = microrrede.concessionaria
            
            custo_instantaneo_a5 = np.zeros(len(df_resultado_a5))
            for i in range(len(df_resultado_a5)):
                custo_i = 0
                if solar is not None:
                    custo_i += df_resultado_a5['Solar'].iloc[i] * solar.custo_kwh / 60
                if bateria is not None:
                    custo_i += df_resultado_a5['Bateria'].iloc[i] * bateria.custo_kwh / 60
                if diesel is not None:
                    custo_i += df_resultado_a5['Diesel'].iloc[i] * diesel.custo_por_kWh / 60
                if biogas is not None:
                    custo_i += df_resultado_a5['Biogas'].iloc[i] * biogas.custo_por_kWh / 60
                if concessionaria is not None:
                    custo_i += df_resultado_a5['Concessionaria'].iloc[i] * concessionaria.tarifa / 60
                    # Desconta receita de venda
                    custo_i -= df_resultado_a5['Venda'].iloc[i] * concessionaria.tarifa * 0.8 / 60
                custo_instantaneo_a5[i] = custo_i
            
            custo_acumulado_a5 = np.cumsum(custo_instantaneo_a5)
            
            # Criar DataFrame para gráfico
            df_comparacao = pd.DataFrame({
                "Análise 3 (Heurística)": custo_acumulado_a3,
                "Análise 5 (MILP)": custo_acumulado_a5
            })
            
            fig = Grafico_linha(df_comparacao, 
                               xlabel="Tempo (min)", 
                               ylabel="Custo Acumulado (R$)", 
                               title="Custo Acumulado ao Longo do Dia")
            st.plotly_chart(fig, use_container_width=True)
            
            # ===== GRÁFICO DE CUSTO INSTANTÂNEO =====
            st.subheader("⏱️ Custo Instantâneo")
            
            df_custo_inst = pd.DataFrame({
                "Análise 3": custo_total_instantaneo_a3,
                "Análise 5": custo_instantaneo_a5
            })
            
            fig2 = Grafico_linha(df_custo_inst,
                                xlabel="Tempo (min)",
                                ylabel="Custo (R$)",
                                title="Custo Instantâneo de Operação")
            st.plotly_chart(fig2, use_container_width=True)
            
            # ===== TABELA COMPARATIVA =====
            st.subheader("📊 Resumo Comparativo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Análise 3 (Heurística)**")
                df_resumo_a3 = pd.DataFrame({
                    'Fonte': ['Solar', 'Bateria', 'Diesel', 'Biogas', 'Concessionária'],
                    'Energia (kWh)': [
                        f"{total_uso_solar_a3:.2f}",
                        f"{total_uso_bateria_a3:.2f}",
                        f"{total_uso_diesel_a3:.2f}",
                        f"{total_uso_biogas_a3:.2f}",
                        f"{total_uso_concessionaria_a3:.2f}"
                    ]
                })
                st.dataframe(df_resumo_a3, hide_index=True)
            
            with col2:
                st.write("**Análise 5 (MILP)**")
                df_resumo_a5 = pd.DataFrame({
                    'Fonte': ['Solar', 'Bateria', 'Diesel', 'Biogas', 'Concessionária'],
                    'Energia (kWh)': [
                        f"{df_resultado_a5['Solar'].sum():.2f}",
                        f"{df_resultado_a5['Bateria'].sum():.2f}",
                        f"{df_resultado_a5['Diesel'].sum():.2f}",
                        f"{df_resultado_a5['Biogas'].sum():.2f}",
                        f"{df_resultado_a5['Concessionaria'].sum():.2f}"
                    ]
                })
                st.dataframe(df_resumo_a5, hide_index=True)

st.text("Uso otimizado das redes com a compra e venda de energia entre as micorredes com a filosofia de eficiencia da microrrede")
if st.button("Analise 4 Heurística com todas as otmizações "):
    #analise4(microrredes)
    pass
st.text("Uso otimizado das redes com a compra e venda de energia entre as microrredes com a filosofia de eficiencia global")
if st.button("Análise 5 - MILP"):
    for microrrede in microrredes:
        with st.container(border=True):
            analise_5_milp(microrrede)
    analise_5_milp_multi(microrredes)

st.text("Otimização usando Particle Swarm Optimization (PSO) - Metaheurística")
if st.button("Análise 6 - PSO"):
    for microrrede in microrredes:
        with st.container(border=True):
            analise_6_pso(microrrede)
    analise_6_pso_multi(microrredes)