import streamlit as st
import pandas as pd

from analises.PrioridadeMicro import Analise1, Analise2, Analise3, Analise4, analise_5_milp_multi, analise_5_milp, analise_6_pso, analise_6_pso_multi
from models.Microrrede import Microrrede
from models.CRUD import Ler
from otmizadores.exemplo_milp import exemplo_2_multiplas_microrredes
from otmizadores.milp_controle_microrrede import analise_milp, analise_milp_sem_venda
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
    for idx, microrrede in enumerate(microrredes):
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
            st.plotly_chart(fig, key=f"analise1_custo_fonte_{idx}")
            #fig2= Grafico_barra(dataframe, xlabel="Tempo (min)", ylabel="Carga (kW)",title="Carregamento da bateria (SOC)")
            #st.plotly_chart(fig2)

st.text("Uso otimizado das Fontes da microrrede")
if st.button("Analise 2"):
    for idx, microrrede in enumerate(microrredes):
        with st.container(border=True):
            custo_kwh_ordenado, total_uso_diesel, total_uso_bateria, total_uso_concessionaria, total_uso_biogas, total_uso_solar, total_sobra, total_carga, total, uso_energia, niveis_tanque, custo_total, custo_total_instantaneo = Analise2.analise_2(microrrede)
            st.subheader(f"{microrrede}", divider=True, width='stretch', text_alignment='center')
            st.dataframe(custo_kwh_ordenado)
            st.text("Fluxo de energia (kWh)")
            sankey_chart(uso_diesel=total_uso_diesel, uso_bateria=total_uso_bateria, uso_concessionaria=total_uso_concessionaria, uso_biogas=total_uso_biogas, uso_solar=total_uso_solar, sobra=total_sobra, carga=total_carga)
            st.dataframe(total.style.format("{:,.2f} kWh"))

            fig1 = Grafico_linha(uso_energia, "Tempo (min)", "Potência (kW)", "Uso da energia por fonte")
            st.plotly_chart(fig1, key=f"analise2_uso_energia_{idx}")
            
            fig2 = Grafico_linha(niveis_tanque, xlabel="Tempo(min)", ylabel="Energia (kWh)", title = "Níveis de energia armazenados")
            st.plotly_chart(fig2, key=f"analise2_niveis_{idx}")

            st.subheader("Custo de energia da microrrede para operar")
            st.write(f"Custo total da microrrede: R$ {custo_total:,.2f}")
            custo_total_instantaneo_df = pd.DataFrame({"Custo total instantaneo":custo_total_instantaneo })
            fig3 = Grafico_linha(custo_total_instantaneo_df,xlabel="Tempo (min)", ylabel="Custo (R$)", title="Custo total instâneo de operação (R$)")
            st.plotly_chart(fig3, key=f"analise2_custo_{idx}")

            #st.line_chart(custo_total_instantaneo)

