import streamlit as st
import pandas as pd

from analises.PrioridadeMicro import Analise1, Analise2, Analise3, Analise4, analise_5_milp_multi, analise_5_milp, analise_6_pso, analise_6_pso_multi
from models.Microrrede import Microrrede
from models.CRUD import Ler
from otmizadores.exemplo_milp import exemplo_2_multiplas_microrredes
from otmizadores.milp_controle_microrrede import analise_milp, analise_milp_sem_venda, analise_milp_com_deslizamento
import numpy as np
from Tools.Graficos.BarChart import Grafico_barra 
from Tools.Graficos.Sankey_Chart import sankey_chart
from Tools.Graficos.LineChartMath import Grafico_linha


from analises.config import ConfigAnalise

# Configuração da página
st.set_page_config(page_title="Simulador de Energia", layout="wide")
st.title("Simulador de Energia")

st.sidebar.header("Controle de Fontes")
config = ConfigAnalise(
    solar_ligado=st.sidebar.checkbox("☀️ Solar", value=True),
    bateria_ligada=st.sidebar.checkbox("🔋 Bateria", value=True),
    diesel_ligado=st.sidebar.checkbox("🔥 Diesel", value=True),
    biogas_ligado=st.sidebar.checkbox("💨 Biogás", value=True),
    concessionaria_ligada=st.sidebar.checkbox("🏢 Concessionária", value=True)
)

microrredes = Ler(Microrrede)
st.text("Uso exclusivo de apenas uma fonte de energia durante o dia")
if st.button("Analise 1"): 
    for idx, microrrede in enumerate(microrredes):
        with st.container(border=True):
            st.header(f"{microrrede}", divider=True, width='stretch', text_alignment="center")
        
            total_carga, total_concessionaria, alerta_bateria, total_bateria, alerta_solar, total_solar, alerta_diesel, total_diesel, alerta_biogas, total_biogas, resultado_microrrede = Analise1.executar(microrrede, config)
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
            custo_kwh_ordenado, total_uso_diesel, total_uso_bateria, total_uso_concessionaria, total_uso_biogas, total_uso_solar, total_sobra, total_carga, total, uso_energia, niveis_tanque, custo_total, custo_total_instantaneo = Analise2.executar(microrrede, config)
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

# ===== FUNÇÕES AUXILIARES PARA ANÁLISE 3 =====

def _extract_analise3_results(resultado: dict) -> dict:
    """
    Extrai resultados da Análise 3 de uma tupla para um dicionário estruturado.
    
    Args:
        resultado: Dicionário contendo 'original' e 'otimizado' retornado por Analise3.analise_3()
        
    Returns:
        Dicionário com chaves estruturadas para 'original' e 'otimizado'
    """
    def _unpack_tuple(tup: tuple) -> dict:
        """Converte tupla de resultados em dicionário."""
        return {
            'custo_kwh_ordenado': tup[0],
            'total_uso_diesel': tup[1],
            'total_uso_bateria': tup[2],
            'total_uso_concessionaria': tup[3],
            'total_uso_biogas': tup[4],
            'total_uso_solar': tup[5],
            'total_sobra': tup[6],
            'total_carga': tup[7],
            'uso_solar': tup[8],
            'uso_bateria': tup[9],
            'uso_biogas': tup[10],
            'uso_diesel': tup[11],
            'uso_concessionaria': tup[12],
            'curva_carga': tup[13],
            'nivel_bateria': tup[14],
            'nivel_biogas': tup[15],
            'nivel_diesel': tup[16],
            'custo_total_instantaneo': tup[17],
            'recarga_bateria': tup[18],
        }
    
    return {
        'original': _unpack_tuple(resultado['original']),
        'otimizado': _unpack_tuple(resultado['otimizado'])
    }


def _calculate_energy_metrics(total_carga: float, total_uso_concessionaria: float, 
                             total_uso_solar: float, total_sobra: float, 
                             custo_total_or: float, custo_total_ot: float) -> dict:
    """
    Calcula métricas de energia (cobertura, aproveitamento, economia).
    
    Args:
        total_carga: Demanda total (kWh)
        total_uso_concessionaria: Uso de concessionária (kWh)
        total_uso_solar: Uso de solar (kWh)
        total_sobra: Energia não utilizada (kWh)
        custo_total_or: Custo original (R$)
        custo_total_ot: Custo otimizado (R$)
        
    Returns:
        Dicionário com métricas calculadas
    """
    return {
        'cobertura_local': ((total_carga - total_uso_concessionaria) / total_carga * 100) if total_carga > 0 else 0,
        'aproveitamento_solar': (total_uso_solar / (total_uso_solar + total_sobra) * 100) if (total_uso_solar + total_sobra) > 0 else 0,
        'economia': custo_total_or - custo_total_ot,
        'economia_pct': ((custo_total_or - custo_total_ot) / custo_total_or * 100) if custo_total_or > 0 else 0
    }


def _calculate_source_costs(dados: dict, microrrede: Microrrede) -> dict:
    """
    Calcula custos por fonte de energia.
    
    Args:
        dados: Dicionário com totais de uso por fonte
        microrrede: Objeto da microrrede com informações de custo
        
    Returns:
        Dicionário com custos calculados por fonte
    """
    return {
        'solar': dados['total_uso_solar'] * (microrrede.solar.custo_kwh if microrrede.solar else 0) / 60,
        'diesel': dados['total_uso_diesel'] * (microrrede.diesel.custo_por_kWh if microrrede.diesel else 0) / 60,
        'bateria': dados['total_uso_bateria'] * (microrrede.bateria.custo_kwh if microrrede.bateria else 0) / 60,
        'biogas': dados['total_uso_biogas'] * (microrrede.biogas.custo_por_kWh if microrrede.biogas else 0) / 60,
        'concessionaria': dados['total_uso_concessionaria'] * (microrrede.concessionaria.tarifa if microrrede.concessionaria else 0) / 60
    }


