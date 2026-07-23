import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
import copy
from collections import defaultdict

from models.Microrrede import Microrrede
from models.CRUD import Ler, Ler_Objeto
import models.CRUD as _crud
from analises.config import ConfigAnalise
from mercado.simulacao_simultanea import SimuladorMercado
from Tools.Solar.gerar_curva_solar_sazonal import (
    gerar_curvas_sazonais,
    DATAS_ESTACOES,
    ICONES_ESTACOES,
)

st.set_page_config(page_title="Mercado Sazonal", layout="wide")
st.title("🌍 Mercado de Energia P2P — Análise Sazonal")
st.markdown(
    "Simulação do mercado P2P para cada estação do ano, "
    "comparando perfis solares e de carga das microrredes."
)

# ============================================================
# CONFIGURAÇÕES
# ============================================================

st.header("⚙️ Configurações")

todas_microrredes = Ler(Microrrede)

if not todas_microrredes:
    st.warning("Nenhuma microrrede cadastrada. Cadastre pelo menos 2 microrredes.")
    st.stop()

# Agrupar microrredes por estação
mgs_por_estacao = defaultdict(list)
for mg in todas_microrredes:
    est = mg.estacao or "Verão"
    mgs_por_estacao[est].append(mg)

estacoes_disponiveis = sorted(mgs_por_estacao.keys(), key=lambda e: ["Verão", "Outono", "Inverno", "Primavera"].index(e) if e in ["Verão", "Outono", "Inverno", "Primavera"] else 99)

st.subheader("🗓️ Seleção por Estação")
st.caption(
    "Cada microrrede tem uma estação associada no banco de dados. "
    "Selecione as estações que deseja simular e compare os resultados."
)

# Mostrar resumo de microrredes por estação
cols_resumo = st.columns(min(len(estacoes_disponiveis), 4))
for idx, est in enumerate(estacoes_disponiveis):
    icone = ICONES_ESTACOES.get(est, "📅")
    with cols_resumo[idx % 4]:
        st.metric(
            f"{icone} {est}",
            f"{len(mgs_por_estacao[est])} MGs",
        )

estacoes_selecionadas = st.multiselect(
    "Estações a Simular:",
    estacoes_disponiveis,
    default=estacoes_disponiveis,
    format_func=lambda e: f"{ICONES_ESTACOES.get(e, '📅')} {e} ({len(mgs_por_estacao[e])} MGs)",
)

if not estacoes_selecionadas:
    st.warning("Selecione pelo menos uma estação para simular.")
    st.stop()

# Verificar que todas as estações têm pelo menos 2 MGs
for est in estacoes_selecionadas:
    if len(mgs_por_estacao[est]) < 2:
        st.warning(f"A estação **{est}** tem apenas {len(mgs_por_estacao[est])} microrrede(s). É necessário pelo menos 2 para o mercado P2P.")
        st.stop()

st.divider()

col_cfg1, col_cfg2 = st.columns(2)

with col_cfg1:
    st.subheader("Fontes Habilitadas")
    solar_ligado = st.checkbox("☀️ Solar", value=True, key="saz_solar")
    bateria_ligada = st.checkbox("🔋 Bateria", value=True, key="saz_bat")
    diesel_ligado = st.checkbox("⛽ Diesel", value=True, key="saz_diesel")
    biogas_ligado = st.checkbox("🌿 Biogás", value=True, key="saz_biogas")

with col_cfg2:
    st.subheader("Parâmetros do Mercado")
    margem = st.slider("Margem de Lucro na Venda (%)", 0.0, 20.0, 5.0, 0.5, key="saz_margem") / 100.0
    coef_perda = st.slider("Fator de Perda (% / km)", 0.0, 1.0, 0.4, 0.1, key="saz_perda") / 100.0

config = ConfigAnalise(
    solar_ligado=solar_ligado,
    bateria_ligada=bateria_ligada,
    diesel_ligado=diesel_ligado,
    biogas_ligado=biogas_ligado,
)

st.divider()

# ============================================================
# CONFIGURAÇÃO DE CARGA SAZONAL (opcional)
# ============================================================

st.header("📊 Fator de Carga Sazonal (opcional)")
st.caption("Ajuste para refletir variações adicionais de demanda por estação.")

cols_fator = st.columns(len(estacoes_selecionadas))
fatores_carga = {}
for idx, est in enumerate(estacoes_selecionadas):
    with cols_fator[idx]:
        fatores_carga[est] = st.slider(
            f"{ICONES_ESTACOES.get(est, '📅')} {est}",
            -30.0, 30.0, 0.0, 1.0,
            key=f"fator_{est}",
        ) / 100.0

st.divider()

# ============================================================
# SIMULAÇÃO SAZONAL
# ============================================================

executar = st.button(
    "🚀 Simular Todas as Estações",
    type="primary",
    width='stretch',
)

if executar:
    resultados_sazonais = {}
    total_estacoes = len(estacoes_selecionadas)
    progress = st.progress(0, text="Preparando simulações...")

    # Usar no_autoflush para evitar que modificações temporárias
    # (curva_geracao, potência de carga) disparem escrita no banco
    with _crud.session.no_autoflush:
        for idx_est, estacao in enumerate(estacoes_selecionadas):
            progress.progress(
                idx_est / total_estacoes,
                text=f"Simulando {ICONES_ESTACOES.get(estacao, '📅')} {estacao}...",
            )

            # Pegar as MGs daquela estação diretamente do banco
            mgs_estacao = [Ler_Objeto(Microrrede, mg.id) for mg in mgs_por_estacao[estacao]]

            # Gerar curvas solares sazonais
            curvas_solares = {}
            for mg in mgs_estacao:
                if mg.solar and config.fonte_disponivel("Solar", mg):
                    lat = float(mg.coordenada_x) if mg.coordenada_x else -23.55
                    lon = float(mg.coordenada_y) if mg.coordenada_y else -46.63
                    curvas = gerar_curvas_sazonais(
                        latitude=lat,
                        longitude=lon,
                        potencia_kw=mg.solar.potencia,
                        eficiencia=0.8,
                        estacoes=[estacao],
                    )
                    if estacao in curvas:
                        mg.solar.curva_geracao = json.dumps(curvas[estacao].tolist())
                        curvas_solares[mg.id] = curvas[estacao]

            # Aplicar fator de carga sazonal
            fator = fatores_carga.get(estacao, 0.0)
            if fator != 0.0:
                for mg in mgs_estacao:
                    if mg.carga:
                        for carga_fixa in mg.carga.cargaFixa:
                            carga_fixa.potencia = carga_fixa.potencia * (1 + fator)

            # Simular mercado P2P
            simulador = SimuladorMercado(
                microrredes=mgs_estacao,
                config=config,
                margem_venda=margem,
                coef_perda_km=coef_perda,
            )
            resultado = simulador.simular()
            resultados_sazonais[estacao] = {
                "resultado": resultado,
                "curvas_solares": curvas_solares,
                "mgs": mgs_estacao,
            }

    # Descartar modificações temporárias para não persistir no banco
    _crud.session.rollback()

    progress.progress(1.0, text="Simulações concluídas!")
    st.session_state["resultados_sazonais"] = resultados_sazonais
    st.session_state["estacoes_simuladas"] = estacoes_selecionadas
    st.session_state["mgs_por_estacao"] = dict(mgs_por_estacao)
    st.session_state["fatores_carga"] = fatores_carga