st.text("Uso otimizado das fontes e controle de cargas microrrede")
if st.button("Analise 3"):
    for idx, microrrede in enumerate(microrredes):
        with st.container(border=True):
            st.subheader(f"{microrrede}", divider=True)
            
            # Executa a análise com deslizamento de cargas
            with st.spinner("Executando Análise 3 com otimização de cargas..."):
                resultado_analise3 = Analise3.analise_3(microrrede)
            
            # Extrai resultados otimizados (com deslizamento)
            (custo_kwh_ordenado_ot, total_uso_diesel_ot, total_uso_bateria_ot, total_uso_concessionaria_ot, 
             total_uso_biogas_ot, total_uso_solar_ot, total_sobra_ot, total_carga_ot, uso_solar_ot, 
             uso_bateria_ot, uso_biogas_ot, uso_diesel_ot, uso_concessionaria_ot, curva_carga_ot, 
             nivel_bateria_ot, nivel_biogas_ot, nivel_diesel_ot, custo_total_instantaneo_ot, carga_bateria_ot,
             venda_ot, receita_venda_ot, total_venda_ot, total_receita_venda_ot) = resultado_analise3['otimizado']
            
            # Extrai resultados originais (sem deslizamento)
            (custo_kwh_ordenado_or, total_uso_diesel_or, total_uso_bateria_or, total_uso_concessionaria_or, 
             total_uso_biogas_or, total_uso_solar_or, total_sobra_or, total_carga_or, uso_solar_or, 
             uso_bateria_or, uso_biogas_or, uso_diesel_or, uso_concessionaria_or, curva_carga_or, 
             nivel_bateria_or, nivel_biogas_or, nivel_diesel_or, custo_total_instantaneo_or, carga_bateria_or,
             venda_or, receita_venda_or, total_venda_or_val, total_receita_venda_or_val) = resultado_analise3['original']
            
            custo_total_ot = custo_total_instantaneo_ot.sum()
            custo_total_or = custo_total_instantaneo_or.sum()
            
            # Calcula economia
            economia = custo_total_or - custo_total_ot
            economia_pct = (economia / custo_total_or * 100) if custo_total_or > 0 else 0
            
            # ===== MÉTRICAS RESUMIDAS =====
            st.markdown("### 📊 Resumo de Operação (COM DESLIZAMENTO DE CARGAS)")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("💰 Custo Total", f"R$ {custo_total_ot:,.2f}", f"-R$ {economia:,.2f}" if economia > 0 else f"+R$ {abs(economia):,.2f}")
            with col2:
                cobertura_local = ((total_carga_ot - total_uso_concessionaria_ot) / total_carga_ot * 100) if total_carga_ot > 0 else 0
                st.metric("🏠 Cobertura Local", f"{cobertura_local:.1f}%")
            with col3:
                aproveitamento_solar = (total_uso_solar_ot / (total_uso_solar_ot + total_sobra_ot) * 100) if (total_uso_solar_ot + total_sobra_ot) > 0 else 0
                st.metric("☀️ Aproveit. Solar", f"{aproveitamento_solar:.1f}%")
            with col4:
                st.metric("📦 Demanda Total", f"{total_carga_ot:,.2f} kWh")
            with col5:
                st.metric("📊 Economia", f"{economia_pct:.1f}%")
            
            # ===== ABAS ORGANIZADAS =====
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 Fluxo de Energia", "🔋 Armazenamento", "💵 Custos", "🎯 Resumo de Fontes", "📋 Detalhes", "🔄 Comparação"])
            
            # TAB 1: FLUXO DE ENERGIA
            with tab1:
                st.markdown("#### Despacho de Energia ao Longo do Dia (COM DESLIZAMENTO)")
                demanda_negativa_ot = -np.abs(np.array(curva_carga_ot))
                uso_energia_ot = pd.DataFrame({
                    "Solar": uso_solar_ot, 
                    "Diesel": uso_diesel_ot,
                    "Biogas": uso_biogas_ot,
                    "Concessionaria": uso_concessionaria_ot,
                    "Descarga Bateria": uso_bateria_ot,
                    "Carga Bateria": -carga_bateria_ot,
                    "Venda": venda_ot,
                    "Carga (Demanda)": demanda_negativa_ot
                })
                fig1 = Grafico_linha(uso_energia_ot, xlabel="Tempo (min)", ylabel="Potência (kW)", title="Positivo = Fornecimento | Negativo = Consumo/Carregamento")
                st.plotly_chart(fig1, use_container_width=True)
                
                st.markdown("**Legenda:**")
                st.write("- 📈 **Acima do zero**: Fontes gerando/fornecendo energia")
                st.write("- 📉 **Abaixo do zero**: Demanda de carga e carregamento de bateria")
                st.write("- 💱 **Venda**: Energia excedente vendia para a rede")
                st.info("💡 Observe como as cargas com prioridade 2 e 4 foram movidas para horários de menor custo operacional")
                
                # Resumo de venda
                st.divider()
                st.markdown("#### 📤 Resumo de Venda para a Rede")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📤 Total Vendido", f"{total_venda_ot:,.2f} kWh")
                with col2:
                    st.metric("💵 Receita de Venda", f"R$ {total_receita_venda_ot:,.2f}")
                with col3:
                    st.metric("Tarifa de Venda", "80% da compra")
            
            # TAB 2: ARMAZENAMENTO
            with tab2:
                st.markdown("#### Evolução dos Níveis de Armazenamento (COM DESLIZAMENTO)")
                niveis_tanques_ot = pd.DataFrame({
                    "Bateria (kWh)": nivel_bateria_ot, 
                    "Biogas (m³)": nivel_biogas_ot,
                    "Diesel (L)": nivel_diesel_ot,
                })
                fig2 = Grafico_linha(niveis_tanques_ot, xlabel="Tempo (min)", ylabel="Energia/Volume", title="Dinâmica dos Sistemas de Armazenamento")
                st.plotly_chart(fig2, use_container_width=True)
                
                st.divider()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🔋 Bateria Final", f"{nivel_bateria_ot[-1]:.2f} kWh", f"{(nivel_bateria_ot[-1]/microrrede.bateria.capacidade*100 if microrrede.bateria else 0):.1f}%")
                with col2:
                    st.metric("⛽ Diesel Final", f"{nivel_diesel_ot[-1]:.2f} L")
                with col3:
                    st.metric("💨 Biogas Final", f"{nivel_biogas_ot[-1]:.2f} m³" if nivel_biogas_ot[-1] > 0 else "Sem biogas")
            
            # TAB 3: CUSTOS
            with tab3:
                st.markdown("#### Análise de Custos (COM DESLIZAMENTO)")
                
                # Custo instantâneo
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Custo Instantâneo**")
                    custo_inst_df_ot = pd.DataFrame({"Custo (R$)": custo_total_instantaneo_ot})
                    fig_inst = Grafico_linha(custo_inst_df_ot, xlabel="Tempo (min)", ylabel="Custo (R$)", title="")
                    st.plotly_chart(fig_inst, use_container_width=True)
                
                with col2:
                    st.markdown("**Custo Acumulado**")
                    custo_acumulado_ot = np.cumsum(custo_total_instantaneo_ot)
                    custo_acu_df_ot = pd.DataFrame({"Custo Acumulado (R$)": custo_acumulado_ot})
                    fig_acu = Grafico_linha(custo_acu_df_ot, xlabel="Tempo (min)", ylabel="Custo Acumulado (R$)", title="")
                    st.plotly_chart(fig_acu, use_container_width=True)
                
                st.divider()
                st.markdown("**Custo por Fonte:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    custo_solar_ot = total_uso_solar_ot * (microrrede.solar.custo_kwh if microrrede.solar else 0) / 60
                    st.metric("☀️ Solar", f"R$ {custo_solar_ot:,.2f}")
                    custo_diesel_ot = total_uso_diesel_ot * (microrrede.diesel.custo_por_kWh if microrrede.diesel else 0) / 60
                    st.metric("🔥 Diesel", f"R$ {custo_diesel_ot:,.2f}")
                with col2:
                    custo_bateria_ot = total_uso_bateria_ot * (microrrede.bateria.custo_kwh if microrrede.bateria else 0) / 60
                    st.metric("🔋 Bateria", f"R$ {custo_bateria_ot:,.2f}")
                    custo_biogas_ot = total_uso_biogas_ot * (microrrede.biogas.custo_por_kWh if microrrede.biogas else 0) / 60
                    st.metric("💨 Biogas", f"R$ {custo_biogas_ot:,.2f}")
                with col3:
                    custo_rede_ot = total_uso_concessionaria_ot * (microrrede.concessionaria.tarifa if microrrede.concessionaria else 0) / 60
                    st.metric("🏢 Concessionária", f"R$ {custo_rede_ot:,.2f}")
            
            # TAB 4: RESUMO DE FONTES
            with tab4:
                st.markdown("#### Uso Total por Fonte")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.write("**Custo por kWh (ordenado):**")
                    st.dataframe(custo_kwh_ordenado_ot, use_container_width=True)
                
                with col2:
                    st.write("**Diagrama de Fluxo:**")
                    sankey_chart(uso_diesel=total_uso_diesel_ot, uso_bateria=total_uso_bateria_ot, uso_concessionaria=total_uso_concessionaria_ot, uso_biogas=total_uso_biogas_ot, uso_solar=total_uso_solar_ot, sobra=total_sobra_ot, carga=total_carga_ot)
                
                st.divider()
                st.write("**Resumo Energético:**")
                total_df_ot = pd.DataFrame({
                    "Fonte": ["☀️ Solar", "🔋 Bateria", "💨 Biogas", "🔥 Diesel", "🏢 Concessionária", "📤 Venda para Rede", "📤 Excedente/Sobra"],
                    "Energia (kWh)": [
                        f"{total_uso_solar_ot:,.2f}",
                        f"{total_uso_bateria_ot:,.2f}",
                        f"{total_uso_biogas_ot:,.2f}",
                        f"{total_uso_diesel_ot:,.2f}",
                        f"{total_uso_concessionaria_ot:,.2f}",
                        f"{total_venda_ot:,.2f}",
                        f"{total_sobra_ot:,.2f}"
                    ]
                })
                st.dataframe(total_df_ot, use_container_width=True, hide_index=True)
            
            # TAB 5: DETALHES
            with tab5:
                st.markdown("#### Dados Horários Detalhados (COM DESLIZAMENTO)")
                
                # Criar dataframe completo
                df_completo_ot = pd.DataFrame({
                    "Tempo (min)": range(len(curva_carga_ot)),
                    "Demanda (kW)": curva_carga_ot,
                    "Solar (kW)": uso_solar_ot,
                    "Diesel (kW)": uso_diesel_ot,
                    "Biogas (kW)": uso_biogas_ot,
                    "Bateria Descarga (kW)": uso_bateria_ot,
                    "Bateria Carga (kW)": carga_bateria_ot,
                    "Concessionária (kW)": uso_concessionaria_ot,
                    "Venda (kW)": venda_ot,
                    "Receita Venda (R$)": receita_venda_ot,
                    "Nível Bateria (kWh)": nivel_bateria_ot,
                    "Nível Diesel (L)": nivel_diesel_ot,
                    "Nível Biogas (m³)": nivel_biogas_ot,
                    "Custo Instantâneo (R$)": custo_total_instantaneo_ot
                })
                
                st.dataframe(df_completo_ot.style.format("{:.4f}"), use_container_width=True)
                
                st.download_button(
                    label="📥 Baixar dados em CSV",
                    data=df_completo_ot.to_csv(index=False),
                    file_name=f"analise3_{microrrede}.csv",
                    mime="text/csv"
                )
            
            # TAB 6: COMPARAÇÃO ANTES/DEPOIS
            with tab6:
                st.markdown("#### Impacto do Deslizamento de Cargas")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("💰 Sem Deslizamento", f"R$ {custo_total_or:,.2f}")
                    st.metric("", "")  # Espaçador
                with col2:
                    st.metric("💰 Com Deslizamento", f"R$ {custo_total_ot:,.2f}")
                    st.metric("", "")  # Espaçador
                with col3:
                    st.metric("📊 Economia Total", f"-R$ {economia:,.2f}")
                    st.metric("", "")  # Espaçador
                with col4:
                    st.metric("📈 Percentual", f"{economia_pct:.2f}%")
                    st.metric("", "")  # Espaçador
                
                st.divider()
                
                # Comparação de curva de carga
                st.markdown("#### Mudança na Curva de Carga")
                comparacao_cargas = pd.DataFrame({
                    "Original (kW)": curva_carga_or,
                    "Otimizada (kW)": curva_carga_ot,
                })
                fig_comp_carga = Grafico_linha(comparacao_cargas, xlabel="Tempo (min)", ylabel="Demanda (kW)", title="Comparação de Curvas de Carga")
                st.plotly_chart(fig_comp_carga, use_container_width=True)
                
                st.divider()
                
                # Comparação de custos
                st.markdown("#### Comparação de Custos Acumulados")
                custo_acu_or = np.cumsum(custo_total_instantaneo_or)
                custo_acu_ot = np.cumsum(custo_total_instantaneo_ot)
                comparacao_custos = pd.DataFrame({
                    "Sem Deslizamento (R$)": custo_acu_or,
                    "Com Deslizamento (R$)": custo_acu_ot,
                })
                fig_comp_custo = Grafico_linha(comparacao_custos, xlabel="Tempo (min)", ylabel="Custo Acumulado (R$)", title="")
                st.plotly_chart(fig_comp_custo, use_container_width=True)
                
                st.divider()
                
                # Tabela comparativa de fontes
                st.markdown("#### Resumo Comparativo por Fonte")
                tabela_comp = pd.DataFrame({
                    "Fonte": ["☀️ Solar", "🔋 Bateria", "💨 Biogas", "🔥 Diesel", "🏢 Concessionária"],
                    "Original (kWh)": [
                        f"{total_uso_solar_or:,.2f}",
                        f"{total_uso_bateria_or:,.2f}",
                        f"{total_uso_biogas_or:,.2f}",
                        f"{total_uso_diesel_or:,.2f}",
                        f"{total_uso_concessionaria_or:,.2f}"
                    ],
                    "Otimizado (kWh)": [
                        f"{total_uso_solar_ot:,.2f}",
                        f"{total_uso_bateria_ot:,.2f}",
                        f"{total_uso_biogas_ot:,.2f}",
                        f"{total_uso_diesel_ot:,.2f}",
                        f"{total_uso_concessionaria_ot:,.2f}"
                    ]
                })
                st.dataframe(tabela_comp, use_container_width=True, hide_index=True)
st.text("Comparação entre Análise 3 (Heurística com Deslizamento) e Análise 5 (MILP)")
if st.button("Comparação de Custos"):
    for idx, microrrede in enumerate(microrredes):
        with st.container(border=True):
            st.subheader(f"{microrrede} - Comparação de Custos", divider=True, width='stretch', text_alignment='center')
            
            # Executar Análise 3 (com deslizamento)
            with st.spinner("Executando Análise 3 (Heurística com Deslizamento)..."):
                resultado_a3 = Analise3.analise_3(microrrede)
                # Extrai versão otimizada (com deslizamento)
                (custo_kwh_ordenado_a3, total_uso_diesel_a3, total_uso_bateria_a3, total_uso_concessionaria_a3, 
                 total_uso_biogas_a3, total_uso_solar_a3, total_sobra_a3, total_carga_a3, uso_solar_a3, 
                 uso_bateria_a3, uso_biogas_a3, uso_diesel_a3, uso_concessionaria_a3, curva_carga_a3, 
                 nivel_bateria_a3, nivel_biogas_a3, nivel_diesel_a3, custo_total_instantaneo_a3, carga_bateria_a3,
                 venda_a3, receita_venda_a3, total_venda_a3, total_receita_venda_a3) = resultado_a3['otimizado']
            
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
                #if biogas is not None:
                #    custo_i += df_resultado_a5['Biogas'].iloc[i] * biogas.custo_por_kWh / 60
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
            st.plotly_chart(fig, use_container_width=True, key=f"comp_a3_a5_custo_acu_{idx}")
            
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
            st.plotly_chart(fig2, use_container_width=True, key=f"comp_a3_a5_custo_inst_{idx}")
            
            # ===== TABELA COMPARATIVA =====
            st.subheader("📊 Resumo Comparativo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Análise 3 (Heurística)**")
                df_resumo_a3 = pd.DataFrame({
                    'Fonte': ['☀️ Solar', '🔋 Bateria', '💨 Biogas', '🔥 Diesel', '🏢 Concessionária', '📤 Venda para Rede'],
                    'Energia/Receita': [
                        f"{total_uso_solar_a3:.2f} kWh",
                        f"{total_uso_bateria_a3:.2f} kWh",
                        f"{total_uso_biogas_a3:.2f} kWh",
                        f"{total_uso_diesel_a3:.2f} kWh",
                        f"{total_uso_concessionaria_a3:.2f} kWh",
                        f"{total_venda_a3:.2f} kWh"
                    ],
                    'Custo/Receita': [
                        f"R$ {total_uso_solar_a3 * (microrrede.solar.custo_kwh if microrrede.solar else 0):.2f}",
                        f"R$ {total_uso_bateria_a3 * (microrrede.bateria.custo_kwh if microrrede.bateria else 0):.2f}",
                        f"R$ {total_uso_biogas_a3 * (microrrede.biogas.custo_por_kWh if microrrede.biogas else 0):.2f}",
                        f"R$ {total_uso_diesel_a3 * (microrrede.diesel.custo_por_kWh if microrrede.diesel else 0):.2f}",
                        f"R$ {total_uso_concessionaria_a3 * (microrrede.concessionaria.tarifa if microrrede.concessionaria else 0):.2f}",
                        f"-R$ {total_receita_venda_a3:.2f}"
                    ]
                })
                st.dataframe(df_resumo_a3, hide_index=True)
            
            with col2:
                st.write("**Análise 5 (MILP)**")
                total_venda_a5 = df_resultado_a5['Venda'].sum()
                total_receita_venda_a5 = total_venda_a5 * (microrrede.concessionaria.tarifa * 0.8 if microrrede.concessionaria else 0)
                df_resumo_a5 = pd.DataFrame({
                    #'Fonte': ['☀️ Solar', '🔋 Bateria', '💨 Biogas', '🔥 Diesel', '🏢 Concessionária', '📤 Venda para Rede'],
                    'Fonte': ['☀️ Solar', '🔋 Bateria', '🔥 Diesel', '🏢 Concessionária', '📤 Venda para Rede'],
                    'Energia/Receita': [
                        f"{df_resultado_a5['Solar'].sum():.2f} kWh",
                        f"{df_resultado_a5['Bateria'].sum():.2f} kWh",
                        #f"{df_resultado_a5['Biogas'].sum():.2f} kWh",
                        f"{df_resultado_a5['Diesel'].sum():.2f} kWh",
                        f"{df_resultado_a5['Concessionaria'].sum():.2f} kWh",
                        f"{total_venda_a5:.2f} kWh"
                    ],
                    'Custo/Receita': [
                        f"R$ {df_resultado_a5['Solar'].sum() * (microrrede.solar.custo_kwh if microrrede.solar else 0):.2f}",
                        f"R$ {df_resultado_a5['Bateria'].sum() * (microrrede.bateria.custo_kwh if microrrede.bateria else 0):.2f}",
                        #f"R$ {df_resultado_a5['Biogas'].sum() * (microrrede.biogas.custo_por_kWh if microrrede.biogas else 0):.2f}",
                        f"R$ {df_resultado_a5['Diesel'].sum() * (microrrede.diesel.custo_por_kWh if microrrede.diesel else 0):.2f}",
                        f"R$ {df_resultado_a5['Concessionaria'].sum() * (microrrede.concessionaria.tarifa if microrrede.concessionaria else 0):.2f}",
                        f"-R$ {total_receita_venda_a5:.2f}"
                    ]
                })
                st.dataframe(df_resumo_a5, hide_index=True)
            
            # ===== RESUMO DE VENDA =====
            st.divider()
            st.subheader("📤 Comparação de Venda para Rede")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("A3: Energia Vendida", f"{total_venda_a3:.2f} kWh")
            with col2:
                st.metric("A3: Receita Venda", f"R$ {total_receita_venda_a3:.2f}")
            with col3:
                st.metric("A5: Energia Vendida", f"{total_venda_a5:.2f} kWh")
            with col4:
                st.metric("A5: Receita Venda", f"R$ {total_receita_venda_a5:.2f}")

st.text("Comparação: Método 5 (com venda) vs Método 5.1 (sem venda de energia para a rede)")
if st.button("Comparação Método 5 vs Método 5.1"):
    for idx, microrrede in enumerate(microrredes):
        with st.container(border=True):
            st.subheader(f"{microrrede} - Método 5 vs Método 5.1", divider=True, width='stretch', text_alignment='center')
            
            # Executar Método 5 (com venda)
            with st.spinner("Executando Método 5 (COM venda para a rede)..."):
                df_resultado_m5, custos_m5, solucao_m5 = analise_milp(microrrede)
            
            if df_resultado_m5 is None:
                st.error("❌ Não foi possível resolver Método 5")
                continue
            
            custo_total_m5 = custos_m5.get('Total', 0)
            
            # Executar Método 5.1 (sem venda)
            with st.spinner("Executando Método 5.1 (SEM venda para a rede)..."):
                df_resultado_m51, custos_m51, solucao_m51 = analise_milp_sem_venda(microrrede)
            
            if df_resultado_m51 is None:
                st.error("❌ Não foi possível resolver Método 5.1")
                continue
            
            custo_total_m51 = custos_m51.get('Total', 0)
            
            # ===== MÉTRICAS COMPARATIVAS =====
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💰 Método 5 (COM venda)", f"R$ {custo_total_m5:,.2f}")
            with col2:
                st.metric("💰 Método 5.1 (SEM venda)", f"R$ {custo_total_m51:,.2f}")
            with col3:
                economia = custo_total_m51 - custo_total_m5
                percentual = (economia / custo_total_m51 * 100) if custo_total_m51 > 0 else 0
                if economia >= 0:
                    st.metric("💹 Benefício Venda", f"R$ {economia:,.2f}", f"{percentual:.2f}%", delta_color="inverse")
                else:
                    st.metric("⚠️ Custo Venda", f"R$ {abs(economia):,.2f}", f"{abs(percentual):.2f}%")
            with col4:
                economia_pct = ((custo_total_m51 - custo_total_m5) / custo_total_m51 * 100)
                st.metric("📊 Redução %", f"{abs(economia_pct):.2f}%", f"{'Melhora' if economia > 0 else 'Piora'}")
            
            # ===== GRÁFICO DE CUSTO ACUMULADO =====
            st.subheader("📈 Custo Acumulado ao Longo do Dia")
            
            # Calcular custos instantâneos para ambos
            bateria = microrrede.bateria
            diesel = microrrede.diesel
            biogas = microrrede.biogas
            solar = microrrede.solar
            concessionaria = microrrede.concessionaria
            
            # Custo M5 (com venda)
            custo_inst_m5 = np.zeros(len(df_resultado_m5))
            for i in range(len(df_resultado_m5)):
                custo_i = 0
                if solar is not None:
                    custo_i += df_resultado_m5['Solar'].iloc[i] * solar.custo_kwh / 60
                if bateria is not None:
                    custo_i += df_resultado_m5['Bateria'].iloc[i] * bateria.custo_kwh / 60
                if diesel is not None:
                    custo_i += df_resultado_m5['Diesel'].iloc[i] * diesel.custo_por_kWh / 60
                if biogas is not None:
                    custo_i += df_resultado_m5['Biogas'].iloc[i] * biogas.custo_por_kWh / 60
                if concessionaria is not None:
                    custo_i += df_resultado_m5['Concessionaria'].iloc[i] * concessionaria.tarifa / 60
                    custo_i -= df_resultado_m5['Venda'].iloc[i] * concessionaria.tarifa * 0.8 / 60
                custo_inst_m5[i] = custo_i
            
            # Custo M5.1 (sem venda)
            custo_inst_m51 = np.zeros(len(df_resultado_m51))
            for i in range(len(df_resultado_m51)):
                custo_i = 0
                if solar is not None:
                    custo_i += df_resultado_m51['Solar'].iloc[i] * solar.custo_kwh / 60
                if bateria is not None:
                    custo_i += df_resultado_m51['Bateria'].iloc[i] * bateria.custo_kwh / 60
                if diesel is not None:
                    custo_i += df_resultado_m51['Diesel'].iloc[i] * diesel.custo_por_kWh / 60
                if biogas is not None:
                    custo_i += df_resultado_m51['Biogas'].iloc[i] * biogas.custo_por_kWh / 60
                if concessionaria is not None:
                    custo_i += df_resultado_m51['Concessionaria'].iloc[i] * concessionaria.tarifa / 60
                custo_inst_m51[i] = custo_i
            
            custo_acu_m5 = np.cumsum(custo_inst_m5)
            custo_acu_m51 = np.cumsum(custo_inst_m51)
            
            # Gráfico de custo acumulado
            df_acu = pd.DataFrame({
                "Método 5 (COM venda)": custo_acu_m5,
                "Método 5.1 (SEM venda)": custo_acu_m51
            })
            
            fig_acu = Grafico_linha(df_acu, 
                                   xlabel="Tempo (min)", 
                                   ylabel="Custo Acumulado (R$)", 
                                   title="Comparação de Custos Acumulados ao Longo do Dia")
            st.plotly_chart(fig_acu, use_container_width=True, key=f"comp_m5_m51_custo_acu_{idx}")
            
            # ===== GRÁFICO DE CUSTO INSTANTÂNEO =====
            st.subheader("⏱️ Custo Instantâneo de Operação")
            
            df_inst = pd.DataFrame({
                "Método 5 (COM venda)": custo_inst_m5,
                "Método 5.1 (SEM venda)": custo_inst_m51
            })
            
            fig_inst = Grafico_linha(df_inst,
                                    xlabel="Tempo (min)",
                                    ylabel="Custo (R$)",
                                    title="Comparação de Custos Instantâneos")
            st.plotly_chart(fig_inst, use_container_width=True, key=f"comp_m5_m51_custo_inst_{idx}")
            
            # ===== TABELA COMPARATIVA DE CUSTOS =====
            st.subheader("📊 Resumo Detalhado de Custos")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Método 5 (COM venda)**")
                total_solar_m5 = df_resultado_m5['Solar'].sum()
                total_bateria_m5 = df_resultado_m5['Bateria'].sum()
                total_diesel_m5 = df_resultado_m5['Diesel'].sum()
                total_biogas_m5 = df_resultado_m5['Biogas'].sum()
                total_conc_m5 = df_resultado_m5['Concessionaria'].sum()
                total_venda_m5 = df_resultado_m5['Venda'].sum()
                
                df_custos_m5 = pd.DataFrame({
                    'Fonte': ['☀️ Solar', '🔋 Bateria', '💨 Biogas', '🔥 Diesel', '🏢 Concessionária', '📤 Venda (Receita)'],
                    'Energia (kWh)': [
                        f"{total_solar_m5:.2f}",
                        f"{total_bateria_m5:.2f}",
                        f"{total_biogas_m5:.2f}",
                        f"{total_diesel_m5:.2f}",
                        f"{total_conc_m5:.2f}",
                        f"{total_venda_m5:.2f}"
                    ],
                    'Custo (R$)': [
                        f"{total_solar_m5 * (solar.custo_kwh if solar else 0):.2f}",
                        f"{total_bateria_m5 * (bateria.custo_kwh if bateria else 0):.2f}",
                        f"{total_biogas_m5 * (biogas.custo_por_kWh if biogas else 0):.2f}",
                        f"{total_diesel_m5 * (diesel.custo_por_kWh if diesel else 0):.2f}",
                        f"{total_conc_m5 * (concessionaria.tarifa if concessionaria else 0):.2f}",
                        f"-{total_venda_m5 * (concessionaria.tarifa * 0.8 if concessionaria else 0):.2f}"
                    ]
                })
                st.dataframe(df_custos_m5, hide_index=True, use_container_width=True)
            
            with col2:
                st.write("**Método 5.1 (SEM venda)**")
                total_solar_m51 = df_resultado_m51['Solar'].sum()
                total_bateria_m51 = df_resultado_m51['Bateria'].sum()
                total_diesel_m51 = df_resultado_m51['Diesel'].sum()
                total_biogas_m51 = df_resultado_m51['Biogas'].sum()
                total_conc_m51 = df_resultado_m51['Concessionaria'].sum()
                
                df_custos_m51 = pd.DataFrame({
                    'Fonte': ['☀️ Solar', '🔋 Bateria', '💨 Biogas', '🔥 Diesel', '🏢 Concessionária'],
                    'Energia (kWh)': [
                        f"{total_solar_m51:.2f}",
                        f"{total_bateria_m51:.2f}",
                        f"{total_biogas_m51:.2f}",
                        f"{total_diesel_m51:.2f}",
                        f"{total_conc_m51:.2f}"
                    ],
                    'Custo (R$)': [
                        f"{total_solar_m51 * (solar.custo_kwh if solar else 0):.2f}",
                        f"{total_bateria_m51 * (bateria.custo_kwh if bateria else 0):.2f}",
                        f"{total_biogas_m51 * (biogas.custo_por_kWh if biogas else 0):.2f}",
                        f"{total_diesel_m51 * (diesel.custo_por_kWh if diesel else 0):.2f}",
                        f"{total_conc_m51 * (concessionaria.tarifa if concessionaria else 0):.2f}"
                    ]
                })
                st.dataframe(df_custos_m51, hide_index=True, use_container_width=True)
            
            # ===== ANÁLISE DE VENDA =====
            st.divider()
            st.subheader("📤 Impacto da Venda de Energia")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Energia Vendida", f"{total_venda_m5:.2f} kWh")
            with col2:
                receita_venda = total_venda_m5 * (concessionaria.tarifa * 0.8 if concessionaria else 0)
                st.metric("Receita Venda", f"R$ {receita_venda:.2f}")
            with col3:
                st.metric("Impacto no Custo", f"-R$ {receita_venda:.2f}", "Redução")
            with col4:
                impacto_pct = (receita_venda / custo_total_m51 * 100) if custo_total_m51 > 0 else 0
                st.metric("Redução %", f"{impacto_pct:.2f}%")
            
            # ===== DESPACHO ENERGY COMPARATIVO =====
            st.divider()
            st.subheader("⚡ Despacho de Energia Comparativo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Método 5 (COM venda)**")
                despacho_m5 = pd.DataFrame({
                    "Solar": df_resultado_m5['Solar'],
                    "Bateria": df_resultado_m5['Bateria'],
                    "Diesel": df_resultado_m5['Diesel'],
                    "Biogas": df_resultado_m5['Biogas'],
                    "Concessionária": df_resultado_m5['Concessionaria'],
                    "Venda": df_resultado_m5['Venda']
                })
                fig_desp_m5 = Grafico_linha(despacho_m5, xlabel="Tempo (min)", ylabel="Potência (kW)", title="")
                st.plotly_chart(fig_desp_m5, use_container_width=True, key=f"comp_m5_m51_desp_m5_{idx}")
            
            with col2:
                st.write("**Método 5.1 (SEM venda)**")
                despacho_m51 = pd.DataFrame({
                    "Solar": df_resultado_m51['Solar'],
                    "Bateria": df_resultado_m51['Bateria'],
                    "Diesel": df_resultado_m51['Diesel'],
                    "Biogas": df_resultado_m51['Biogas'],
                    "Concessionária": df_resultado_m51['Concessionaria']
                })
                fig_desp_m51 = Grafico_linha(despacho_m51, xlabel="Tempo (min)", ylabel="Potência (kW)", title="")
                st.plotly_chart(fig_desp_m51, use_container_width=True, key=f"comp_m5_m51_desp_m51_{idx}")

st.text("Comparação: Método 3 (Heurística com deslizamento) vs Método 5.1 (MILP sem venda)")
if st.button("Comparação Método 3 vs Método 5.1"):
    for idx, microrrede in enumerate(microrredes):
        with st.container(border=True):
            st.subheader(f"{microrrede} - Método 3 vs Método 5.1", divider=True, width='stretch', text_alignment='center')
            
            # Executar Análise 3 (com deslizamento)
            with st.spinner("Executando Método 3 (Heurística com deslizamento)..."):
                resultado_m3 = Analise3.analise_3(microrrede)
                (custo_kwh_ordenado_m3, total_uso_diesel_m3, total_uso_bateria_m3, total_uso_concessionaria_m3, 
                 total_uso_biogas_m3, total_uso_solar_m3, total_sobra_m3, total_carga_m3, uso_solar_m3, 
                 uso_bateria_m3, uso_biogas_m3, uso_diesel_m3, uso_concessionaria_m3, curva_carga_m3, 
                 nivel_bateria_m3, nivel_biogas_m3, nivel_diesel_m3, custo_total_instantaneo_m3, carga_bateria_m3,
                 venda_m3, receita_venda_m3, total_venda_m3, total_receita_venda_m3) = resultado_m3['otimizado']
            
            custo_total_m3 = custo_total_instantaneo_m3.sum()
            
            # Executar Método 5.1 (sem venda)
            with st.spinner("Executando Método 5.1 (MILP sem venda)..."):
                df_resultado_51, custos_51, solucao_51 = analise_milp_sem_venda(microrrede)
            
            if df_resultado_51 is None:
                st.error("❌ Não foi possível resolver Método 5.1")
                continue
            
            custo_total_51 = custos_51.get('Total', 0)
            
            # ===== MÉTRICAS COMPARATIVAS =====
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💰 Método 3", f"R$ {custo_total_m3:,.2f}")
            with col2:
                st.metric("🎯 Método 5.1", f"R$ {custo_total_51:,.2f}")
            with col3:
                economia = custo_total_m3 - custo_total_51
                percentual = (economia / custo_total_m3 * 100) if custo_total_m3 > 0 else 0
                if economia >= 0:
                    st.metric("✅ Economia MILP", f"R$ {economia:,.2f}", f"{percentual:.2f}%", delta_color="inverse")
                else:
                    st.metric("⚠️ Custo Adicional", f"R$ {abs(economia):,.2f}", f"{abs(percentual):.2f}%")
            with col4:
                economia_pct = ((custo_total_m3 - custo_total_51) / custo_total_m3 * 100) if custo_total_m3 > 0 else 0
                st.metric("📊 Melhoria %", f"{economia_pct:.2f}%")
            
            # ===== GRÁFICO DE CUSTO ACUMULADO =====
            st.subheader("📈 Custo Acumulado ao Longo do Dia")
            
            # Calcular custos instantâneos para ambos
            bateria = microrrede.bateria
            diesel = microrrede.diesel
            biogas = microrrede.biogas
            solar = microrrede.solar
            concessionaria = microrrede.concessionaria
            
            # Custo M3 já está disponível
            custo_acu_m3 = np.cumsum(custo_total_instantaneo_m3)
            
            # Custo M5.1 (sem venda)
            custo_inst_51 = np.zeros(len(df_resultado_51))
            for i in range(len(df_resultado_51)):
                custo_i = 0
                if solar is not None:
                    custo_i += df_resultado_51['Solar'].iloc[i] * solar.custo_kwh / 60
                if bateria is not None:
                    custo_i += df_resultado_51['Bateria'].iloc[i] * bateria.custo_kwh / 60
                if diesel is not None:
                    custo_i += df_resultado_51['Diesel'].iloc[i] * diesel.custo_por_kWh / 60
                if biogas is not None:
                    custo_i += df_resultado_51['Biogas'].iloc[i] * biogas.custo_por_kWh / 60
                if concessionaria is not None:
                    custo_i += df_resultado_51['Concessionaria'].iloc[i] * concessionaria.tarifa / 60
                custo_inst_51[i] = custo_i
            
            custo_acu_51 = np.cumsum(custo_inst_51)
            
            # Gráfico de custo acumulado
            df_acu = pd.DataFrame({
                "Método 3 (Heurística)": custo_acu_m3,
                "Método 5.1 (MILP SEM venda)": custo_acu_51
            })
            
            fig_acu = Grafico_linha(df_acu, 
                                   xlabel="Tempo (min)", 
                                   ylabel="Custo Acumulado (R$)", 
                                   title="Comparação de Custos Acumulados ao Longo do Dia")
            st.plotly_chart(fig_acu, use_container_width=True, key=f"comp_m3_m51_custo_acu_{idx}")
            
            # ===== GRÁFICO DE CUSTO INSTANTÂNEO =====
            st.subheader("⏱️ Custo Instantâneo de Operação")
            
            df_inst = pd.DataFrame({
                "Método 3": custo_total_instantaneo_m3,
                "Método 5.1": custo_inst_51
            })
            
            fig_inst = Grafico_linha(df_inst,
                                    xlabel="Tempo (min)",
                                    ylabel="Custo (R$)",
                                    title="Comparação de Custos Instantâneos")
            st.plotly_chart(fig_inst, use_container_width=True, key=f"comp_m3_m51_custo_inst_{idx}")
            
            # ===== TABELA COMPARATIVA DE CUSTOS =====
            st.subheader("📊 Resumo Detalhado de Custos")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Método 3 (Heurística com deslizamento)**")
                df_custos_m3 = pd.DataFrame({
                    'Fonte': ['☀️ Solar', '🔋 Bateria', '💨 Biogas', '🔥 Diesel', '🏢 Concessionária'],
                    'Energia (kWh)': [
                        f"{total_uso_solar_m3:.2f}",
                        f"{total_uso_bateria_m3:.2f}",
                        f"{total_uso_biogas_m3:.2f}",
                        f"{total_uso_diesel_m3:.2f}",
                        f"{total_uso_concessionaria_m3:.2f}"
                    ],
                    'Custo (R$)': [
                        f"{total_uso_solar_m3 * (solar.custo_kwh if solar else 0):.2f}",
                        f"{total_uso_bateria_m3 * (bateria.custo_kwh if bateria else 0):.2f}",
                        f"{total_uso_biogas_m3 * (biogas.custo_por_kWh if biogas else 0):.2f}",
                        f"{total_uso_diesel_m3 * (diesel.custo_por_kWh if diesel else 0):.2f}",
                        f"{total_uso_concessionaria_m3 * (concessionaria.tarifa if concessionaria else 0):.2f}"
                    ]
                })
                st.dataframe(df_custos_m3, hide_index=True, use_container_width=True)
            
            with col2:
                st.write("**Método 5.1 (MILP SEM venda)**")
                total_solar_51 = df_resultado_51['Solar'].sum()
                total_bateria_51 = df_resultado_51['Bateria'].sum()
                total_diesel_51 = df_resultado_51['Diesel'].sum()
                total_biogas_51 = df_resultado_51['Biogas'].sum()
                total_conc_51 = df_resultado_51['Concessionaria'].sum()
                
                df_custos_51 = pd.DataFrame({
                    'Fonte': ['☀️ Solar', '🔋 Bateria', '💨 Biogas', '🔥 Diesel', '🏢 Concessionária'],
                    'Energia (kWh)': [
                        f"{total_solar_51:.2f}",
                        f"{total_bateria_51:.2f}",
                        f"{total_biogas_51:.2f}",
                        f"{total_diesel_51:.2f}",
                        f"{total_conc_51:.2f}"
                    ],
                    'Custo (R$)': [
                        f"{total_solar_51 * (solar.custo_kwh if solar else 0):.2f}",
                        f"{total_bateria_51 * (bateria.custo_kwh if bateria else 0):.2f}",
                        f"{total_biogas_51 * (biogas.custo_por_kWh if biogas else 0):.2f}",
                        f"{total_diesel_51 * (diesel.custo_por_kWh if diesel else 0):.2f}",
                        f"{total_conc_51 * (concessionaria.tarifa if concessionaria else 0):.2f}"
                    ]
                })
                st.dataframe(df_custos_51, hide_index=True, use_container_width=True)
            
            # ===== ANÁLISE DE EFICIÊNCIA =====
            st.divider()
            st.subheader("⚡ Análise de Eficiência")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                cobertura_local_m3 = ((total_carga_m3 - total_uso_concessionaria_m3) / total_carga_m3 * 100) if total_carga_m3 > 0 else 0
                cobertura_local_51 = ((df_resultado_51['Carga'].sum() - total_conc_51) / df_resultado_51['Carga'].sum() * 100) if df_resultado_51['Carga'].sum() > 0 else 0
                st.metric("🏠 Cobertura Local (M3)", f"{cobertura_local_m3:.1f}%")
                st.metric("🏠 Cobertura Local (M5.1)", f"{cobertura_local_51:.1f}%")
            
            with col2:
                diesel_m3_total = total_uso_diesel_m3
                diesel_51_total = total_diesel_51
                st.metric("🔥 Diesel M3", f"{diesel_m3_total:.2f} kWh")
                st.metric("🔥 Diesel M5.1", f"{diesel_51_total:.2f} kWh")
            
            with col3:
                bateria_m3_total = total_uso_bateria_m3
                bateria_51_total = total_bateria_51
                st.metric("🔋 Bateria M3", f"{bateria_m3_total:.2f} kWh")
                st.metric("🔋 Bateria M5.1", f"{bateria_51_total:.2f} kWh")
            
            with col4:
                conc_m3_total = total_uso_concessionaria_m3
                conc_51_total = total_conc_51
                st.metric("🏢 Rede M3", f"{conc_m3_total:.2f} kWh")
                st.metric("🏢 Rede M5.1", f"{conc_51_total:.2f} kWh")
            
            with col5:
                economia_diesel = diesel_m3_total - diesel_51_total
                economia_bateria = bateria_m3_total - bateria_51_total
                st.metric("💹 ↓ Diesel", f"{economia_diesel:.2f} kWh" if economia_diesel >= 0 else f"{abs(economia_diesel):.2f} kWh ↑")
                st.metric("💹 ↓ Bateria", f"{economia_bateria:.2f} kWh" if economia_bateria >= 0 else f"{abs(economia_bateria):.2f} kWh ↑")
            
            # ===== DESPACHO ENERGY COMPARATIVO =====
            st.divider()
            st.subheader("⚡ Despacho de Energia Comparativo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Método 3 (Heurística)**")
                despacho_m3 = pd.DataFrame({
                    "Solar": uso_solar_m3,
                    "Bateria": uso_bateria_m3,
                    "Diesel": uso_diesel_m3,
                    "Biogas": uso_biogas_m3,
                    "Concessionária": uso_concessionaria_m3
                })
                fig_desp_m3 = Grafico_linha(despacho_m3, xlabel="Tempo (min)", ylabel="Potência (kW)", title="")
                st.plotly_chart(fig_desp_m3, use_container_width=True, key=f"comp_m3_m51_desp_m3_{idx}")
            
            with col2:
                st.write("**Método 5.1 (MILP SEM venda)**")
                despacho_51 = pd.DataFrame({
                    "Solar": df_resultado_51['Solar'],
                    "Bateria": df_resultado_51['Bateria'],
                    "Diesel": df_resultado_51['Diesel'],
                    "Biogas": df_resultado_51['Biogas'],
                    "Concessionária": df_resultado_51['Concessionaria']
                })
                fig_desp_51 = Grafico_linha(despacho_51, xlabel="Tempo (min)", ylabel="Potência (kW)", title="")
                st.plotly_chart(fig_desp_51, use_container_width=True, key=f"comp_m3_m51_desp_51_{idx}")
            
            # ===== NÍVEL DE ARMAZENAMENTO COMPARATIVO =====
            st.divider()
            st.subheader("📦 Evolução dos Níveis de Armazenamento")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Método 3**")
                nivel_m3 = pd.DataFrame({
                    "Bateria (kWh)": nivel_bateria_m3,
                    "Diesel (L)": nivel_diesel_m3,
                    "Biogas (m³)": nivel_biogas_m3
                })
                fig_nivel_m3 = Grafico_linha(nivel_m3, xlabel="Tempo (min)", ylabel="Capacidade", title="")
                st.plotly_chart(fig_nivel_m3, use_container_width=True, key=f"comp_m3_m51_nivel_m3_{idx}")
            
            with col2:
                st.write("**Método 5.1**")
                nivel_51 = pd.DataFrame({
                    "Bateria (kWh)": df_resultado_51['Carga_Bateria'] if 'Carga_Bateria' in df_resultado_51.columns else np.zeros(len(df_resultado_51)),
                })
                if 'Carga_Bateria' in df_resultado_51.columns:
                    fig_nivel_51 = Grafico_linha(nivel_51, xlabel="Tempo (min)", ylabel="Capacidade", title="")
                    st.plotly_chart(fig_nivel_51, use_container_width=True, key=f"comp_m3_m51_nivel_51_{idx}")
                else:
                    st.info("Informações de nível de armazenamento não disponíveis")

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