def _create_source_comparison_df(total_solar: float, total_bateria: float, total_diesel: float, 
                                 total_concessionaria: float, microrrede: Microrrede) -> pd.DataFrame:
    """
    Cria DataFrame com comparação de fontes.
    
    Args:
        total_solar, total_bateria, total_diesel, total_concessionaria: Totais de uso
        microrrede: Objeto da microrrede
        
    Returns:
        DataFrame estruturado com energia, custo unitário e custo total
    """
    return pd.DataFrame({
        "Fonte": ["☀️ Solar", "🔋 Bateria", "🔥 Diesel", "🏢 Concessionária"],
        "Energia (kWh)": [f"{total_solar:,.2f}", f"{total_bateria:,.2f}", 
                          f"{total_diesel:,.2f}", f"{total_concessionaria:,.2f}"],
        "Custo Unitário (R$/kWh)": [
            f"R$ {microrrede.solar.custo_kwh if microrrede.solar else 0:.4f}",
            f"R$ {microrrede.bateria.custo_kwh if microrrede.bateria else 0:.4f}",
            f"R$ {microrrede.diesel.custo_por_kWh if microrrede.diesel else 0:.4f}",
            f"R$ {microrrede.concessionaria.tarifa if microrrede.concessionaria else 0:.4f}"
        ],
        "Custo Total (R$)": [
            f"R$ {total_solar * (microrrede.solar.custo_kwh if microrrede.solar else 0):.2f}",
            f"R$ {total_bateria * (microrrede.bateria.custo_kwh if microrrede.bateria else 0):.2f}",
            f"R$ {total_diesel * (microrrede.diesel.custo_por_kWh if microrrede.diesel else 0):.2f}",
            f"R$ {total_concessionaria * (microrrede.concessionaria.tarifa if microrrede.concessionaria else 0):.2f}"
        ]
    })


