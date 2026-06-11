import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from models.Microrrede import Microrrede
from models.CRUD import Ler
from analises.config import ConfigAnalise
from mercado.simulacao_simultanea import SimuladorMercado, OtimizadorPosDia

st.set_page_config(page_title="Mercado de Energia", layout="wide")
st.title("⚡ Mercado de Energia P2P")
st.markdown("Simulação simultânea de todas as microrredes com mercado de energia entre elas.")

# ============================================================
# CONFIGURAÇÕES
# ============================================================

st.header("⚙️ Configurações")

todas_microrredes = Ler(Microrrede)

if not todas_microrredes:
    st.warning("Nenhuma microrrede cadastrada. Cadastre pelo menos 2 microrredes para usar o mercado.")
    st.stop()

mgs_selecionadas = st.multiselect(
    "Microrredes Participantes:", 
    todas_microrredes, 
    default=todas_microrredes,
    format_func=lambda x: str(x)
)

if len(mgs_selecionadas) < 2:
    st.warning("Selecione pelo menos 2 microrredes para o mercado P2P.")
    st.stop()

col_cfg1, col_cfg2 = st.columns(2)

with col_cfg1:
    st.subheader("Fontes Habilitadas")
    solar_ligado = st.checkbox("☀️ Solar", value=True)
    bateria_ligada = st.checkbox("🔋 Bateria", value=True)
    diesel_ligado = st.checkbox("⛽ Diesel", value=True)
    biogas_ligado = st.checkbox("🌿 Biogás", value=True)

with col_cfg2:
    st.subheader("Parâmetros do Mercado")
    margem = st.slider("Margem de Lucro na Venda (%)", 0.0, 20.0, 5.0, 0.5) / 100.0
    coef_perda = st.slider("Fator de Perda (% / km)", 0.0, 1.0, 0.4, 0.1) / 100.0

config = ConfigAnalise(
    solar_ligado=solar_ligado,
    bateria_ligada=bateria_ligada,
    diesel_ligado=diesel_ligado,
    biogas_ligado=biogas_ligado,
)

st.divider()

# ============================================================
# SIMULAÇÃO DO DIA
# ============================================================

executar = st.button("🚀 Simular Dia Completo", type="primary", use_container_width=True)

if executar:
    # Recarregar MGs do banco para garantir sessão ativa
    from models.CRUD import Ler_Objeto
    microrredes_frescas = [Ler_Objeto(Microrrede, mg.id) for mg in mgs_selecionadas]
    
    progress = st.progress(0, text="Simulando dia...")
    
    def callback_progresso(t, total):
        progress.progress(t / total, text=f"Simulando... {t//60:02d}:{t%60:02d} / 24:00")
    
    simulador = SimuladorMercado(
        microrredes=microrredes_frescas,
        config=config,
        margem_venda=margem,
        coef_perda_km=coef_perda,
    )
    
    resultado = simulador.simular(callback=callback_progresso)
    progress.progress(1.0, text="Simulação concluída!")
    
    # Salva resultado na sessão para usar na otimização
    st.session_state['resultado_simulacao'] = resultado
    st.session_state['mgs_selecionadas'] = mgs_selecionadas
    st.session_state['config'] = config
    st.session_state['margem'] = margem
    st.session_state['coef_perda'] = coef_perda

# ============================================================
# EXIBIR RESULTADOS
# ============================================================