# ============================================================
# RESULTADOS POR ESTAÇÃO
# ============================================================

if "resultados_sazonais" in st.session_state:
    resultados_sazonais = st.session_state["resultados_sazonais"]
    estacoes_simuladas = st.session_state["estacoes_simuladas"]

    st.divider()
    st.header("📊 Resultados por Estação")

    cores_fonte = {
        "Solar": "rgba(255,215,0,0.6)",
        "Bateria": "rgba(50,205,50,0.6)",
        "Diesel": "rgba(169,169,169,0.6)",
        "Biogás": "rgba(139,69,19,0.6)",
        "Concessionária": "rgba(65,105,225,0.6)",
        "Compra P2P": "rgba(255,105,180,0.6)",
        "Venda P2P": "rgba(255,69,0,0.3)",
    }

    tabs_estacoes = st.tabs(
        [f"{ICONES_ESTACOES.get(e, '📅')} {e}" for e in estacoes_simuladas]
    )

    for idx_est, estacao in enumerate(estacoes_simuladas):
        with tabs_estacoes[idx_est]:
            resultado = resultados_sazonais[estacao]["resultado"]
            nomes = list(resultado.custo_isolado_por_mg.keys())

            # --- MÉTRICAS GLOBAIS ---
            c1, c2, c3, c4 = st.columns(4)

            custo_iso_total = sum(resultado.custo_isolado_por_mg.values())
            economia_pct = (
                (resultado.economia_total / custo_iso_total * 100)
                if custo_iso_total > 0
                else 0
            )

            c1.metric(
                "💰 Economia Total",
                f"R$ {resultado.economia_total:,.2f}",
                f"{economia_pct:.1f}%",
            )
            c2.metric(
                "⚡ Volume Negociado",
                f"{resultado.volume_total_kwh:,.1f} kWh",
            )
            c3.metric(
                "📉 Perdas por Distância",
                f"{resultado.perdas_totais_kwh:,.2f} kWh",
            )
            c4.metric("🔄 Nº Transações", f"{resultado.num_transacoes:,}")

            st.divider()

            # --- CUSTOS COMPARATIVOS ---
            st.subheader(f"💰 Custos — {ICONES_ESTACOES.get(estacao, '📅')} {estacao}")

            df_custos = pd.DataFrame(
                {
                    "Microrrede": nomes,
                    "Operação Isolada (R$)": [
                        resultado.custo_isolado_por_mg[n] for n in nomes
                    ],
                    "Com Mercado P2P (R$)": [
                        resultado.custo_total_por_mg[n] for n in nomes
                    ],
                }
            )

            fig_custos = px.bar(
                df_custos,
                x="Microrrede",
                y=["Operação Isolada (R$)", "Com Mercado P2P (R$)"],
                barmode="group",
                text_auto=".2s",
                color_discrete_map={
                    "Operação Isolada (R$)": "#EF553B",
                    "Com Mercado P2P (R$)": "#00CC96",
                },
            )
            fig_custos.update_layout(yaxis_title="Custo Diário (R$)")
            st.plotly_chart(
                fig_custos,
                width='stretch',
                key=f"saz_custos_{estacao}",
            )

            st.divider()

            # --- BALANÇO FINANCEIRO ---
            st.subheader("📋 Balanço Financeiro por Microrrede")
            df_balanco = pd.DataFrame(
                {
                    "Microrrede": nomes,
                    "Custo Isolado (R$)": [
                        f"R$ {resultado.custo_isolado_por_mg[n]:,.2f}" for n in nomes
                    ],
                    "Custo com Mercado (R$)": [
                        f"R$ {resultado.custo_total_por_mg[n]:,.2f}" for n in nomes
                    ],
                    "Vendas (R$)": [
                        f"R$ {resultado.receita_por_mg[n]:,.2f}" for n in nomes
                    ],
                    "Compras (R$)": [
                        f"R$ {resultado.gasto_compras_por_mg[n]:,.2f}" for n in nomes
                    ],
                    "Economia (R$)": [
                        f"R$ {resultado.economia_por_mg[n]:,.2f}" for n in nomes
                    ],
                }
            )
            st.dataframe(df_balanco, width='stretch', hide_index=True)

            st.divider()

            # --- FLUXO SANKEY ---
            st.subheader(f"🔄 Fluxo de Energia P2P — {ICONES_ESTACOES.get(estacao, '📅')} {estacao}")
            
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
                st.plotly_chart(fig_sankey, width='stretch', key=f"saz_sankey_{estacao}")
            else:
                st.info("Não houve transações P2P neste cenário.")

            st.divider()

            # --- PERFIL ENERGÉTICO POR MG ---
            st.subheader(f"📈 Perfil Energético — {ICONES_ESTACOES.get(estacao, '📅')} {estacao}")

            tabs_mg = st.tabs([str(n) for n in nomes])

            for idx_mg, nome in enumerate(nomes):
                with tabs_mg[idx_mg]:
                    est = resultado.estados[nome]
                    horas = np.arange(1440) / 60

                    fig_perfil = go.Figure()

                    # Áreas empilhadas de uso
                    fig_perfil.add_trace(
                        go.Scatter(
                            x=horas,
                            y=est.uso_solar,
                            mode="lines",
                            name="Solar",
                            line=dict(width=0),
                            stackgroup="uso",
                            fillcolor="rgba(255,215,0,0.6)",
                        )
                    )
                    fig_perfil.add_trace(
                        go.Scatter(
                            x=horas,
                            y=est.uso_bateria,
                            mode="lines",
                            name="Bateria",
                            line=dict(width=0),
                            stackgroup="uso",
                            fillcolor="rgba(50,205,50,0.6)",
                        )
                    )
                    fig_perfil.add_trace(
                        go.Scatter(
                            x=horas,
                            y=est.uso_diesel,
                            mode="lines",
                            name="Diesel",
                            line=dict(width=0),
                            stackgroup="uso",
                            fillcolor="rgba(169,169,169,0.6)",
                        )
                    )
                    fig_perfil.add_trace(
                        go.Scatter(
                            x=horas,
                            y=est.uso_biogas,
                            mode="lines",
                            name="Biogás",
                            line=dict(width=0),
                            stackgroup="uso",
                            fillcolor="rgba(139,69,19,0.6)",
                        )
                    )
                    fig_perfil.add_trace(
                        go.Scatter(
                            x=horas,
                            y=est.uso_concessionaria,
                            mode="lines",
                            name="Concessionária",
                            line=dict(width=0),
                            stackgroup="uso",
                            fillcolor="rgba(65,105,225,0.6)",
                        )
                    )
                    fig_perfil.add_trace(
                        go.Scatter(
                            x=horas,
                            y=est.energia_comprada,
                            mode="lines",
                            name="Compra P2P",
                            line=dict(width=0),
                            stackgroup="uso",
                            fillcolor="rgba(255,105,180,0.6)",
                        )
                    )

                    # Linha de demanda
                    fig_perfil.add_trace(
                        go.Scatter(
                            x=horas,
                            y=est.curva_carga,
                            mode="lines",
                            name="Demanda",
                            line=dict(color="red", width=2, dash="dash"),
                        )
                    )

                    # Energia vendida (negativa)
                    if est.energia_vendida.sum() > 0:
                        fig_perfil.add_trace(
                            go.Scatter(
                                x=horas,
                                y=-est.energia_vendida,
                                mode="lines",
                                name="Venda P2P",
                                line=dict(color="#FF4500", width=1),
                                fill="tozeroy",
                                fillcolor="rgba(255,69,0,0.3)",
                            )
                        )

                    fig_perfil.update_layout(
                        title=f"Perfil Energético — {nome} ({estacao})",
                        xaxis_title="Hora do Dia",
                        yaxis_title="Potência (kW)",
                        xaxis=dict(
                            tickmode="array",
                            tickvals=list(range(0, 25, 2)),
                            ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
                        ),
                        hovermode="x unified",
                        height=450,
                    )
                    st.plotly_chart(
                        fig_perfil,
                        width='stretch',
                        key=f"saz_perfil_{estacao}_{idx_mg}",
                    )

                    # --- NÍVEIS DE TANQUE E BATERIA ---
                    st.markdown("##### 🛢️ Níveis de Tanque e Bateria")

                    fig_niveis = go.Figure()

                    # Tanque Diesel
                    if est.hist_nivel_diesel.sum() > 0:
                        fig_niveis.add_trace(
                            go.Scatter(
                                x=horas,
                                y=est.hist_nivel_diesel,
                                mode="lines",
                                name="⛽ Diesel (L)",
                                line=dict(color="#A9A9A9", width=2),
                            )
                        )

                    # Tanque Biogás
                    if est.hist_nivel_biogas.sum() > 0:
                        fig_niveis.add_trace(
                            go.Scatter(
                                x=horas,
                                y=est.hist_nivel_biogas,
                                mode="lines",
                                name="🌿 Biogás (m³)",
                                line=dict(color="#8B4513", width=2),
                            )
                        )

                    # Nível de Bateria
                    if est.hist_nivel_bateria.sum() > 0:
                        fig_niveis.add_trace(
                            go.Scatter(
                                x=horas,
                                y=est.hist_nivel_bateria,
                                mode="lines",
                                name="🔋 Bateria (kWh)",
                                line=dict(color="#32CD32", width=2),
                            )
                        )

                    fig_niveis.update_layout(
                        title=f"Níveis de Armazenamento — {nome} ({estacao})",
                        xaxis_title="Hora do Dia",
                        yaxis_title="Nível",
                        xaxis=dict(
                            tickmode="array",
                            tickvals=list(range(0, 25, 2)),
                            ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
                        ),
                        hovermode="x unified",
                        height=350,
                    )
                    st.plotly_chart(
                        fig_niveis,
                        width='stretch',
                        key=f"saz_niveis_{estacao}_{idx_mg}",
                    )

                    # Mini-métricas por MG
                    c1m, c2m, c3m, c4m, c5m = st.columns(5)
                    total_vendido = est.energia_vendida.sum() / 60
                    total_comprado = est.energia_comprada.sum() / 60
                    c1m.metric("Energia Vendida", f"{total_vendido:,.1f} kWh")
                    c2m.metric("Energia Comprada", f"{total_comprado:,.1f} kWh")
                    saldo = (
                        resultado.receita_por_mg[nome]
                        - resultado.gasto_compras_por_mg[nome]
                    )
                    c3m.metric(
                        "Saldo P2P",
                        f"R$ {saldo:,.2f}",
                        "Superávit" if saldo >= 0 else "Déficit",
                    )
                    c4m.metric(
                        "⛽ Diesel Final",
                        f"{est.hist_nivel_diesel[-1]:,.2f} L",
                    )
                    c5m.metric(
                        "🔋 Bateria Final",
                        f"{est.hist_nivel_bateria[-1]:,.2f} kWh",
                    )

    # ============================================================
    # COMPARAÇÃO ENTRE ESTAÇÕES
    # ============================================================

    st.divider()
    st.header("📊 Comparação entre Estações")

    if len(estacoes_simuladas) >= 2:
        # --- TABELA COMPARATIVA ---
        st.subheader("📋 Resumo Comparativo")

        dados_comp = []
        for estacao in estacoes_simuladas:
            res = resultados_sazonais[estacao]["resultado"]
            custo_iso = sum(res.custo_isolado_por_mg.values())
            custo_p2p = sum(res.custo_total_por_mg.values())
            dados_comp.append(
                {
                    "Estação": f"{ICONES_ESTACOES.get(estacao, '📅')} {estacao}",
                    "Custo Isolado (R$)": custo_iso,
                    "Custo com Mercado (R$)": custo_p2p,
                    "Economia (R$)": res.economia_total,
                    "Economia (%)": (
                        (res.economia_total / custo_iso * 100) if custo_iso > 0 else 0
                    ),
                    "Volume P2P (kWh)": res.volume_total_kwh,
                    "Nº Transações": res.num_transacoes,
                }
            )

        df_comp = pd.DataFrame(dados_comp)
        st.dataframe(
            df_comp.style.format(
                {
                    "Custo Isolado (R$)": "R$ {:,.2f}",
                    "Custo com Mercado (R$)": "R$ {:,.2f}",
                    "Economia (R$)": "R$ {:,.2f}",
                    "Economia (%)": "{:.1f}%",
                    "Volume P2P (kWh)": "{:,.1f}",
                    "Nº Transações": "{:,}",
                }
            ),
            width='stretch',
            hide_index=True,
        )

        st.divider()

        # --- GRÁFICO CUSTOS POR ESTAÇÃO ---
        st.subheader("💰 Custos por Estação")

        fig_comp_custos = go.Figure()
        nomes_est = [f"{ICONES_ESTACOES.get(e, '📅')} {e}" for e in estacoes_simuladas]
        custos_iso = [
            sum(resultados_sazonais[e]["resultado"].custo_isolado_por_mg.values())
            for e in estacoes_simuladas
        ]
        custos_p2p = [
            sum(resultados_sazonais[e]["resultado"].custo_total_por_mg.values())
            for e in estacoes_simuladas
        ]
        economias = [
            resultados_sazonais[e]["resultado"].economia_total
            for e in estacoes_simuladas
        ]

        fig_comp_custos.add_trace(
            go.Bar(
                name="Operação Isolada",
                x=nomes_est,
                y=custos_iso,
                marker_color="#EF553B",
                text=[f"R$ {v:,.2f}" for v in custos_iso],
                textposition="auto",
            )
        )
        fig_comp_custos.add_trace(
            go.Bar(
                name="Com Mercado P2P",
                x=nomes_est,
                y=custos_p2p,
                marker_color="#00CC96",
                text=[f"R$ {v:,.2f}" for v in custos_p2p],
                textposition="auto",
            )
        )
        fig_comp_custos.add_trace(
            go.Bar(
                name="Economia",
                x=nomes_est,
                y=economias,
                marker_color="#636EFA",
                text=[f"R$ {v:,.2f}" for v in economias],
                textposition="auto",
            )
        )
        fig_comp_custos.update_layout(
            barmode="group",
            yaxis_title="Valor (R$)",
            height=450,
        )
        st.plotly_chart(
            fig_comp_custos,
            width='stretch',
            key="saz_comp_custos",
        )

        st.divider()

        # --- VOLUME P2P POR ESTAÇÃO ---
        st.subheader("🔄 Volume de Transações P2P por Estação")

        volumes = [
            resultados_sazonais[e]["resultado"].volume_total_kwh
            for e in estacoes_simuladas
        ]
        perdas = [
            resultados_sazonais[e]["resultado"].perdas_totais_kwh
            for e in estacoes_simuladas
        ]
        transacoes = [
            resultados_sazonais[e]["resultado"].num_transacoes
            for e in estacoes_simuladas
        ]

        fig_volume = go.Figure()
        fig_volume.add_trace(
            go.Bar(
                name="Volume (kWh)",
                x=nomes_est,
                y=volumes,
                marker_color="#AB63FA",
                text=[f"{v:,.1f}" for v in volumes],
                textposition="auto",
            )
        )
        fig_volume.add_trace(
            go.Bar(
                name="Perdas (kWh)",
                x=nomes_est,
                y=perdas,
                marker_color="#FFA15A",
                text=[f"{v:,.2f}" for v in perdas],
                textposition="auto",
            )
        )
        fig_volume.update_layout(
            barmode="group",
            yaxis_title="Energia (kWh)",
            height=400,
        )
        st.plotly_chart(
            fig_volume,
            width='stretch',
            key="saz_comp_volume",
        )

        # Métricas de transações
        cols_trans = st.columns(len(estacoes_simuladas))
        for idx_e, estacao in enumerate(estacoes_simuladas):
            cols_trans[idx_e].metric(
                f"{ICONES_ESTACOES.get(estacao, '📅')} Transações",
                f"{transacoes[idx_e]:,}",
            )

        st.divider()

        # ============================================================
        # COMPARAÇÃO MG-A-MG ENTRE ESTAÇÕES (MESMA MG EM ESTAÇÕES DIFERENTES)
        # ============================================================

        st.header("🔍 Comparação por Microrrede entre Estações")
        st.caption(
            "Compare a mesma microrrede (por nome base) em estações diferentes. "
            "Microrredes com o mesmo nome em estações distintas são agrupadas."
        )

        # Agrupar por nome base (sem a estação)
        nomes_base = defaultdict(dict)
        for estacao in estacoes_simuladas:
            res = resultados_sazonais[estacao]["resultado"]
            mgs_est = resultados_sazonais[estacao].get("mgs", [])
            for mg in mgs_est:
                nome_base = mg.nome  # O nome base da MG (sem estação)
                mg_display = f"Microrrede: {mg.nome}"
                if mg_display in res.custo_isolado_por_mg:
                    nomes_base[nome_base][estacao] = {
                        "display": mg_display,
                        "custo_isolado": res.custo_isolado_por_mg[mg_display],
                        "custo_p2p": res.custo_total_por_mg[mg_display],
                        "receita": res.receita_por_mg[mg_display],
                        "gasto_compras": res.gasto_compras_por_mg[mg_display],
                        "economia": res.economia_por_mg[mg_display],
                        "estado": res.estados[mg_display],
                        "curva_solar": resultados_sazonais[estacao].get("curvas_solares", {}).get(mg.id, np.zeros(1440)),
                    }

        # Filtrar nomes que aparecem em mais de uma estação
        nomes_comparaveis = {n: v for n, v in nomes_base.items() if len(v) >= 2}

        if nomes_comparaveis:
            tabs_comp_mg = st.tabs([f"📊 {n}" for n in nomes_comparaveis.keys()])

            cores_estacao = {
                "Verão": "#FF6B35",
                "Outono": "#D4A574",
                "Inverno": "#4A90D9",
                "Primavera": "#50C878",
            }

            for idx_tab, (nome_base, dados_estacoes) in enumerate(nomes_comparaveis.items()):
                with tabs_comp_mg[idx_tab]:
                    st.subheader(f"Comparação Sazonal — {nome_base}")

                    estacoes_desta_mg = sorted(
                        dados_estacoes.keys(),
                        key=lambda e: ["Verão", "Outono", "Inverno", "Primavera"].index(e) if e in ["Verão", "Outono", "Inverno", "Primavera"] else 99,
                    )

                    # --- TABELA DE CUSTOS ---
                    st.markdown("#### 💰 Custos por Estação")
                    dados_tabela = []
                    for est in estacoes_desta_mg:
                        d = dados_estacoes[est]
                        dados_tabela.append({
                            "Estação": f"{ICONES_ESTACOES.get(est, '📅')} {est}",
                            "Custo Isolado (R$)": d["custo_isolado"],
                            "Custo c/ Mercado (R$)": d["custo_p2p"],
                            "Receita Vendas (R$)": d["receita"],
                            "Gasto Compras (R$)": d["gasto_compras"],
                            "Economia (R$)": d["economia"],
                        })
                    df_mg_comp = pd.DataFrame(dados_tabela)
                    st.dataframe(
                        df_mg_comp.style.format({
                            "Custo Isolado (R$)": "R$ {:,.2f}",
                            "Custo c/ Mercado (R$)": "R$ {:,.2f}",
                            "Receita Vendas (R$)": "R$ {:,.2f}",
                            "Gasto Compras (R$)": "R$ {:,.2f}",
                            "Economia (R$)": "R$ {:,.2f}",
                        }),
                        width='stretch',
                        hide_index=True,
                    )

                    # --- GRÁFICO COMPARATIVO DE CUSTOS ---
                    fig_mg_custos = go.Figure()
                    nomes_est_mg = [f"{ICONES_ESTACOES.get(e, '📅')} {e}" for e in estacoes_desta_mg]

                    fig_mg_custos.add_trace(go.Bar(
                        name="Custo Isolado",
                        x=nomes_est_mg,
                        y=[dados_estacoes[e]["custo_isolado"] for e in estacoes_desta_mg],
                        marker_color="#EF553B",
                        text=[f"R$ {dados_estacoes[e]['custo_isolado']:,.2f}" for e in estacoes_desta_mg],
                        textposition="auto",
                    ))
                    fig_mg_custos.add_trace(go.Bar(
                        name="Custo c/ Mercado",
                        x=nomes_est_mg,
                        y=[dados_estacoes[e]["custo_p2p"] for e in estacoes_desta_mg],
                        marker_color="#00CC96",
                        text=[f"R$ {dados_estacoes[e]['custo_p2p']:,.2f}" for e in estacoes_desta_mg],
                        textposition="auto",
                    ))
                    fig_mg_custos.update_layout(
                        title=f"Custos — {nome_base}",
                        barmode="group",
                        yaxis_title="Valor (R$)",
                        height=400,
                    )
                    st.plotly_chart(fig_mg_custos, width='stretch', key=f"comp_mg_custos_{idx_tab}")

                    st.divider()

                    # --- PERFIS ENERGÉTICOS SOBREPOSTOS ---
                    st.markdown("#### 📈 Perfis de Demanda Sobrepostos")

                    horas = np.arange(1440) / 60
                    fig_demanda = go.Figure()

                    for est in estacoes_desta_mg:
                        estado = dados_estacoes[est]["estado"]
                        fig_demanda.add_trace(
                            go.Scatter(
                                x=horas,
                                y=estado.curva_carga,
                                mode="lines",
                                name=f"{ICONES_ESTACOES.get(est, '📅')} {est}",
                                line=dict(
                                    color=cores_estacao.get(est, "#888"),
                                    width=2,
                                ),
                            )
                        )

                    fig_demanda.update_layout(
                        title=f"Curva de Carga — {nome_base} (por Estação)",
                        xaxis_title="Hora do Dia",
                        yaxis_title="Potência (kW)",
                        xaxis=dict(
                            tickmode="array",
                            tickvals=list(range(0, 25, 2)),
                            ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
                        ),
                        hovermode="x unified",
                        height=400,
                    )
                    st.plotly_chart(fig_demanda, width='stretch', key=f"comp_mg_demanda_{idx_tab}")

                    # --- CURVAS SOLARES SOBREPOSTAS ---
                    tem_solar = any(
                        dados_estacoes[e]["curva_solar"].sum() > 0
                        for e in estacoes_desta_mg
                    )
                    if tem_solar:
                        st.markdown("#### ☀️ Geração Solar Sobreposta")
                        fig_solar = go.Figure()

                        for est in estacoes_desta_mg:
                            curva = dados_estacoes[est]["curva_solar"]
                            fig_solar.add_trace(
                                go.Scatter(
                                    x=horas,
                                    y=curva,
                                    mode="lines",
                                    name=f"{ICONES_ESTACOES.get(est, '📅')} {est}",
                                    line=dict(
                                        color=cores_estacao.get(est, "#888"),
                                        width=2,
                                    ),
                                )
                            )

                        fig_solar.update_layout(
                            title=f"Geração Solar — {nome_base} (por Estação)",
                            xaxis_title="Hora do Dia",
                            yaxis_title="Potência (kW)",
                            xaxis=dict(
                                tickmode="array",
                                tickvals=list(range(0, 25, 2)),
                                ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
                            ),
                            hovermode="x unified",
                            height=400,
                        )
                        st.plotly_chart(fig_solar, width='stretch', key=f"comp_mg_solar_{idx_tab}")

                        # --- TOTAL DE GERAÇÃO SOLAR ---
                        st.markdown("#### ☀️ Total de Geração Solar Diária")
                        fig_solar_total = go.Figure()
                        totais_solar = []
                        for est in estacoes_desta_mg:
                            curva = dados_estacoes[est]["curva_solar"]
                            total_kwh = curva.sum() / 60
                            totais_solar.append(total_kwh)
                            
                        fig_solar_total.add_trace(go.Bar(
                            name="Energia Solar Diária",
                            x=[f"{ICONES_ESTACOES.get(e, '📅')} {e}" for e in estacoes_desta_mg],
                            y=totais_solar,
                            marker_color="#FFD700",
                            text=[f"{v:,.1f} kWh" for v in totais_solar],
                            textposition="auto",
                        ))
                        fig_solar_total.update_layout(
                            title=f"Energia Solar Total Diária — {nome_base} (por Estação)",
                            yaxis_title="Energia (kWh/dia)",
                            height=400,
                        )
                        st.plotly_chart(fig_solar_total, width='stretch', key=f"comp_mg_solar_tot_{idx_tab}")

                    # --- PERFIL ENERGÉTICO (MIX) LADO A LADO ---
                    st.markdown("#### 📊 Perfil Energético (Mix) por Estação")
                    cols_mix = st.columns(2)
                    
                    for i, est in enumerate(estacoes_desta_mg):
                        estado = dados_estacoes[est]["estado"]
                        fig_mix = go.Figure()

                        fig_mix.add_trace(go.Scatter(x=horas, y=estado.uso_solar, mode="lines", name="Solar", line=dict(width=0), stackgroup="uso", fillcolor="rgba(255,215,0,0.6)"))
                        fig_mix.add_trace(go.Scatter(x=horas, y=estado.uso_bateria, mode="lines", name="Bateria", line=dict(width=0), stackgroup="uso", fillcolor="rgba(50,205,50,0.6)"))
                        fig_mix.add_trace(go.Scatter(x=horas, y=estado.uso_diesel, mode="lines", name="Diesel", line=dict(width=0), stackgroup="uso", fillcolor="rgba(169,169,169,0.6)"))
                        fig_mix.add_trace(go.Scatter(x=horas, y=estado.uso_biogas, mode="lines", name="Biogás", line=dict(width=0), stackgroup="uso", fillcolor="rgba(139,69,19,0.6)"))
                        fig_mix.add_trace(go.Scatter(x=horas, y=estado.uso_concessionaria, mode="lines", name="Grid", line=dict(width=0), stackgroup="uso", fillcolor="rgba(65,105,225,0.6)"))
                        fig_mix.add_trace(go.Scatter(x=horas, y=estado.energia_comprada, mode="lines", name="Compra P2P", line=dict(width=0), stackgroup="uso", fillcolor="rgba(255,105,180,0.6)"))

                        fig_mix.add_trace(go.Scatter(x=horas, y=estado.curva_carga, mode="lines", name="Demanda", line=dict(color="red", width=2, dash="dash")))

                        if estado.energia_vendida.sum() > 0:
                            fig_mix.add_trace(go.Scatter(x=horas, y=-estado.energia_vendida, mode="lines", name="Venda P2P", line=dict(color="#FF4500", width=1), fill="tozeroy", fillcolor="rgba(255,69,0,0.3)"))

                        fig_mix.update_layout(
                            title=f"{ICONES_ESTACOES.get(est, '📅')} {est}",
                            xaxis_title="Hora",
                            yaxis_title="kW",
                            xaxis=dict(tickmode="array", tickvals=list(range(0, 25, 4)), ticktext=[f"{h:02d}:00" for h in range(0, 25, 4)]),
                            hovermode="x unified",
                            height=350,
                            margin=dict(l=20, r=20, t=40, b=20),
                            showlegend=False
                        )
                        
                        with cols_mix[i % 2]:
                            st.plotly_chart(fig_mix, width='stretch', key=f"comp_mg_mix_{idx_tab}_{est}")

                    # --- MÉTRICAS COMPARATIVAS ---
                    st.markdown("#### 📊 Métricas Comparativas")
                    cols_met = st.columns(len(estacoes_desta_mg))
                    for idx_e, est in enumerate(estacoes_desta_mg):
                        d = dados_estacoes[est]
                        estado = d["estado"]
                        with cols_met[idx_e]:
                            st.markdown(f"**{ICONES_ESTACOES.get(est, '📅')} {est}**")
                            st.metric("Economia", f"R$ {d['economia']:,.2f}")
                            vendido = estado.energia_vendida.sum() / 60
                            comprado = estado.energia_comprada.sum() / 60
                            st.metric("Energia Vendida", f"{vendido:,.1f} kWh")
                            st.metric("Energia Comprada", f"{comprado:,.1f} kWh")
                            saldo = d["receita"] - d["gasto_compras"]
                            st.metric(
                                "Saldo P2P",
                                f"R$ {saldo:,.2f}",
                                "Superávit" if saldo >= 0 else "Déficit",
                            )

        else:
            st.info(
                "Nenhuma microrrede com o mesmo nome aparece em mais de uma estação. "
                "Para comparar, cadastre microrredes com o **mesmo nome** em estações diferentes."
            )

    else:
        st.info("Selecione pelo menos 2 estações para ver a comparação.")

    # ============================================================
    # OTIMIZAÇÃO PÓS-DIA (POR ESTAÇÃO)
    # ============================================================

    st.divider()
    st.header("🔧 Otimização Pós-Dia")
    st.markdown(
        "Desloca cargas flexíveis (prioridade 2 e 3) para horários mais baratos "
        "e otimiza o uso de geradores. A otimização é aplicada **por estação**."
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        otimizar_heuristica = st.button(
            "⚡ Otimização Heurística", type="secondary",
            width='stretch', key="saz_otm_heur",
        )
    with col_btn2:
        otimizar_milp = st.button(
            "🧠 Otimização MILP", type="primary",
            width='stretch', key="saz_otm_milp",
        )

    otimizar = otimizar_heuristica or otimizar_milp

    if otimizar:
        from mercado.simulacao_simultanea import OtimizadorPosDia, OtimizadorMILPPosDia

        resultados_otm_sazonais = {}
        status_otm = st.empty()

        for idx_est, estacao in enumerate(estacoes_simuladas):
            status_otm.info(
                f"Otimizando {ICONES_ESTACOES.get(estacao, '📅')} {estacao} "
                f"({idx_est + 1}/{len(estacoes_simuladas)})..."
            )

            resultado_est = resultados_sazonais[estacao]["resultado"]

            # Recarregar MGs frescas para otimização
            mgs_por_est = st.session_state.get("mgs_por_estacao", {})
            mgs_da_estacao = mgs_por_est.get(estacao, [])

            with _crud.session.no_autoflush:
                mgs_frescas = [Ler_Objeto(Microrrede, mg.id) for mg in mgs_da_estacao]

            _crud.session.rollback()

            def callback_otm(msg):
                status_otm.info(f"{ICONES_ESTACOES.get(estacao, '📅')} {estacao}: {msg}")

            if otimizar_milp:
                otimizador = OtimizadorMILPPosDia(
                    microrredes=mgs_frescas,
                    config=config,
                    margem_venda=margem,
                    coef_perda_km=coef_perda,
                )
            else:
                otimizador = OtimizadorPosDia(
                    microrredes=mgs_frescas,
                    config=config,
                    margem_venda=margem,
                    coef_perda_km=coef_perda,
                )

            resultado_otm = otimizador.otimizar(resultado_est, callback=callback_otm)
            resultados_otm_sazonais[estacao] = resultado_otm

        st.session_state["resultados_otm_sazonais"] = resultados_otm_sazonais
        status_otm.success("Otimização concluída para todas as estações!")

    # Exibe resultados da otimização
    if "resultados_otm_sazonais" in st.session_state:
        resultados_otm_sazonais = st.session_state["resultados_otm_sazonais"]

        st.subheader("📊 Resultados da Otimização por Estação")

        # --- RESUMO GLOBAL DA OTIMIZAÇÃO ---
        dados_resumo_otm = []
        for estacao in estacoes_simuladas:
            if estacao not in resultados_otm_sazonais:
                continue
            res_otm = resultados_otm_sazonais[estacao]
            res_orig = res_otm["original"]
            res_otim = res_otm["otimizado"]
            custo_antes = sum(res_orig.custo_total_por_mg.values())
            custo_depois = sum(res_otim.custo_total_por_mg.values())
            economia_otm = custo_antes - custo_depois
            dados_resumo_otm.append({
                "Estação": f"{ICONES_ESTACOES.get(estacao, '📅')} {estacao}",
                "Custo Antes (R$)": custo_antes,
                "Custo Depois (R$)": custo_depois,
                "Economia Otm (R$)": economia_otm,
                "Economia Otm (%)": (economia_otm / custo_antes * 100) if custo_antes > 0 else 0,
                "Cargas Movidas": len(res_otm.get("cargas_movidas", [])),
            })

        if dados_resumo_otm:
            df_resumo_otm = pd.DataFrame(dados_resumo_otm)
            st.dataframe(
                df_resumo_otm.style.format({
                    "Custo Antes (R$)": "R$ {:,.2f}",
                    "Custo Depois (R$)": "R$ {:,.2f}",
                    "Economia Otm (R$)": "R$ {:,.2f}",
                    "Economia Otm (%)": "{:.1f}%",
                    "Cargas Movidas": "{:,}",
                }),
                width='stretch',
                hide_index=True,
            )

        st.divider()

        # --- DETALHES POR ESTAÇÃO ---
        tabs_otm = st.tabs(
            [f"{ICONES_ESTACOES.get(e, '📅')} {e}" for e in estacoes_simuladas if e in resultados_otm_sazonais]
        )

        for idx_est, estacao in enumerate([e for e in estacoes_simuladas if e in resultados_otm_sazonais]):
            with tabs_otm[idx_est]:
                res_otm = resultados_otm_sazonais[estacao]
                res_orig = res_otm["original"]
                res_otim = res_otm["otimizado"]
                nomes_otm = list(res_orig.custo_total_por_mg.keys())

                # Métricas globais
                custo_antes = sum(res_orig.custo_total_por_mg.values())
                custo_depois = sum(res_otim.custo_total_por_mg.values())
                economia_otm = custo_antes - custo_depois

                c1o, c2o, c3o = st.columns(3)
                c1o.metric("Custo Antes", f"R$ {custo_antes:,.2f}")
                c2o.metric("Custo Depois", f"R$ {custo_depois:,.2f}")
                c3o.metric(
                    "Economia da Otimização",
                    f"R$ {economia_otm:,.2f}",
                    f"{(economia_otm / custo_antes * 100):.1f}%" if custo_antes > 0 else "0%",
                )

                st.divider()

                # Tabela comparativa por MG
                st.markdown("#### 💰 Comparação por Microrrede")
                df_comp_otm = pd.DataFrame({
                    "Microrrede": nomes_otm,
                    "Antes (R$)": [f"R$ {res_orig.custo_total_por_mg[n]:,.2f}" for n in nomes_otm],
                    "Depois (R$)": [f"R$ {res_otim.custo_total_por_mg[n]:,.2f}" for n in nomes_otm],
                    "Economia (R$)": [
                        f"R$ {res_orig.custo_total_por_mg[n] - res_otim.custo_total_por_mg[n]:,.2f}"
                        for n in nomes_otm
                    ],
                })
                st.dataframe(df_comp_otm, width='stretch', hide_index=True)

                # Gráfico comparativo
                df_comp_chart = pd.DataFrame({
                    "Microrrede": nomes_otm,
                    "Antes da Otimização (R$)": [res_orig.custo_total_por_mg[n] for n in nomes_otm],
                    "Após Otimização (R$)": [res_otim.custo_total_por_mg[n] for n in nomes_otm],
                })
                fig_otm = px.bar(
                    df_comp_chart,
                    x="Microrrede",
                    y=["Antes da Otimização (R$)", "Após Otimização (R$)"],
                    barmode="group",
                    text_auto=".2s",
                    color_discrete_map={
                        "Antes da Otimização (R$)": "#EF553B",
                        "Após Otimização (R$)": "#00CC96",
                    },
                )
                fig_otm.update_layout(yaxis_title="Custo (R$)", height=400)
                st.plotly_chart(fig_otm, width='stretch', key=f"saz_otm_custos_{estacao}")

                st.divider()

                # Cargas movidas
                if res_otm.get("cargas_movidas"):
                    st.markdown("#### 🔀 Cargas Deslizadas")
                    df_movidas = pd.DataFrame(res_otm["cargas_movidas"])
                    df_movidas.columns = [
                        "Microrrede", "Carga", "Horário Original",
                        "Novo Horário", "Duração (min)",
                    ]
                    st.dataframe(df_movidas, width='stretch', hide_index=True)
                else:
                    st.info("Nenhuma carga foi deslizada — os horários atuais já são ótimos.")

                st.divider()

                # --- FLUXO SANKEY PÓS-OTIMIZAÇÃO ---
                st.subheader("🔄 Fluxo de Energia P2P Pós-Otimização")
                
                fluxos_otm = {}
                for t in res_otim.trades:
                    key = (t.vendedor_nome, t.comprador_nome)
                    fluxos_otm[key] = fluxos_otm.get(key, 0.0) + (t.energia_enviada_kw / 60)
                
                if fluxos_otm:
                    nomes_unicos_otm = list(set([k[0] for k in fluxos_otm] + [k[1] for k in fluxos_otm]))
                    idx_nome_otm = {n: i for i, n in enumerate(nomes_unicos_otm)}
                    
                    fig_sankey_otm = go.Figure(data=[go.Sankey(
                        node=dict(
                            pad=15, thickness=20,
                            line=dict(color="black", width=0.5),
                            label=nomes_unicos_otm,
                            color=["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"][:len(nomes_unicos_otm)]
                        ),
                        link=dict(
                            source=[idx_nome_otm[k[0]] for k in fluxos_otm],
                            target=[idx_nome_otm[k[1]] for k in fluxos_otm],
                            value=list(fluxos_otm.values()),
                        )
                    )])
                    fig_sankey_otm.update_layout(height=400)
                    st.plotly_chart(fig_sankey_otm, width='stretch', key=f"saz_sankey_otm_{estacao}")
                else:
                    st.info("Não houve transações P2P neste cenário otimizado.")

                st.divider()

                # Perfis energéticos pós-otimização
                st.markdown("#### 📈 Perfil Energético Pós-Otimização")

                tabs_mg_otm = st.tabs([str(n) for n in nomes_otm])

                for idx_mg, nome in enumerate(nomes_otm):
                    with tabs_mg_otm[idx_mg]:
                        est_otm = res_otim.estados[nome]
                        horas = np.arange(1440) / 60

                        fig_perfil_otm = go.Figure()

                        fig_perfil_otm.add_trace(go.Scatter(
                            x=horas, y=est_otm.uso_solar, mode="lines", name="Solar",
                            line=dict(width=0), stackgroup="uso",
                            fillcolor="rgba(255,215,0,0.6)",
                        ))
                        fig_perfil_otm.add_trace(go.Scatter(
                            x=horas, y=est_otm.uso_bateria, mode="lines", name="Bateria",
                            line=dict(width=0), stackgroup="uso",
                            fillcolor="rgba(50,205,50,0.6)",
                        ))
                        fig_perfil_otm.add_trace(go.Scatter(
                            x=horas, y=est_otm.uso_diesel, mode="lines", name="Diesel",
                            line=dict(width=0), stackgroup="uso",
                            fillcolor="rgba(169,169,169,0.6)",
                        ))
                        fig_perfil_otm.add_trace(go.Scatter(
                            x=horas, y=est_otm.uso_biogas, mode="lines", name="Biogás",
                            line=dict(width=0), stackgroup="uso",
                            fillcolor="rgba(139,69,19,0.6)",
                        ))
                        fig_perfil_otm.add_trace(go.Scatter(
                            x=horas, y=est_otm.uso_concessionaria, mode="lines",
                            name="Concessionária",
                            line=dict(width=0), stackgroup="uso",
                            fillcolor="rgba(65,105,225,0.6)",
                        ))
                        fig_perfil_otm.add_trace(go.Scatter(
                            x=horas, y=est_otm.energia_comprada, mode="lines",
                            name="Compra P2P",
                            line=dict(width=0), stackgroup="uso",
                            fillcolor="rgba(255,105,180,0.6)",
                        ))

                        # Linha de demanda
                        fig_perfil_otm.add_trace(go.Scatter(
                            x=horas, y=est_otm.curva_carga, mode="lines",
                            name="Demanda",
                            line=dict(color="red", width=2, dash="dash"),
                        ))

                        # Energia vendida (negativa)
                        if est_otm.energia_vendida.sum() > 0:
                            fig_perfil_otm.add_trace(go.Scatter(
                                x=horas, y=-est_otm.energia_vendida, mode="lines",
                                name="Venda P2P",
                                line=dict(color="#FF4500", width=1),
                                fill="tozeroy",
                                fillcolor="rgba(255,69,0,0.3)",
                            ))

                        fig_perfil_otm.update_layout(
                            title=f"Perfil Energético Otimizado — {nome} ({estacao})",
                            xaxis_title="Hora do Dia",
                            yaxis_title="Potência (kW)",
                            xaxis=dict(
                                tickmode="array",
                                tickvals=list(range(0, 25, 2)),
                                ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
                            ),
                            hovermode="x unified",
                            height=450,
                        )
                        st.plotly_chart(
                            fig_perfil_otm, width='stretch',
                            key=f"saz_otm_perfil_{estacao}_{idx_mg}",
                        )

                        # --- NÍVEIS DE TANQUE E BATERIA (PÓS-OTIMIZAÇÃO) ---
                        st.markdown("##### 🛢️ Níveis de Armazenamento (Pós-Otimização)")

                        fig_niveis_otm = go.Figure()

                        if est_otm.hist_nivel_diesel.sum() > 0:
                            fig_niveis_otm.add_trace(
                                go.Scatter(
                                    x=horas,
                                    y=est_otm.hist_nivel_diesel,
                                    mode="lines",
                                    name="⛽ Diesel (L)",
                                    line=dict(color="#A9A9A9", width=2),
                                )
                            )

                        if est_otm.hist_nivel_biogas.sum() > 0:
                            fig_niveis_otm.add_trace(
                                go.Scatter(
                                    x=horas,
                                    y=est_otm.hist_nivel_biogas,
                                    mode="lines",
                                    name="🌿 Biogás (m³)",
                                    line=dict(color="#8B4513", width=2),
                                )
                            )

                        if est_otm.hist_nivel_bateria.sum() > 0:
                            fig_niveis_otm.add_trace(
                                go.Scatter(
                                    x=horas,
                                    y=est_otm.hist_nivel_bateria,
                                    mode="lines",
                                    name="🔋 Bateria (kWh)",
                                    line=dict(color="#32CD32", width=2),
                                )
                            )

                        fig_niveis_otm.update_layout(
                            title=f"Níveis de Armazenamento (Otimizado) — {nome} ({estacao})",
                            xaxis_title="Hora do Dia",
                            yaxis_title="Nível",
                            xaxis=dict(
                                tickmode="array",
                                tickvals=list(range(0, 25, 2)),
                                ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
                            ),
                            hovermode="x unified",
                            height=350,
                        )
                        st.plotly_chart(
                            fig_niveis_otm, width='stretch',
                            key=f"saz_otm_niveis_{estacao}_{idx_mg}",
                        )

                        # Mini-métricas pós-otimização
                        c1o, c2o, c3o, c4o, c5o = st.columns(5)
                        total_vendido_otm = est_otm.energia_vendida.sum() / 60
                        total_comprado_otm = est_otm.energia_comprada.sum() / 60
                        c1o.metric("Energia Vendida", f"{total_vendido_otm:,.1f} kWh")
                        c2o.metric("Energia Comprada", f"{total_comprado_otm:,.1f} kWh")
                        saldo_otm = (
                            res_otim.receita_por_mg[nome]
                            - res_otim.gasto_compras_por_mg[nome]
                        )
                        c3o.metric(
                            "Saldo P2P",
                            f"R$ {saldo_otm:,.2f}",
                            "Superávit" if saldo_otm >= 0 else "Déficit",
                        )
                        c4o.metric(
                            "⛽ Diesel Final",
                            f"{est_otm.hist_nivel_diesel[-1]:,.2f} L",
                        )
                        c5o.metric(
                            "🔋 Bateria Final",
                            f"{est_otm.hist_nivel_bateria[-1]:,.2f} kWh",
                        )