st.text("Uso otimizado das fontes e controle de cargas microrrede")
if st.button("Analise 3"):
    for idx, microrrede in enumerate(microrredes):
        with st.container(border=True):
            st.subheader(f"{microrrede}", divider=True)
            
            # Executa a análise com deslizamento de cargas
            with st.spinner("Executando Análise 3 com otimização de cargas..."):
                resultado_analise3 = Analise3.analise_3(microrrede, config)
            
            # Extrai resultados usando função auxiliar
            dados = _extract_analise3_results(resultado_analise3)
            resultado_ot = dados['otimizado']
            resultado_or = dados['original']
            
            # Calcula métricas de custo
            custo_total_ot = resultado_ot['custo_total_instantaneo'].sum()
            custo_total_or = resultado_or['custo_total_instantaneo'].sum()
            
            # Calcula métricas de energia
            metricas = _calculate_energy_metrics(
                resultado_ot['total_carga'],
                resultado_ot['total_uso_concessionaria'],
                resultado_ot['total_uso_solar'],
                resultado_ot['total_sobra'],
                custo_total_or,
                custo_total_ot
            )
            
            # ===== MÉTRICAS RESUMIDAS =====
            st.markdown("### 📊 Resumo de Operação (COM DESLIZAMENTO DE CARGAS)")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("💰 Custo Total", f"R$ {custo_total_ot:,.2f}", 
                         f"-R$ {metricas['economia']:,.2f}" if metricas['economia'] > 0 else f"+R$ {abs(metricas['economia']):,.2f}")
            with col2:
                st.metric("🏠 Cobertura Local", f"{metricas['cobertura_local']:.1f}%")
            with col3:
                st.metric("☀️ Aproveit. Solar", f"{metricas['aproveitamento_solar']:.1f}%")
            with col4:
                st.metric("📦 Demanda Total", f"{resultado_ot['total_carga']:,.2f} kWh")
            with col5:
                st.metric("📊 Economia", f"{metricas['economia_pct']:.1f}%")
            
            # ===== ABAS ORGANIZADAS =====
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 Fluxo de Energia", "🔋 Armazenamento", "💵 Custos", "🎯 Resumo de Fontes", "📋 Detalhes", "🔄 Comparação"])
            
            # TAB 1: FLUXO DE ENERGIA
            with tab1:
                st.markdown("#### Despacho de Energia ao Longo do Dia (COM DESLIZAMENTO)")
                demanda_negativa_ot = -np.abs(np.array(resultado_ot['curva_carga']))
                uso_energia_ot = pd.DataFrame({
                    "Solar": resultado_ot['uso_solar'], 
                    "Bateria": resultado_ot['uso_bateria'],
                    "Diesel": resultado_ot['uso_diesel'],
                    "Concessionária": resultado_ot['uso_concessionaria'],
                    "Recarga Bateria": -resultado_ot['recarga_bateria'],
                    "Carga (Demanda)": demanda_negativa_ot
                })
                fig1 = Grafico_linha(uso_energia_ot, xlabel="Tempo (min)", ylabel="Potência (kW)", title="Positivo = Fornecimento | Negativo = Consumo/Carregamento")
                st.plotly_chart(fig1, width='stretch', key=f"analise3_fluxo_energia_{idx}")
                
                st.markdown("**Legenda:**")
                st.write("- 📈 **Acima do zero**: Fontes gerando/fornecendo energia")
                st.write("- 📉 **Abaixo do zero**: Demanda de carga e carregamento de bateria")
                st.write("- ☀️ **Solar**: Geração solar disponível")
                st.write("- 🔋 **Bateria**: Descarga para suprir demanda ou carga para armazenar")
                st.write("- 🔥 **Diesel**: Geração diesel quando necessário")
                st.write("- 🏢 **Concessionária**: Compra de energia da rede")
                st.info("💡 Observe como as cargas com prioridade 2 e 4 foram movidas para horários de menor custo operacional")
            
            # TAB 2: ARMAZENAMENTO
            with tab2:
                st.markdown("#### Evolução dos Níveis de Armazenamento (COM DESLIZAMENTO)")
                niveis_tanques_ot = pd.DataFrame({
                    "Bateria (kWh)": resultado_ot['nivel_bateria'], 
                    "Biogas (m³)": resultado_ot['nivel_biogas'],
                    "Diesel (L)": resultado_ot['nivel_diesel'],
                })
                fig2 = Grafico_linha(niveis_tanques_ot, xlabel="Tempo (min)", ylabel="Energia/Volume", title="Dinâmica dos Sistemas de Armazenamento")
                st.plotly_chart(fig2, width='stretch', key=f"analise3_armazenamento_{idx}")
                
                st.divider()
                col1, col2, col3 = st.columns(3)
                with col1:
                    bateria_pct = (resultado_ot['nivel_bateria'][-1] / microrrede.bateria.capacidade * 100) if microrrede.bateria else 0
                    st.metric("🔋 Bateria Final", f"{resultado_ot['nivel_bateria'][-1]:.2f} kWh", f"{bateria_pct:.1f}%")
                with col2:
                    st.metric("⛽ Diesel Final", f"{resultado_ot['nivel_diesel'][-1]:.2f} L")
                with col3:
                    st.metric("💨 Biogas Final", f"{resultado_ot['nivel_biogas'][-1]:.2f} m³" if resultado_ot['nivel_biogas'][-1] > 0 else "Sem biogas")
            
            # TAB 3: CUSTOS
            with tab3:
                st.markdown("#### Análise de Custos (COM DESLIZAMENTO)")
                
                # Calcula custos por fonte
                custos_ot = _calculate_source_costs(resultado_ot, microrrede)
                
                # Gráficos de custo
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Custo Instantâneo**")
                    custo_inst_df_ot = pd.DataFrame({"Custo (R$)": resultado_ot['custo_total_instantaneo']})
                    fig_inst = Grafico_linha(custo_inst_df_ot, xlabel="Tempo (min)", ylabel="Custo (R$)", title="")
                    st.plotly_chart(fig_inst, width='stretch', key=f"analise3_custo_inst_{idx}")
                
                with col2:
                    st.markdown("**Custo Acumulado**")
                    custo_acumulado_ot = np.cumsum(resultado_ot['custo_total_instantaneo'])
                    custo_acu_df_ot = pd.DataFrame({"Custo Acumulado (R$)": custo_acumulado_ot})
                    fig_acu = Grafico_linha(custo_acu_df_ot, xlabel="Tempo (min)", ylabel="Custo Acumulado (R$)", title="")
                    st.plotly_chart(fig_acu, width='stretch', key=f"analise3_custo_acu_{idx}")
                
                st.divider()
                st.markdown("**Custo por Fonte:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("☀️ Solar", f"R$ {custos_ot['solar']:,.2f}")
                    st.metric("🔥 Diesel", f"R$ {custos_ot['diesel']:,.2f}")
                with col2:
                    st.metric("🔋 Bateria", f"R$ {custos_ot['bateria']:,.2f}")
                    st.metric("💨 Biogas", f"R$ {custos_ot['biogas']:,.2f}")
                with col3:
                    st.metric("🏢 Concessionária", f"R$ {custos_ot['concessionaria']:,.2f}")
            
            # TAB 4: RESUMO DE FONTES
            with tab4:
                st.markdown("#### Comparação de Fontes de Energia")
                
                # Tabela comparativa com custos por fonte
                st.write("**Uso e Custo por Fonte:**")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Custo Ordenado (menor para maior):**")
                    st.dataframe(resultado_ot['custo_kwh_ordenado'], width='stretch')
                
                with col2:
                    comparacao_fontes_ot = _create_source_comparison_df(
                        resultado_ot['total_uso_solar'],
                        resultado_ot['total_uso_bateria'],
                        resultado_ot['total_uso_diesel'],
                        resultado_ot['total_uso_concessionaria'],
                        microrrede
                    )
                    st.markdown("**Tabela Comparativa de Fontes:**")
                    st.dataframe(comparacao_fontes_ot, width='stretch', hide_index=True)
                
                st.divider()
                st.write("**Diagrama de Fluxo:**")
                sankey_chart(
                    uso_diesel=resultado_ot['total_uso_diesel'],
                    uso_bateria=resultado_ot['total_uso_bateria'],
                    uso_concessionaria=resultado_ot['total_uso_concessionaria'],
                    uso_biogas=resultado_ot['total_uso_biogas'],
                    uso_solar=resultado_ot['total_uso_solar'],
                    sobra=resultado_ot['total_sobra'],
                    carga=resultado_ot['total_carga']
                )
            
            # TAB 5: DETALHES
            with tab5:
                st.markdown("#### Dados Horários Detalhados (COM DESLIZAMENTO)")
                
                # Criar dataframe completo
                df_completo_ot = pd.DataFrame({
                    "Tempo (min)": range(len(resultado_ot['curva_carga'])),
                    "Demanda (kW)": resultado_ot['curva_carga'],
                    "Solar (kW)": resultado_ot['uso_solar'],
                    "Diesel (kW)": resultado_ot['uso_diesel'],
                    "Biogas (kW)": resultado_ot['uso_biogas'],
                    "Bateria Descarga (kW)": resultado_ot['uso_bateria'],
                    "Bateria Recarga (kW)": resultado_ot['recarga_bateria'],
                    "Concessionária (kW)": resultado_ot['uso_concessionaria'],
                    "Nível Bateria (kWh)": resultado_ot['nivel_bateria'],
                    "Nível Diesel (L)": resultado_ot['nivel_diesel'],
                    "Nível Biogas (m³)": resultado_ot['nivel_biogas'],
                    "Custo Instantâneo (R$)": resultado_ot['custo_total_instantaneo']
                })
                
                st.dataframe(df_completo_ot.style.format("{:.4f}"), width='stretch')
                
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
                    st.metric("", "")
                with col2:
                    st.metric("💰 Com Deslizamento", f"R$ {custo_total_ot:,.2f}")
                    st.metric("", "")
                with col3:
                    st.metric("📊 Economia Total", f"-R$ {metricas['economia']:,.2f}")
                    st.metric("", "")
                with col4:
                    st.metric("📈 Percentual", f"{metricas['economia_pct']:.2f}%")
                    st.metric("", "")
                
                st.divider()
                
                # Comparação de curva de carga
                st.markdown("#### Mudança na Curva de Carga")
                comparacao_cargas = pd.DataFrame({
                    "Original (kW)": resultado_or['curva_carga'],
                    "Otimizada (kW)": resultado_ot['curva_carga'],
                })
                fig_comp_carga = Grafico_linha(comparacao_cargas, xlabel="Tempo (min)", ylabel="Demanda (kW)", title="Comparação de Curvas de Carga")
                st.plotly_chart(fig_comp_carga, width='stretch', key=f"analise3_comp_carga_{idx}")
                
                st.divider()
                
                # Comparação de custos
                st.markdown("#### Comparação de Custos Acumulados")
                custo_acu_or = np.cumsum(resultado_or['custo_total_instantaneo'])
                custo_acu_ot = np.cumsum(resultado_ot['custo_total_instantaneo'])
                comparacao_custos = pd.DataFrame({
                    "Sem Deslizamento (R$)": custo_acu_or,
                    "Com Deslizamento (R$)": custo_acu_ot,
                })
                fig_comp_custo = Grafico_linha(comparacao_custos, xlabel="Tempo (min)", ylabel="Custo Acumulado (R$)", title="")
                st.plotly_chart(fig_comp_custo, width='stretch', key=f"analise3_comp_custo_{idx}")
                
                st.divider()
                
                # Tabela comparativa de fontes
                st.markdown("#### Resumo Comparativo por Fonte")
                tabela_comp = pd.DataFrame({
                    "Fonte": ["☀️ Solar", "🔋 Bateria", "💨 Biogas", "🔥 Diesel", "🏢 Concessionária"],
                    "Original (kWh)": [
                        f"{resultado_or['total_uso_solar']:,.2f}",
                        f"{resultado_or['total_uso_bateria']:,.2f}",
                        f"{resultado_or['total_uso_biogas']:,.2f}",
                        f"{resultado_or['total_uso_diesel']:,.2f}",
                        f"{resultado_or['total_uso_concessionaria']:,.2f}"
                    ],
                    "Otimizado (kWh)": [
                        f"{resultado_ot['total_uso_solar']:,.2f}",
                        f"{resultado_ot['total_uso_bateria']:,.2f}",
                        f"{resultado_ot['total_uso_biogas']:,.2f}",
                        f"{resultado_ot['total_uso_diesel']:,.2f}",
                        f"{resultado_ot['total_uso_concessionaria']:,.2f}"
                    ]
                })
                st.dataframe(tabela_comp, width='stretch', hide_index=True)
st.text("Comparação entre Análise 2, Análise 3 e Análise 5 (sem venda para rede)")
if st.button("Comparação de Custos"):
    for idx, microrrede in enumerate(microrredes):
        with st.container(border=True):
            st.subheader(f"{microrrede} - Comparação de Custos (A2 vs A3 vs A5)", divider=True, width='stretch', text_alignment='center')
            
            # ===== EXECUTAR AS 3 ANÁLISES =====
            
            # Análise 2 (Heurística sem deslizamento)
            with st.spinner("Executando Análise 2 (Heurística)..."):
                (custo_kwh_ordenado_a2, total_uso_diesel_a2, total_uso_bateria_a2, total_uso_concessionaria_a2,
                 total_uso_biogas_a2, total_uso_solar_a2, total_sobra_a2, total_carga_a2, total_a2,
                 uso_energia_a2, niveis_tanque_a2, custo_total_a2_val, custo_total_instantaneo_a2) = Analise2.executar(microrrede, config)
            
            # Análise 3 (Heurística com deslizamento)
            with st.spinner("Executando Análise 3 (Heurística com Deslizamento)..."):
                resultado_a3 = Analise3.analise_3(microrrede, config)
                (custo_kwh_ordenado_a3, total_uso_diesel_a3, total_uso_bateria_a3, total_uso_concessionaria_a3, 
                 total_uso_biogas_a3, total_uso_solar_a3, total_sobra_a3, total_carga_a3, uso_solar_a3, 
                 uso_bateria_a3, uso_biogas_a3, uso_diesel_a3, uso_concessionaria_a3, curva_carga_a3, 
                 nivel_bateria_a3, nivel_biogas_a3, nivel_diesel_a3, custo_total_instantaneo_a3, recarga_bateria_a3) = resultado_a3['otimizado']
            
            # Análise 5 (MILP com deslizamento, sem venda)
            with st.spinner("Executando Análise 5 (MILP com Deslizamento)..."):
                df_resultado_a5, custos_a5, solucao_a5 = analise_milp_com_deslizamento(microrrede)
            
            if df_resultado_a5 is None:
                st.error("❌ Não foi possível resolver MILP")
                continue
            
            # ===== CALCULAR CUSTOS =====
            custo_total_a2 = np.sum(custo_total_instantaneo_a2)
            custo_total_a3 = np.sum(custo_total_instantaneo_a3)
            custo_total_a5 = custos_a5.get('Total', 0)
             
            # Calcular custo instantâneo para MILP
            bateria = microrrede.bateria
            diesel = microrrede.diesel
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
                if concessionaria is not None:
                    custo_i += df_resultado_a5['Concessionaria'].iloc[i] * concessionaria.tarifa / 60
                custo_instantaneo_a5[i] = custo_i
            
            # ===== MÉTRICAS COMPARATIVAS =====
            menor_custo = min(custo_total_a2, custo_total_a3, custo_total_a5)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                delta_a2 = f"{'Menor custo' if custo_total_a2 == menor_custo else f'+R$ {custo_total_a2 - menor_custo:,.2f}'}"
                st.metric("💰 Análise 2 (Heurística)", f"R$ {custo_total_a2:,.2f}", delta_a2, delta_color="inverse" if custo_total_a2 == menor_custo else "normal")
            with col2:
                delta_a3 = f"{'Menor custo' if custo_total_a3 == menor_custo else f'+R$ {custo_total_a3 - menor_custo:,.2f}'}"
                st.metric("🔄 Análise 3 (Heurística + Deslizamento)", f"R$ {custo_total_a3:,.2f}", delta_a3, delta_color="inverse" if custo_total_a3 == menor_custo else "normal")
            with col3:
                delta_a5 = f"{'Menor custo' if custo_total_a5 == menor_custo else f'+R$ {custo_total_a5 - menor_custo:,.2f}'}"
                st.metric("🎯 Análise 5 (MILP + Deslizamento)", f"R$ {custo_total_a5:,.2f}", delta_a5, delta_color="inverse" if custo_total_a5 == menor_custo else "normal")
            
            # ===== GRÁFICO DE CUSTO ACUMULADO =====
            st.subheader("📈 Custo Acumulado ao Longo do Dia")
            
            custo_acumulado_a2 = np.cumsum(custo_total_instantaneo_a2)
            custo_acumulado_a3 = np.cumsum(custo_total_instantaneo_a3)
            custo_acumulado_a5 = np.cumsum(custo_instantaneo_a5)
            
            df_custo_acu = pd.DataFrame({
                "Análise 2 (Heurística)": custo_acumulado_a2,
                "Análise 3 (Heurística + Deslizamento)": custo_acumulado_a3,
                "Análise 5 (MILP + Deslizamento)": custo_acumulado_a5
            })
            
            fig_acu = Grafico_linha(df_custo_acu, 
                               xlabel="Tempo (min)", 
                               ylabel="Custo Acumulado (R$)", 
                               title="Custo Acumulado ao Longo do Dia")
            st.plotly_chart(fig_acu, width='stretch', key=f"comp_a2_a3_a5_custo_acu_{idx}")
            
            # ===== GRÁFICO DE CUSTO INSTANTÂNEO =====
            st.subheader("⏱️ Custo Instantâneo de Operação")
            
            df_custo_inst = pd.DataFrame({
                "Análise 2": custo_total_instantaneo_a2,
                "Análise 3": custo_total_instantaneo_a3,
                "Análise 5": custo_instantaneo_a5
            })
            
            fig_inst = Grafico_linha(df_custo_inst,
                                xlabel="Tempo (min)",
                                ylabel="Custo (R$)",
                                title="Custo Instantâneo de Operação")
            st.plotly_chart(fig_inst, width='stretch', key=f"comp_a2_a3_a5_custo_inst_{idx}")
            
            # ===== DESPACHO DE ENERGIA POR ANÁLISE =====
            st.subheader("⚡ Despacho de Energia por Análise")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Análise 2 (Heurística)**")
                fig_desp_a2 = Grafico_linha(uso_energia_a2, xlabel="Tempo (min)", ylabel="Potência (kW)", title="")
                st.plotly_chart(fig_desp_a2, width='stretch', key=f"comp_desp_a2_{idx}")
            
            with col2:
                st.write("**Análise 3 (Heurística + Deslizamento)**")
                despacho_a3 = pd.DataFrame({
                    "Solar": uso_solar_a3,
                    "Bateria": uso_bateria_a3,
                    "Diesel": uso_diesel_a3,
                    "Concessionária": uso_concessionaria_a3,
                    "Recarga Bateria": -recarga_bateria_a3
                })
                fig_desp_a3 = Grafico_linha(despacho_a3, xlabel="Tempo (min)", ylabel="Potência (kW)", title="")
                st.plotly_chart(fig_desp_a3, width='stretch', key=f"comp_desp_a3_{idx}")
            
            with col3:
                st.write("**Análise 5 (MILP + Deslizamento)**")
                despacho_a5 = pd.DataFrame({
                    "Solar": df_resultado_a5['Solar'],
                    "Bateria": df_resultado_a5['Bateria'],
                    "Diesel": df_resultado_a5['Diesel'],
                    "Concessionária": df_resultado_a5['Concessionaria'],
                    "Recarga Bateria": -np.abs(df_resultado_a5['Carga_Bateria'])
                })
                fig_desp_a5 = Grafico_linha(despacho_a5, xlabel="Tempo (min)", ylabel="Potência (kW)", title="")
                st.plotly_chart(fig_desp_a5, width='stretch', key=f"comp_desp_a5_{idx}")
            
            # ===== TABELA COMPARATIVA =====
            st.subheader("📊 Resumo Comparativo por Fonte")
            
            total_solar_a5 = df_resultado_a5['Solar'].sum()
            total_bateria_a5 = df_resultado_a5['Bateria'].sum()
            total_diesel_a5 = df_resultado_a5['Diesel'].sum()
            total_conc_a5 = df_resultado_a5['Concessionaria'].sum()
            
            df_comparativo = pd.DataFrame({
                'Fonte': ['☀️ Solar', '🔋 Bateria', '🔥 Diesel', '🏢 Concessionária', '💰 TOTAL'],
                'A2 Energia (kWh)': [
                    f"{total_uso_solar_a2:.2f}",
                    f"{total_uso_bateria_a2:.2f}",
                    f"{total_uso_diesel_a2:.2f}",
                    f"{total_uso_concessionaria_a2:.2f}",
                    f"{total_uso_solar_a2 + total_uso_bateria_a2 + total_uso_diesel_a2 + total_uso_concessionaria_a2:.2f}"
                ],
                'A2 Custo (R$)': [
                    f"R$ {total_uso_solar_a2 * (solar.custo_kwh if solar else 0) / 60:.2f}",
                    f"R$ {total_uso_bateria_a2 * (bateria.custo_kwh if bateria else 0) / 60:.2f}",
                    f"R$ {total_uso_diesel_a2 * (diesel.custo_por_kWh if diesel else 0) / 60:.2f}",
                    f"R$ {total_uso_concessionaria_a2 * (concessionaria.tarifa if concessionaria else 0) / 60:.2f}",
                    f"R$ {custo_total_a2:,.2f}"
                ],
                'A3 Energia (kWh)': [
                    f"{total_uso_solar_a3:.2f}",
                    f"{total_uso_bateria_a3:.2f}",
                    f"{total_uso_diesel_a3:.2f}",
                    f"{total_uso_concessionaria_a3:.2f}",
                    f"{total_uso_solar_a3 + total_uso_bateria_a3 + total_uso_diesel_a3 + total_uso_concessionaria_a3:.2f}"
                ],
                'A3 Custo (R$)': [
                    f"R$ {total_uso_solar_a3 * (solar.custo_kwh if solar else 0) / 60:.2f}",
                    f"R$ {total_uso_bateria_a3 * (bateria.custo_kwh if bateria else 0) / 60:.2f}",
                    f"R$ {total_uso_diesel_a3 * (diesel.custo_por_kWh if diesel else 0) / 60:.2f}",
                    f"R$ {total_uso_concessionaria_a3 * (concessionaria.tarifa if concessionaria else 0) / 60:.2f}",
                    f"R$ {custo_total_a3:,.2f}"
                ],
                'A5 Energia (kWh)': [
                    f"{total_solar_a5:.2f}",
                    f"{total_bateria_a5:.2f}",
                    f"{total_diesel_a5:.2f}",
                    f"{total_conc_a5:.2f}",
                    f"{total_solar_a5 + total_bateria_a5 + total_diesel_a5 + total_conc_a5:.2f}"
                ],
                'A5 Custo (R$)': [
                    f"R$ {total_solar_a5 * (solar.custo_kwh if solar else 0) / 60:.2f}",
                    f"R$ {total_bateria_a5 * (bateria.custo_kwh if bateria else 0) / 60:.2f}",
                    f"R$ {total_diesel_a5 * (diesel.custo_por_kWh if diesel else 0) / 60:.2f}",
                    f"R$ {total_conc_a5 * (concessionaria.tarifa if concessionaria else 0) / 60:.2f}",
                    f"R$ {custo_total_a5:,.2f}"
                ]
            })
            st.dataframe(df_comparativo, hide_index=True, width='stretch')
            
            # ===== ECONOMIA RELATIVA =====
            st.subheader("💹 Economia Relativa")
            col1, col2, col3 = st.columns(3)
            with col1:
                eco_a3_vs_a2 = custo_total_a2 - custo_total_a3
                eco_a3_vs_a2_pct = (eco_a3_vs_a2 / custo_total_a2 * 100) if custo_total_a2 > 0 else 0
                st.metric("A3 vs A2", f"R$ {eco_a3_vs_a2:,.2f}", f"{eco_a3_vs_a2_pct:.2f}%", delta_color="inverse" if eco_a3_vs_a2 >= 0 else "normal")
            with col2:
                eco_a5_vs_a2 = custo_total_a2 - custo_total_a5
                eco_a5_vs_a2_pct = (eco_a5_vs_a2 / custo_total_a2 * 100) if custo_total_a2 > 0 else 0
                st.metric("A5 vs A2", f"R$ {eco_a5_vs_a2:,.2f}", f"{eco_a5_vs_a2_pct:.2f}%", delta_color="inverse" if eco_a5_vs_a2 >= 0 else "normal")
            with col3:
                eco_a5_vs_a3 = custo_total_a3 - custo_total_a5
                eco_a5_vs_a3_pct = (eco_a5_vs_a3 / custo_total_a3 * 100) if custo_total_a3 > 0 else 0
                st.metric("A5 vs A3", f"R$ {eco_a5_vs_a3:,.2f}", f"{eco_a5_vs_a3_pct:.2f}%", delta_color="inverse" if eco_a5_vs_a3 >= 0 else "normal")
            

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
                #if biogas is not None:
                #    custo_i += df_resultado_m5['Biogas'].iloc[i] * biogas.custo_por_kWh / 60
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
                #if biogas is not None:
                #    custo_i += df_resultado_m51['Biogas'].iloc[i] * biogas.custo_por_kWh / 60
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
            st.plotly_chart(fig_acu, width='stretch', key=f"comp_m5_m51_custo_acu_{idx}")
            
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
            st.plotly_chart(fig_inst, width='stretch', key=f"comp_m5_m51_custo_inst_{idx}")
            
            # ===== TABELA COMPARATIVA DE CUSTOS =====
            st.subheader("📊 Resumo Detalhado de Custos")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Método 5 (COM venda)**")
                total_solar_m5 = df_resultado_m5['Solar'].sum()
                total_bateria_m5 = df_resultado_m5['Bateria'].sum()
                total_diesel_m5 = df_resultado_m5['Diesel'].sum()
                #total_biogas_m5 = df_resultado_m5['Biogas'].sum()
                total_conc_m5 = df_resultado_m5['Concessionaria'].sum()
                total_venda_m5 = df_resultado_m5['Venda'].sum()
                
                df_custos_m5 = pd.DataFrame({
                    #'Fonte': ['☀️ Solar', '🔋 Bateria', '💨 Biogas', '🔥 Diesel', '🏢 Concessionária', '📤 Venda (Receita)'],
                    'Fonte': ['☀️ Solar', '🔋 Bateria',  '🔥 Diesel', '🏢 Concessionária', '📤 Venda (Receita)'],
                    'Energia (kWh)': [
                        f"{total_solar_m5:.2f}",
                        f"{total_bateria_m5:.2f}",
                        #f"{total_biogas_m5:.2f}",
                        f"{total_diesel_m5:.2f}",
                        f"{total_conc_m5:.2f}",
                        f"{total_venda_m5:.2f}"
                    ],
                    'Custo (R$)': [
                        f"{total_solar_m5 * (solar.custo_kwh if solar else 0):.2f}",
                        f"{total_bateria_m5 * (bateria.custo_kwh if bateria else 0):.2f}",
                       # f"{total_biogas_m5 * (biogas.custo_por_kWh if biogas else 0):.2f}",
                        f"{total_diesel_m5 * (diesel.custo_por_kWh if diesel else 0):.2f}",
                        f"{total_conc_m5 * (concessionaria.tarifa if concessionaria else 0):.2f}",
                        f"-{total_venda_m5 * (concessionaria.tarifa * 0.8 if concessionaria else 0):.2f}"
                    ]
                })
                st.dataframe(df_custos_m5, hide_index=True, width='stretch')
            
            with col2:
                st.write("**Método 5.1 (SEM venda)**")
                total_solar_m51 = df_resultado_m51['Solar'].sum()
                total_bateria_m51 = df_resultado_m51['Bateria'].sum()
                total_diesel_m51 = df_resultado_m51['Diesel'].sum()
                #total_biogas_m51 = df_resultado_m51['Biogas'].sum()
                total_conc_m51 = df_resultado_m51['Concessionaria'].sum()
                
                df_custos_m51 = pd.DataFrame({
                    #'Fonte': ['☀️ Solar', '🔋 Bateria', '💨 Biogas', '🔥 Diesel', '🏢 Concessionária'],
                    'Fonte': ['☀️ Solar', '🔋 Bateria', '🔥 Diesel', '🏢 Concessionária'],
                    
                    'Energia (kWh)': [
                        f"{total_solar_m51:.2f}",
                        f"{total_bateria_m51:.2f}",
                      #  f"{total_biogas_m51:.2f}",
                        f"{total_diesel_m51:.2f}",
                        f"{total_conc_m51:.2f}"
                    ],
                    'Custo (R$)': [
                        f"{total_solar_m51 * (solar.custo_kwh if solar else 0):.2f}",
                        f"{total_bateria_m51 * (bateria.custo_kwh if bateria else 0):.2f}",
                       # f"{total_biogas_m51 * (biogas.custo_por_kWh if biogas else 0):.2f}",
                        f"{total_diesel_m51 * (diesel.custo_por_kWh if diesel else 0):.2f}",
                        f"{total_conc_m51 * (concessionaria.tarifa if concessionaria else 0):.2f}"
                    ]
                })
                st.dataframe(df_custos_m51, hide_index=True, width='stretch')
            
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
                    #"Biogas": df_resultado_m5['Biogas'],
                    "Concessionária": df_resultado_m5['Concessionaria'],
                    "Venda": df_resultado_m5['Venda'],
                    "Recarga Bateria": -np.abs(df_resultado_m5['Carga_Bateria'])
                })
                fig_desp_m5 = Grafico_linha(despacho_m5, xlabel="Tempo (min)", ylabel="Potência (kW)", title="")
                st.plotly_chart(fig_desp_m5, width='stretch', key=f"comp_m5_m51_desp_m5_{idx}")
            
            with col2:
                st.write("**Método 5.1 (SEM venda)**")
                despacho_m51 = pd.DataFrame({
                    "Solar": df_resultado_m51['Solar'],
                    "Bateria": df_resultado_m51['Bateria'],
                    "Diesel": df_resultado_m51['Diesel'],
                   # "Biogas": df_resultado_m51['Biogas'],
                    "Concessionária": df_resultado_m51['Concessionaria'],
                    "Recarga Bateria": -np.abs(df_resultado_m51['Carga_Bateria'])
                })
                fig_desp_m51 = Grafico_linha(despacho_m51, xlabel="Tempo (min)", ylabel="Potência (kW)", title="")
                st.plotly_chart(fig_desp_m51, width='stretch', key=f"comp_m5_m51_desp_m51_{idx}")

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
                 nivel_bateria_m3, nivel_biogas_m3, nivel_diesel_m3, custo_total_instantaneo_m3, recarga_bateria_m3) = resultado_m3['otimizado']
            
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
              #  if biogas is not None:
               #     custo_i += df_resultado_51['Biogas'].iloc[i] * biogas.custo_por_kWh / 60
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
            st.plotly_chart(fig_acu, width='stretch', key=f"comp_m3_m51_custo_acu_{idx}")
            
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
            st.plotly_chart(fig_inst, width='stretch', key=f"comp_m3_m51_custo_inst_{idx}")
            
            # ===== TABELA COMPARATIVA DE CUSTOS =====
            st.subheader("📊 Resumo Detalhado de Custos")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Método 3 (Heurística com deslizamento)**")
                df_custos_m3 = pd.DataFrame({
                    #'Fonte': ['☀️ Solar', '🔋 Bateria', '💨 Biogas', '🔥 Diesel', '🏢 Concessionária'],
                    'Fonte': ['☀️ Solar', '🔋 Bateria',  '🔥 Diesel', '🏢 Concessionária'],
                    'Energia (kWh)': [
                        f"{total_uso_solar_m3:.2f}",
                        f"{total_uso_bateria_m3:.2f}",
                        #f"{total_uso_biogas_m3:.2f}",
                        f"{total_uso_diesel_m3:.2f}",
                        f"{total_uso_concessionaria_m3:.2f}"
                    ],
                    'Custo (R$)': [
                        f"{total_uso_solar_m3 * (solar.custo_kwh if solar else 0):.2f}",
                        f"{total_uso_bateria_m3 * (bateria.custo_kwh if bateria else 0):.2f}",
                        #f"{total_uso_biogas_m3 * (biogas.custo_por_kWh if biogas else 0):.2f}",
                        f"{total_uso_diesel_m3 * (diesel.custo_por_kWh if diesel else 0):.2f}",
                        f"{total_uso_concessionaria_m3 * (concessionaria.tarifa if concessionaria else 0):.2f}"
                    ]
                })
                st.dataframe(df_custos_m3, hide_index=True, width='stretch')
            
            with col2:
                st.write("**Método 5.1 (MILP SEM venda)**")
                total_solar_51 = df_resultado_51['Solar'].sum()
                total_bateria_51 = df_resultado_51['Bateria'].sum()
                total_diesel_51 = df_resultado_51['Diesel'].sum()
                #total_biogas_51 = df_resultado_51['Biogas'].sum()
                total_conc_51 = df_resultado_51['Concessionaria'].sum()
                
                df_custos_51 = pd.DataFrame({
                    #'Fonte': ['☀️ Solar', '🔋 Bateria', '💨 Biogas', '🔥 Diesel', '🏢 Concessionária'],
                    'Fonte': ['☀️ Solar', '🔋 Bateria',  '🔥 Diesel', '🏢 Concessionária'],
                    'Energia (kWh)': [
                        f"{total_solar_51:.2f}",
                        f"{total_bateria_51:.2f}",
                 #       f"{total_biogas_51:.2f}",
                        f"{total_diesel_51:.2f}",
                        f"{total_conc_51:.2f}"
                    ],
                    'Custo (R$)': [
                        f"{total_solar_51 * (solar.custo_kwh if solar else 0):.2f}",
                        f"{total_bateria_51 * (bateria.custo_kwh if bateria else 0):.2f}",
                  #      f"{total_biogas_51 * (biogas.custo_por_kWh if biogas else 0):.2f}",
                        f"{total_diesel_51 * (diesel.custo_por_kWh if diesel else 0):.2f}",
                        f"{total_conc_51 * (concessionaria.tarifa if concessionaria else 0):.2f}"
                    ]
                })
                st.dataframe(df_custos_51, hide_index=True, width='stretch')
            
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
                    "Concessionária": uso_concessionaria_m3,
                    "Recarga Bateria": -recarga_bateria_m3
                })
                fig_desp_m3 = Grafico_linha(despacho_m3, xlabel="Tempo (min)", ylabel="Potência (kW)", title="")
                st.plotly_chart(fig_desp_m3, width='stretch', key=f"comp_m3_m51_desp_m3_{idx}")
            
            with col2:
                st.write("**Método 5.1 (MILP SEM venda)**")
                despacho_51 = pd.DataFrame({
                    "Solar": df_resultado_51['Solar'],
                    "Bateria": df_resultado_51['Bateria'],
                    "Diesel": df_resultado_51['Diesel'],
                    #"Biogas": df_resultado_51['Biogas'],
                    "Concessionária": df_resultado_51['Concessionaria'],
                    "Recarga Bateria": -np.abs(df_resultado_51['Carga_Bateria'])
                })
                fig_desp_51 = Grafico_linha(despacho_51, xlabel="Tempo (min)", ylabel="Potência (kW)", title="")
                st.plotly_chart(fig_desp_51, width='stretch', key=f"comp_m3_m51_desp_51_{idx}")
            
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
                st.plotly_chart(fig_nivel_m3, width='stretch', key=f"comp_m3_m51_nivel_m3_{idx}")
            
            with col2:
                st.write("**Método 5.1**")
                nivel_51 = pd.DataFrame({
                    "Bateria (kWh)": df_resultado_51['Carga_Bateria'] if 'Carga_Bateria' in df_resultado_51.columns else np.zeros(len(df_resultado_51)),
                })
                if 'Carga_Bateria' in df_resultado_51.columns:
                    fig_nivel_51 = Grafico_linha(nivel_51, xlabel="Tempo (min)", ylabel="Capacidade", title="")
                    st.plotly_chart(fig_nivel_51, width='stretch', key=f"comp_m3_m51_nivel_51_{idx}")
                else:
                    st.info("Informações de nível de armazenamento não disponíveis")

st.text("Uso otimizado das redes com a compra e venda de energia entre as micorredes com a filosofia de eficiencia da microrrede")
if st.button("Analise 4 Heurística com todas as otmizações "):
    #analise4(microrredes)
    pass
st.text("Uso otimizado das redes com a compra e venda de energia entre as microrredes com a filosofia de eficiencia global")
if st.button("Análise 5 - MILP"):
    for idx, microrrede in enumerate(microrredes):
        with st.container(border=True):
            analise_5_milp(microrrede, index=idx)
    analise_5_milp_multi(microrredes)

st.text("Otimização usando Particle Swarm Optimization (PSO) - Metaheurística")
if st.button("Análise 6 - PSO"):
    for microrrede in microrredes:
        with st.container(border=True):
            analise_6_pso(microrrede)
    analise_6_pso_multi(microrredes)