if 'resultado_simulacao' in st.session_state:
    resultado = st.session_state['resultado_simulacao']
    mgs_sel = st.session_state['mgs_selecionadas']
    
    st.divider()
    st.header("📊 Resultados da Simulação")
    
    # --- MÉTRICAS GLOBAIS ---
    c1, c2, c3, c4 = st.columns(4)
    
    custo_iso_total = sum(resultado.custo_isolado_por_mg.values())
    economia_pct = (resultado.economia_total / custo_iso_total * 100) if custo_iso_total > 0 else 0
    
    c1.metric("💰 Economia Total", f"R$ {resultado.economia_total:,.2f}", f"{economia_pct:.1f}%")
    c2.metric("⚡ Volume Negociado", f"{resultado.volume_total_kwh:,.1f} kWh")
    c3.metric("📉 Perdas por Distância", f"{resultado.perdas_totais_kwh:,.2f} kWh")
    c4.metric("🔄 Nº Transações", f"{resultado.num_transacoes:,}")
    
    st.divider()
    
    # --- GRÁFICO DE CUSTOS COMPARATIVOS ---
    st.subheader("💰 Custos: Operação Isolada vs Com Mercado P2P")
    
    nomes = list(resultado.custo_isolado_por_mg.keys())
    df_custos = pd.DataFrame({
        "Microrrede": nomes,
        "Operação Isolada (R$)": [resultado.custo_isolado_por_mg[n] for n in nomes],
        "Com Mercado P2P (R$)": [resultado.custo_total_por_mg[n] for n in nomes],
    })
    
    fig_custos = px.bar(
        df_custos, x="Microrrede",
        y=["Operação Isolada (R$)", "Com Mercado P2P (R$)"],
        barmode='group', text_auto='.2s',
        color_discrete_map={
            "Operação Isolada (R$)": "#EF553B",
            "Com Mercado P2P (R$)": "#00CC96"
        }
    )
    fig_custos.update_layout(yaxis_title="Custo Diário (R$)")
    st.plotly_chart(fig_custos, use_container_width=True, key="sim_custos")
    
    st.divider()
    
    # --- BALANÇO POR MICRORREDE ---
    st.subheader("📋 Balanço Financeiro por Microrrede")
    
    df_balanco = pd.DataFrame({
        "Microrrede": nomes,
        "Custo Isolado (R$)": [f"R$ {resultado.custo_isolado_por_mg[n]:,.2f}" for n in nomes],
        "Custo com Mercado (R$)": [f"R$ {resultado.custo_total_por_mg[n]:,.2f}" for n in nomes],
        "Vendas (R$)": [f"R$ {resultado.receita_por_mg[n]:,.2f}" for n in nomes],
        "Compras (R$)": [f"R$ {resultado.gasto_compras_por_mg[n]:,.2f}" for n in nomes],
        "Economia (R$)": [f"R$ {resultado.economia_por_mg[n]:,.2f}" for n in nomes],
    })
    st.dataframe(df_balanco, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # --- GRÁFICOS DE GERAÇÃO/CONSUMO POR MG ---
    st.subheader("📈 Perfil Energético do Dia (por Microrrede)")
    
    cores = {
        'Solar': '#FFD700',
        'Bateria': '#32CD32', 
        'Diesel': '#A9A9A9',
        'Biogás': '#8B4513',
        'Concessionária': '#4169E1',
        'Compra P2P': '#FF69B4',
        'Venda P2P': '#FF4500',
    }
    
    tabs_mg = st.tabs([str(n) for n in nomes])
    
    for idx, nome in enumerate(nomes):
        with tabs_mg[idx]:
            est = resultado.estados[nome]
            horas = np.arange(1440) / 60  # eixo X em horas
            
            fig_perfil = go.Figure()
            
            # Áreas empilhadas de uso
            fig_perfil.add_trace(go.Scatter(
                x=horas, y=est.uso_solar, mode='lines', name='Solar',
                line=dict(width=0), stackgroup='uso', fillcolor='rgba(255,215,0,0.6)'
            ))
            fig_perfil.add_trace(go.Scatter(
                x=horas, y=est.uso_bateria, mode='lines', name='Bateria',
                line=dict(width=0), stackgroup='uso', fillcolor='rgba(50,205,50,0.6)'
            ))
            fig_perfil.add_trace(go.Scatter(
                x=horas, y=est.uso_diesel, mode='lines', name='Diesel',
                line=dict(width=0), stackgroup='uso', fillcolor='rgba(169,169,169,0.6)'
            ))
            fig_perfil.add_trace(go.Scatter(
                x=horas, y=est.uso_biogas, mode='lines', name='Biogás',
                line=dict(width=0), stackgroup='uso', fillcolor='rgba(139,69,19,0.6)'
            ))
            fig_perfil.add_trace(go.Scatter(
                x=horas, y=est.uso_concessionaria, mode='lines', name='Concessionária',
                line=dict(width=0), stackgroup='uso', fillcolor='rgba(65,105,225,0.6)'
            ))
            fig_perfil.add_trace(go.Scatter(
                x=horas, y=est.energia_comprada, mode='lines', name='Compra P2P',
                line=dict(width=0), stackgroup='uso', fillcolor='rgba(255,105,180,0.6)'
            ))
            
            # Linha de carga total
            fig_perfil.add_trace(go.Scatter(
                x=horas, y=est.curva_carga, mode='lines', name='Demanda',
                line=dict(color='red', width=2, dash='dash')
            ))
            
            # Energia vendida (negativa)
            if est.energia_vendida.sum() > 0:
                fig_perfil.add_trace(go.Scatter(
                    x=horas, y=-est.energia_vendida, mode='lines', name='Venda P2P',
                    line=dict(color='#FF4500', width=1),
                    fill='tozeroy', fillcolor='rgba(255,69,0,0.3)'
                ))
            
            fig_perfil.update_layout(
                title=f"Perfil Energético — {nome}",
                xaxis_title="Hora do Dia",
                yaxis_title="Potência (kW)",
                xaxis=dict(tickmode='array', tickvals=list(range(0, 25, 2)),
                          ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)]),
                hovermode='x unified',
                height=450,
            )
            st.plotly_chart(fig_perfil, use_container_width=True, key=f"sim_perfil_{idx}")
            
            # Mini-métricas por MG
            c1m, c2m, c3m = st.columns(3)
            total_vendido = est.energia_vendida.sum() / 60  # kWh
            total_comprado = est.energia_comprada.sum() / 60
            c1m.metric("Energia Vendida", f"{total_vendido:,.1f} kWh")
            c2m.metric("Energia Comprada", f"{total_comprado:,.1f} kWh")
            saldo = resultado.receita_por_mg[nome] - resultado.gasto_compras_por_mg[nome]
            c3m.metric("Saldo P2P", f"R$ {saldo:,.2f}", 
                       "Superávit" if saldo >= 0 else "Déficit")
    
    st.divider()
    
    # --- FLUXO SANKEY ---
    st.subheader("🔄 Fluxo de Energia entre Microrredes")
    
    fluxos = {}
    for t in resultado.trades:
        key = (t.vendedor_nome, t.comprador_nome)
        fluxos[key] = fluxos.get(key, 0.0) + (t.energia_enviada_kw / 60)
    
    if fluxos:
        nomes_unicos = list(set([k[0] for k in fluxos] + [k[1] for k in fluxos]))
        idx_nome = {n: i for i, n in enumerate(nomes_unicos)}
        
        fig_sankey = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15, thickness=20,
                line=dict(color="black", width=0.5),
                label=nomes_unicos,
                color=["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"][:len(nomes_unicos)]
            ),
            link=dict(
                source=[idx_nome[k[0]] for k in fluxos],
                target=[idx_nome[k[1]] for k in fluxos],
                value=list(fluxos.values()),
            )
        )])
        fig_sankey.update_layout(height=400)
        st.plotly_chart(fig_sankey, use_container_width=True, key="sim_sankey")
    else:
        st.info("Não houve transações P2P neste cenário.")
    
    st.divider()
    
    # --- HISTÓRICO COMPLETO DE TRANSAÇÕES ---
    st.subheader("📜 Histórico de Transações")
    
    if resultado.trades:
        # Filtro
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            vendedores_unicos = sorted(set(t.vendedor_nome for t in resultado.trades))
            filtro_vendedor = st.multiselect("Filtrar por Vendedor:", vendedores_unicos, default=vendedores_unicos, key="filtro_vend")
        with col_f2:
            compradores_unicos = sorted(set(t.comprador_nome for t in resultado.trades))
            filtro_comprador = st.multiselect("Filtrar por Comprador:", compradores_unicos, default=compradores_unicos, key="filtro_comp")
        
        # Amostragem: a cada 15 min para não travar a UI
        amostra = st.selectbox("Amostragem:", ["A cada 1 min", "A cada 5 min", "A cada 15 min", "A cada 30 min", "A cada 60 min"], index=2)
        intervalo_map = {"A cada 1 min": 1, "A cada 5 min": 5, "A cada 15 min": 15, "A cada 30 min": 30, "A cada 60 min": 60}
        intervalo = intervalo_map[amostra]
        
        trades_filtrados = [
            t for t in resultado.trades 
            if t.vendedor_nome in filtro_vendedor 
            and t.comprador_nome in filtro_comprador
            and t.periodo % intervalo == 0
        ]
        
        if trades_filtrados:
            df_trades = pd.DataFrame([{
                'Hora': f"{t.periodo//60:02d}:{t.periodo%60:02d}",
                'Vendedor': t.vendedor_nome,
                'Comprador': t.comprador_nome,
                'Energia Recebida (kW)': f"{t.energia_kw:.2f}",
                'Energia Enviada (kW)': f"{t.energia_enviada_kw:.2f}",
                'Perda (kW)': f"{t.perda_kw:.2f}",
                'Distância (km)': f"{t.distancia_km:.2f}",
                'Gerador Acionado': t.gerador_acionado if t.gerador_acionado else '—',
                'Custo Combustível (R$)': f"R$ {t.custo_combustivel:.3f}" if t.custo_combustivel > 0 else '—',
                'Preço (R$/kWh)': f"R$ {t.preco_kwh:.3f}",
                'Total Pago (R$)': f"R$ {t.valor_total:.3f}",
            } for t in trades_filtrados])
            
            st.dataframe(df_trades, use_container_width=True, hide_index=True)
            st.caption(f"Mostrando {len(trades_filtrados)} transações ({amostra.lower()}) de {len(resultado.trades)} totais.")
        else:
            st.info("Nenhuma transação encontrada com os filtros selecionados.")
    else:
        st.info("Não houve transações P2P.")
    
    st.divider()
    
    # ============================================================
    # OTIMIZAÇÃO PÓS-DIA
    # ============================================================
    
    st.header("🔧 Otimização Pós-Dia")
    st.markdown("Desloca cargas flexíveis (prioridade 2 e 4) para horários mais baratos e otimiza o uso de geradores.")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        otimizar_heuristica = st.button("⚡ Otimização Heurística", type="secondary", use_container_width=True)
    with col_btn2:
        otimizar_milp = st.button("🧠 Otimização MILP", type="primary", use_container_width=True)
    
    otimizar = otimizar_heuristica or otimizar_milp
    
    if otimizar:
        from models.CRUD import Ler_Objeto
        from mercado.simulacao_simultanea import OtimizadorMILPPosDia
        
        mgs_frescas = [Ler_Objeto(Microrrede, mg.id) for mg in st.session_state['mgs_selecionadas']]
        
        status_otm = st.empty()
        status_otm.info("Iniciando otimização pós-dia... Isso pode demorar alguns minutos.")
        
        def callback_otm(msg):
            status_otm.info(msg)
            
        if otimizar_milp:
            otimizador = OtimizadorMILPPosDia(
                microrredes=mgs_frescas,
                config=st.session_state['config'],
                margem_venda=st.session_state['margem'],
                coef_perda_km=st.session_state['coef_perda'],
            )
        else:
            otimizador = OtimizadorPosDia(
                microrredes=mgs_frescas,
                config=st.session_state['config'],
                margem_venda=st.session_state['margem'],
                coef_perda_km=st.session_state['coef_perda'],
            )
        
        resultado_otm = otimizador.otimizar(resultado, callback=callback_otm)
        st.session_state['resultado_otimizacao'] = resultado_otm
        status_otm.success("Otimização concluída!")

    # Exibe resultados da otimização
    if 'resultado_otimizacao' in st.session_state:
        res_otm = st.session_state['resultado_otimizacao']
        res_orig = res_otm['original']
        res_otim = res_otm['otimizado']
        
        st.subheader("📊 Comparação: Antes vs Depois da Otimização")
        
        nomes_otm = list(res_orig.custo_total_por_mg.keys())
        
        # Métricas globais
        custo_antes = sum(res_orig.custo_total_por_mg.values())
        custo_depois = sum(res_otim.custo_total_por_mg.values())
        economia_otm = custo_antes - custo_depois
        
        c1o, c2o, c3o = st.columns(3)
        c1o.metric("Custo Antes", f"R$ {custo_antes:,.2f}")
        c2o.metric("Custo Depois", f"R$ {custo_depois:,.2f}")
        c3o.metric("Economia da Otimização", f"R$ {economia_otm:,.2f}",
                   f"{(economia_otm/custo_antes*100):.1f}%" if custo_antes > 0 else "0%")
        
        # Tabela comparativa
        df_comp = pd.DataFrame({
            "Microrrede": nomes_otm,
            "Antes (R$)": [f"R$ {res_orig.custo_total_por_mg[n]:,.2f}" for n in nomes_otm],
            "Depois (R$)": [f"R$ {res_otim.custo_total_por_mg[n]:,.2f}" for n in nomes_otm],
            "Economia (R$)": [f"R$ {res_orig.custo_total_por_mg[n] - res_otim.custo_total_por_mg[n]:,.2f}" for n in nomes_otm],
        })
        st.dataframe(df_comp, use_container_width=True, hide_index=True)
        
        # Gráfico comparativo
        df_comp_chart = pd.DataFrame({
            "Microrrede": nomes_otm,
            "Antes da Otimização (R$)": [res_orig.custo_total_por_mg[n] for n in nomes_otm],
            "Após Otimização (R$)": [res_otim.custo_total_por_mg[n] for n in nomes_otm],
        })
        fig_otm = px.bar(
            df_comp_chart, x="Microrrede",
            y=["Antes da Otimização (R$)", "Após Otimização (R$)"],
            barmode='group', text_auto='.2s',
            color_discrete_map={
                "Antes da Otimização (R$)": "#EF553B",
                "Após Otimização (R$)": "#00CC96"
            }
        )
        st.plotly_chart(fig_otm, use_container_width=True, key="otm_custos")
        
        # Cargas movidas
        if res_otm['cargas_movidas']:
            st.subheader("🔀 Cargas Deslizadas")
            df_movidas = pd.DataFrame(res_otm['cargas_movidas'])
            df_movidas.columns = ['Microrrede', 'Carga', 'Horário Original', 'Novo Horário', 'Duração (min)']
            st.dataframe(df_movidas, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma carga foi deslizada — os horários atuais já são ótimos.")
        
        st.divider()
        
        # --- GRÁFICOS DE GERAÇÃO/CONSUMO PÓS-OTIMIZAÇÃO ---
        st.subheader("📈 Perfil Energético Pós-Otimização (por Microrrede)")
        
        tabs_mg_otm = st.tabs([str(n) for n in nomes_otm])
        
        for idx, nome in enumerate(nomes_otm):
            with tabs_mg_otm[idx]:
                est = res_otim.estados[nome]
                horas = np.arange(1440) / 60  # eixo X em horas
                
                fig_perfil_otm = go.Figure()
                
                # Áreas empilhadas de uso
                fig_perfil_otm.add_trace(go.Scatter(
                    x=horas, y=est.uso_solar, mode='lines', name='Solar',
                    line=dict(width=0), stackgroup='uso', fillcolor='rgba(255,215,0,0.6)'
                ))
                fig_perfil_otm.add_trace(go.Scatter(
                    x=horas, y=est.uso_bateria, mode='lines', name='Bateria',
                    line=dict(width=0), stackgroup='uso', fillcolor='rgba(50,205,50,0.6)'
                ))
                fig_perfil_otm.add_trace(go.Scatter(
                    x=horas, y=est.uso_diesel, mode='lines', name='Diesel',
                    line=dict(width=0), stackgroup='uso', fillcolor='rgba(169,169,169,0.6)'
                ))
                fig_perfil_otm.add_trace(go.Scatter(
                    x=horas, y=est.uso_biogas, mode='lines', name='Biogás',
                    line=dict(width=0), stackgroup='uso', fillcolor='rgba(139,69,19,0.6)'
                ))
                fig_perfil_otm.add_trace(go.Scatter(
                    x=horas, y=est.uso_concessionaria, mode='lines', name='Concessionária',
                    line=dict(width=0), stackgroup='uso', fillcolor='rgba(65,105,225,0.6)'
                ))
                fig_perfil_otm.add_trace(go.Scatter(
                    x=horas, y=est.energia_comprada, mode='lines', name='Compra P2P',
                    line=dict(width=0), stackgroup='uso', fillcolor='rgba(255,105,180,0.6)'
                ))
                
                # Linha de carga total
                fig_perfil_otm.add_trace(go.Scatter(
                    x=horas, y=est.curva_carga, mode='lines', name='Demanda',
                    line=dict(color='red', width=2, dash='dash')
                ))
                
                # Energia vendida (negativa)
                if est.energia_vendida.sum() > 0:
                    fig_perfil_otm.add_trace(go.Scatter(
                        x=horas, y=-est.energia_vendida, mode='lines', name='Venda P2P',
                        line=dict(color='#FF4500', width=1),
                        fill='tozeroy', fillcolor='rgba(255,69,0,0.3)'
                    ))
                
                fig_perfil_otm.update_layout(
                    title=f"Perfil Energético Otimizado — {nome}",
                    xaxis_title="Hora do Dia",
                    yaxis_title="Potência (kW)",
                    xaxis=dict(tickmode='array', tickvals=list(range(0, 25, 2)),
                              ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)]),
                    hovermode='x unified',
                    height=450,
                )
                st.plotly_chart(fig_perfil_otm, use_container_width=True, key=f"otm_perfil_{idx}")
                
                # Mini-métricas por MG (Pós-otimização)
                c1o, c2o, c3o = st.columns(3)
                total_vendido_otm = est.energia_vendida.sum() / 60  # kWh
                total_comprado_otm = est.energia_comprada.sum() / 60
                c1o.metric("Energia Vendida", f"{total_vendido_otm:,.1f} kWh")
                c2o.metric("Energia Comprada", f"{total_comprado_otm:,.1f} kWh")
                saldo_otm = res_otim.receita_por_mg[nome] - res_otim.gasto_compras_por_mg[nome]
                c3o.metric("Saldo P2P", f"R$ {saldo_otm:,.2f}", 
                           "Superávit" if saldo_otm >= 0 else "Déficit")
        
        st.divider()
        
        # Histórico de trades pós-otimização
        if res_otim.trades:
            st.subheader("📜 Histórico de Transações (Pós-Otimização)")
            trades_otm_amostra = [t for t in res_otim.trades if t.periodo % 15 == 0]
            if trades_otm_amostra:
                df_trades_otm = pd.DataFrame([{
                    'Hora': f"{t.periodo//60:02d}:{t.periodo%60:02d}",
                    'Vendedor': t.vendedor_nome,
                    'Comprador': t.comprador_nome,
                    'Energia (kW)': f"{t.energia_kw:.2f}",
                    'Gerador': t.gerador_acionado if t.gerador_acionado else '—',
                    'Preço (R$/kWh)': f"R$ {t.preco_kwh:.3f}",
                    'Total (R$)': f"R$ {t.valor_total:.3f}",
                } for t in trades_otm_amostra])
                st.dataframe(df_trades_otm, use_container_width=True, hide_index=True)
