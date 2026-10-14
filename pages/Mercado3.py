import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import copy
import time
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


# ============================================================
# CENÁRIO SEM TRANSAÇÃO (MICRORREDES ISOLADAS)
# ============================================================

class SimuladorSemTransacao(SimuladorMercado):
    """
    Mesmo despacho local do SimuladorMercado (Solar → Bateria → Diesel/Biogás,
    em ordem de custo), porém SEM mercado P2P: nenhuma microrrede compra ou
    vende para outra. Todo déficit residual é suprido pela concessionária.
    """

    def _matching_mercado(self, estados, deficits, t):
        for nome, deficit in deficits.items():
            if deficit <= 0.001:
                continue
            estado = estados[nome]
            mg = estado.microrrede
            if mg.concessionaria:
                estado.uso_concessionaria[t] += deficit
                estado.custo_concessionaria[t] += deficit * mg.concessionaria.tarifa / 60


def _kwh(arr) -> float:
    """Converte uma série em kW (passo de 1 min) para energia em kWh."""
    return float(np.sum(arr)) / 60


_XAXIS_HORAS = dict(
    title=dict(text="<b>Hora do Dia</b>", font=dict(color="black", size=14)),
    tickfont=dict(color="black", size=13),
    tickmode="array",
    tickvals=list(range(0, 25, 2)),
    ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
)

COR_SEM_TRANSACAO = "#8C564B"
COR_COM_P2P = "#00CC96"

# Catálogo de todos os métodos comparados (chave em comp_otm_sazonais[estacao]).
# (chave, rótulo, cenário, cor, é_base)
METODOS_COMP = [
    ("original_iso", "Sem Transação (base)", "Isolado", COR_SEM_TRANSACAO, True),
    ("heuristica_iso", "Regras", "Isolado", "#CD853F", False),
    ("milp_puro_iso", "MILP Local", "Isolado", "#B794F4", False),
    ("milp_iso", "MILP Local + Refino", "Isolado", "#6B46C1", False),
    ("original", "P2P (base)", "P2P", "#A0AEC0", True),
    ("heuristica", "Regras", "P2P", "#ECC94B", False),
    ("milp_puro", "MILP Local", "P2P", "#9F7AEA", False),
    ("milp", "MILP Local + Refino", "P2P", "#553C9A", False),
    ("milp_central", "MILP Centralizado", "P2P", "#2B6CB0", False),
]


def _rotulo_metodo(chave):
    for k, rot, cen, _cor, base in METODOS_COMP:
        if k == chave:
            return rot if base else f"{rot} ({cen})"
    return chave


def _res_metodo(cs, chave):
    """Retorna o ResultadoSimulacao de um método (bases são o próprio resultado)."""
    v = cs.get(chave)
    if v is None:
        return None
    return v["otimizado"] if isinstance(v, dict) else v


def _cargas_metodo(cs, chave):
    v = cs.get(chave)
    return v.get("cargas_movidas", []) if isinstance(v, dict) else []


def _metodos_disponiveis(cs):
    return [m for m in METODOS_COMP if cs.get(m[0]) is not None]


def _add_perfil_estado(fig, est, row, col, showlegend):
    """Adiciona o mix energético empilhado de um EstadoMG em um subplot."""
    horas_ = np.arange(1440) / 60
    grupo = f"uso_{row}_{col}"
    series = [
        ("Solar", est.uso_solar, "rgba(255,215,0,0.6)"),
        ("Bateria", est.uso_bateria, "rgba(50,205,50,0.6)"),
        ("Diesel", est.uso_diesel, "rgba(169,169,169,0.6)"),
        ("Biogás", est.uso_biogas, "rgba(139,69,19,0.6)"),
        ("Concessionária", est.uso_concessionaria, "rgba(65,105,225,0.6)"),
        ("Compra P2P", est.energia_comprada, "rgba(255,105,180,0.6)"),
    ]
    for nome_s, y, cor in series:
        if np.sum(y) <= 0:
            continue
        fig.add_trace(go.Scatter(
            x=horas_, y=y, mode="lines", name=nome_s, legendgroup=nome_s,
            line=dict(width=0), stackgroup=grupo, fillcolor=cor,
            showlegend=showlegend,
        ), row=row, col=col)
    fig.add_trace(go.Scatter(
        x=horas_, y=est.curva_carga, mode="lines", name="Demanda", legendgroup="Demanda",
        line=dict(color="red", width=2, dash="dash"), showlegend=showlegend,
    ), row=row, col=col)
    if np.sum(est.energia_vendida) > 0:
        fig.add_trace(go.Scatter(
            x=horas_, y=-est.energia_vendida, mode="lines", name="Venda P2P", legendgroup="Venda P2P",
            line=dict(color="#FF4500", width=1), fill="tozeroy",
            fillcolor="rgba(255,69,0,0.3)", showlegend=showlegend,
        ), row=row, col=col)


st.set_page_config(page_title="Mercado Sazonal 3", layout="wide")
st.title("Mercado de Energia P2P — Análise Sazonal (com Cenário Sem Transação)")
st.markdown(
    "Simulação do mercado P2P para cada estação do ano, "
    "comparando perfis solares e de carga das microrredes. "
    "Além disso, cada estação também é simulada **sem transação entre as microrredes** "
    "(cada uma operando isolada, apenas com suas fontes e a concessionária), "
    "permitindo comparar diretamente os dois cenários."
)

# ============================================================
# CONFIGURAÇÕES
# ============================================================

st.header("Configurações")

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

st.subheader("Seleção por Estação")
st.caption(
    "Cada microrrede tem uma estação associada no banco de dados. "
    "Selecione as estações que deseja simular e compare os resultados."
)

# Mostrar resumo de microrredes por estação
cols_resumo = st.columns(min(len(estacoes_disponiveis), 4))
for idx, est in enumerate(estacoes_disponiveis):
    with cols_resumo[idx % 4]:
        st.metric(
            f"{est}",
            f"{len(mgs_por_estacao[est])} MGs",
        )

estacoes_selecionadas = st.multiselect(
    "Estações a Simular:",
    estacoes_disponiveis,
    default=estacoes_disponiveis,
    format_func=lambda e: f"{e} ({len(mgs_por_estacao[e])} MGs)",
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
    solar_ligado = st.checkbox("Solar", value=True, key="saz_solar")
    bateria_ligada = st.checkbox("Bateria", value=True, key="saz_bat")
    diesel_ligado = st.checkbox("Diesel", value=True, key="saz_diesel")
    biogas_ligado = st.checkbox("Biogás", value=True, key="saz_biogas")

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

st.header("Fator de Carga Sazonal (opcional)")
st.caption("Ajuste para refletir variações adicionais de demanda por estação.")

cols_fator = st.columns(len(estacoes_selecionadas))
fatores_carga = {}
for idx, est in enumerate(estacoes_selecionadas):
    with cols_fator[idx]:
        fatores_carga[est] = st.slider(
            f"{est}",
            -30.0, 30.0, 0.0, 1.0,
            key=f"fator_{est}",
        ) / 100.0

st.divider()

# ============================================================
# SIMULAÇÃO SAZONAL
# ============================================================

executar = st.button(
    "Simular Todas as Estações",
    type="primary",
    width='stretch',
)

if executar:
    start_simulacao_global = time.perf_counter()
    tempo_simulador_mercado = 0.0
    tempo_simulador_isolado = 0.0
    resultados_sazonais = {}
    total_estacoes = len(estacoes_selecionadas)
    progress = st.progress(0, text="Preparando simulações...")

    # Usar no_autoflush para evitar que modificações temporárias
    # (curva_geracao, potência de carga) disparem escrita no banco
    with _crud.session.no_autoflush:
        for idx_est, estacao in enumerate(estacoes_selecionadas):
            progress.progress(
                idx_est / total_estacoes,
                text=f"Simulando {estacao}...",
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
            t0 = time.perf_counter()
            resultado = simulador.simular()
            t_sim_p2p = time.perf_counter() - t0
            tempo_simulador_mercado += t_sim_p2p

            # Simular as mesmas microrredes SEM transação entre elas
            simulador_iso = SimuladorSemTransacao(
                microrredes=mgs_estacao,
                config=config,
                margem_venda=margem,
                coef_perda_km=coef_perda,
            )
            t0 = time.perf_counter()
            resultado_isolado = simulador_iso.simular()
            t_sim_iso = time.perf_counter() - t0
            tempo_simulador_isolado += t_sim_iso

            resultados_sazonais[estacao] = {
                "resultado": resultado,
                "resultado_isolado": resultado_isolado,
                "curvas_solares": curvas_solares,
                "mgs": mgs_estacao,
                "tempo_sim_p2p": t_sim_p2p,
                "tempo_sim_iso": t_sim_iso,
            }

    # Descartar modificações temporárias para não persistir no banco
    _crud.session.rollback()

    progress.progress(1.0, text="Simulações concluídas!")
    st.session_state["m3_resultados_sazonais"] = resultados_sazonais
    st.session_state["m3_estacoes_simuladas"] = estacoes_selecionadas
    st.session_state["m3_mgs_por_estacao"] = dict(mgs_por_estacao)
    st.session_state["m3_fatores_carga"] = fatores_carga
    
    st.session_state["m3_tempo_simulador_mercado"] = tempo_simulador_mercado
    st.session_state["m3_tempo_simulador_isolado"] = tempo_simulador_isolado
    st.session_state["m3_tempo_simulacao_total"] = time.perf_counter() - start_simulacao_global

# ============================================================
# RESULTADOS POR ESTAÇÃO
# ============================================================

if "m3_resultados_sazonais" in st.session_state:
    resultados_sazonais = st.session_state["m3_resultados_sazonais"]
    estacoes_simuladas = st.session_state["m3_estacoes_simuladas"]

    st.divider()
    st.header("Resultados por Estação")

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
        [f"{e}" for e in estacoes_simuladas]
    )

    for idx_est, estacao in enumerate(estacoes_simuladas):
        with tabs_estacoes[idx_est]:
            resultado = resultados_sazonais[estacao]["resultado"]
            nomes = list(resultado.custo_isolado_por_mg.keys())

            # --- MÉTRICAS GLOBAIS ---
            custo_iso_total = sum(resultado.custo_isolado_por_mg.values())
            economia_pct = (
                (resultado.economia_total / custo_iso_total * 100)
                if custo_iso_total > 0
                else 0
            )

            c1_g, c2_g = st.columns(2)
            c1_g.metric(
                "Economia Total",
                f"R$ {resultado.economia_total:,.2f}",
                f"{economia_pct:.1f}%",
            )
            c2_g.metric(
                "Custo Total (Mercado)",
                f"R$ {sum(resultado.custo_total_por_mg.values()):,.2f}",
            )

            st.divider()

            # --- CUSTOS COMPARATIVOS ---
            st.subheader(f"Custos — {estacao}")

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
            st.subheader("Balanço Financeiro por Microrrede")
            df_balanco = pd.DataFrame(
                {
                    "Microrrede": nomes,
                    "Custo Isolado (R$)": [
                        f"R$ {resultado.custo_isolado_por_mg[n]:,.2f}" for n in nomes
                    ],
                    "Custo com Mercado (R$)": [
                        f"R$ {resultado.custo_total_por_mg[n]:,.2f}" for n in nomes
                    ],
                    "Economia (R$)": [
                        f"R$ {resultado.economia_por_mg[n]:,.2f}" for n in nomes
                    ],
                }
            )
            st.dataframe(df_balanco, width='stretch', hide_index=True)

            st.divider()

            # ====================================================
            # SEM TRANSAÇÃO x COM MERCADO P2P (POR ESTAÇÃO)
            # ====================================================
            res_iso = resultados_sazonais[estacao].get("resultado_isolado")
            if res_iso is not None:
                st.subheader(f"Sem Transação vs Com Mercado P2P — {estacao}")
                st.caption(
                    "O cenário **Sem Transação** é uma nova simulação das mesmas microrredes, "
                    "com o mesmo despacho local, mas sem compra/venda entre elas: todo déficit "
                    "é suprido pela concessionária e o excedente solar não é vendido."
                )

                custo_sem = sum(res_iso.custo_total_por_mg.values())
                custo_com = sum(resultado.custo_total_por_mg.values())
                ganho_mercado = custo_sem - custo_com
                ganho_pct = (ganho_mercado / custo_sem * 100) if custo_sem > 0 else 0
                conc_sem = sum(_kwh(e.uso_concessionaria) for e in res_iso.estados.values())
                conc_com = sum(_kwh(e.uso_concessionaria) for e in resultado.estados.values())

                c1s, c2s, c3s, c4s = st.columns(4)
                c1s.metric("Custo Sem Transação", f"R$ {custo_sem:,.2f}")
                c2s.metric("Custo Com Mercado P2P", f"R$ {custo_com:,.2f}")
                c3s.metric("Ganho do Mercado", f"R$ {ganho_mercado:,.2f}", f"{ganho_pct:.1f}%")
                c4s.metric(
                    "Energia da Concessionária",
                    f"{conc_com:,.1f} kWh",
                    f"{conc_com - conc_sem:,.1f} kWh vs sem transação",
                    delta_color="inverse",
                )

                # --- Tabela por MG ---
                linhas_sem_com = []
                for n in nomes:
                    e_sem = res_iso.estados[n]
                    e_com = resultado.estados[n]
                    c_sem = res_iso.custo_total_por_mg[n]
                    c_com = resultado.custo_total_por_mg[n]
                    linhas_sem_com.append({
                        "Microrrede": n,
                        "Custo Sem Transação (R$)": c_sem,
                        "Custo Com P2P (R$)": c_com,
                        "Ganho (R$)": c_sem - c_com,
                        "Ganho (%)": ((c_sem - c_com) / c_sem * 100) if c_sem > 0 else 0,
                        "Concessionária Sem (kWh)": _kwh(e_sem.uso_concessionaria),
                        "Concessionária Com (kWh)": _kwh(e_com.uso_concessionaria),
                        "Diesel Sem (kWh)": _kwh(e_sem.uso_diesel),
                        "Diesel Com (kWh)": _kwh(e_com.uso_diesel),
                        "Vendido P2P (kWh)": _kwh(e_com.energia_vendida),
                        "Comprado P2P (kWh)": _kwh(e_com.energia_comprada),
                    })
                df_sem_com = pd.DataFrame(linhas_sem_com)
                st.dataframe(
                    df_sem_com.style.format({
                        "Custo Sem Transação (R$)": "R$ {:,.2f}",
                        "Custo Com P2P (R$)": "R$ {:,.2f}",
                        "Ganho (R$)": "R$ {:,.2f}",
                        "Ganho (%)": "{:.1f}%",
                        "Concessionária Sem (kWh)": "{:,.1f}",
                        "Concessionária Com (kWh)": "{:,.1f}",
                        "Diesel Sem (kWh)": "{:,.1f}",
                        "Diesel Com (kWh)": "{:,.1f}",
                        "Vendido P2P (kWh)": "{:,.1f}",
                        "Comprado P2P (kWh)": "{:,.1f}",
                    }),
                    width='stretch',
                    hide_index=True,
                )

                # --- Gráficos de custo e de concessionária por MG ---
                col_gs1, col_gs2 = st.columns(2)
                with col_gs1:
                    fig_sc_custo = go.Figure()
                    fig_sc_custo.add_trace(go.Bar(
                        name="Sem Transação", x=nomes,
                        y=df_sem_com["Custo Sem Transação (R$)"],
                        marker_color=COR_SEM_TRANSACAO,
                        text=[f"R$ {v:,.2f}" for v in df_sem_com["Custo Sem Transação (R$)"]],
                        textposition="auto", textfont=dict(color="black", size=13),
                    ))
                    fig_sc_custo.add_trace(go.Bar(
                        name="Com Mercado P2P", x=nomes,
                        y=df_sem_com["Custo Com P2P (R$)"],
                        marker_color=COR_COM_P2P,
                        text=[f"R$ {v:,.2f}" for v in df_sem_com["Custo Com P2P (R$)"]],
                        textposition="auto", textfont=dict(color="black", size=13),
                    ))
                    fig_sc_custo.update_layout(
                        title=dict(text="<b>Custo Diário por Microrrede</b>", font=dict(color="black", size=16)),
                        font=dict(color="black", size=14, family="Arial, sans-serif"),
                        barmode="group",
                        yaxis=dict(
                            title=dict(text="<b>Custo (R$)</b>", font=dict(color="black", size=14)),
                            tickfont=dict(color="black", size=13),
                        ),
                        xaxis=dict(tickfont=dict(color="black", size=13)),
                        legend=dict(font=dict(color="black", size=13)),
                        height=420,
                    )
                    st.plotly_chart(fig_sc_custo, width='stretch', key=f"m3_semcom_custo_{estacao}")
                with col_gs2:
                    fig_sc_conc = go.Figure()
                    fig_sc_conc.add_trace(go.Bar(
                        name="Sem Transação", x=nomes,
                        y=df_sem_com["Concessionária Sem (kWh)"],
                        marker_color=COR_SEM_TRANSACAO,
                        text=[f"{v:,.1f} kWh" for v in df_sem_com["Concessionária Sem (kWh)"]],
                        textposition="auto", textfont=dict(color="black", size=13),
                    ))
                    fig_sc_conc.add_trace(go.Bar(
                        name="Com Mercado P2P", x=nomes,
                        y=df_sem_com["Concessionária Com (kWh)"],
                        marker_color=COR_COM_P2P,
                        text=[f"{v:,.1f} kWh" for v in df_sem_com["Concessionária Com (kWh)"]],
                        textposition="auto", textfont=dict(color="black", size=13),
                    ))
                    fig_sc_conc.update_layout(
                        title=dict(text="<b>Energia da Concessionária por Microrrede</b>", font=dict(color="black", size=16)),
                        font=dict(color="black", size=14, family="Arial, sans-serif"),
                        barmode="group",
                        yaxis=dict(
                            title=dict(text="<b>Energia (kWh/dia)</b>", font=dict(color="black", size=14)),
                            tickfont=dict(color="black", size=13),
                        ),
                        xaxis=dict(tickfont=dict(color="black", size=13)),
                        legend=dict(font=dict(color="black", size=13)),
                        height=420,
                    )
                    st.plotly_chart(fig_sc_conc, width='stretch', key=f"m3_semcom_conc_{estacao}")

                # --- Perfis lado a lado por MG ---
                st.markdown("#### Perfil Energético — Sem Transação x Com Mercado P2P")
                tabs_mg_sc = st.tabs([str(n) for n in nomes])
                horas_sc = np.arange(1440) / 60
                for idx_mg, nome in enumerate(nomes):
                    with tabs_mg_sc[idx_mg]:
                        e_sem = res_iso.estados[nome]
                        e_com = resultado.estados[nome]

                        fig_sc = make_subplots(
                            rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.10,
                            subplot_titles=[
                                f"Sem Transação — {nome} ({estacao})",
                                f"Com Mercado P2P — {nome} ({estacao})",
                            ],
                        )
                        _add_perfil_estado(fig_sc, e_sem, 1, 1, showlegend=True)
                        _add_perfil_estado(fig_sc, e_com, 2, 1, showlegend=False)
                        # Garante legenda para séries que só aparecem no cenário P2P
                        nomes_leg = {tr.name for tr in fig_sc.data if tr.showlegend}
                        for tr in fig_sc.data:
                            if tr.name not in nomes_leg:
                                tr.showlegend = True
                                nomes_leg.add(tr.name)
                        fig_sc.update_layout(
                            font=dict(color="black", size=14, family="Arial, sans-serif"),
                            height=650,
                            hovermode="x unified",
                            legend=dict(font=dict(color="black", size=13)),
                        )
                        for annotation in fig_sc['layout']['annotations']:
                            annotation['font'] = dict(size=16, color='black', family="Arial, sans-serif")
                        fig_sc.update_xaxes(_XAXIS_HORAS, row=2, col=1)
                        for r in (1, 2):
                            fig_sc.update_yaxes(
                                title_text="<b>Potência (kW)</b>",
                                title_font=dict(color="black", size=14),
                                tickfont=dict(color="black", size=13),
                                row=r, col=1,
                            )
                        st.plotly_chart(fig_sc, width='stretch', key=f"m3_semcom_perfil_{estacao}_{idx_mg}")

                        # Níveis de armazenamento sobrepostos
                        niveis = [
                            ("Bateria", "hist_nivel_bateria", "Nível (kWh)"),
                            ("Diesel", "hist_nivel_diesel", "Volume (L)"),
                            ("Biogás", "hist_nivel_biogas", "Nível"),
                        ]
                        for rotulo, attr, ytitle in niveis:
                            y_sem = getattr(e_sem, attr)
                            y_com = getattr(e_com, attr)
                            if np.sum(y_sem) <= 0 and np.sum(y_com) <= 0:
                                continue
                            fig_niv = go.Figure()
                            fig_niv.add_trace(go.Scatter(
                                x=horas_sc, y=y_sem, mode="lines", name="Sem Transação",
                                line=dict(color=COR_SEM_TRANSACAO, width=2),
                            ))
                            fig_niv.add_trace(go.Scatter(
                                x=horas_sc, y=y_com, mode="lines", name="Com Mercado P2P",
                                line=dict(color=COR_COM_P2P, width=2, dash="dash"),
                            ))
                            fig_niv.update_layout(
                                title=dict(text=f"<b>{rotulo} — {nome} ({estacao})</b>", font=dict(color="black", size=16)),
                                font=dict(color="black", size=14, family="Arial, sans-serif"),
                                xaxis=_XAXIS_HORAS,
                                yaxis=dict(
                                    title=dict(text=f"<b>{ytitle}</b>", font=dict(color="black", size=14)),
                                    tickfont=dict(color="black", size=13),
                                ),
                                legend=dict(font=dict(color="black", size=13)),
                                hovermode="x unified",
                                height=300,
                            )
                            st.plotly_chart(fig_niv, width='stretch', key=f"m3_semcom_niv_{attr}_{estacao}_{idx_mg}")

                        # Métricas da MG
                        c_sem_mg = res_iso.custo_total_por_mg[nome]
                        c_com_mg = resultado.custo_total_por_mg[nome]
                        cm1, cm2, cm3, cm4 = st.columns(4)
                        cm1.metric("Custo Sem Transação", f"R$ {c_sem_mg:,.2f}")
                        cm2.metric("Custo Com P2P", f"R$ {c_com_mg:,.2f}")
                        cm3.metric(
                            "Ganho com o Mercado",
                            f"R$ {c_sem_mg - c_com_mg:,.2f}",
                            f"{((c_sem_mg - c_com_mg) / c_sem_mg * 100):.1f}%" if c_sem_mg > 0 else "0%",
                        )
                        cm4.metric(
                            "Concessionária",
                            f"{_kwh(e_com.uso_concessionaria):,.1f} kWh",
                            f"{_kwh(e_com.uso_concessionaria) - _kwh(e_sem.uso_concessionaria):,.1f} kWh",
                            delta_color="inverse",
                        )

                st.divider()

            # --- PERFIL ENERGÉTICO POR MG ---
            st.subheader(f"Perfil Energético — {estacao}")

            tabs_mg = st.tabs([str(n) for n in nomes])

            for idx_mg, nome in enumerate(nomes):
                with tabs_mg[idx_mg]:
                    est = resultado.estados[nome]
                    res_iso = resultados_sazonais[estacao].get("resultado_isolado")
                    est_iso = res_iso.estados[nome] if res_iso else est
                    horas = np.arange(1440) / 60

                    fig_perfil = make_subplots(
                        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.10,
                        subplot_titles=[
                            f"Operação Isolada — {nome} ({estacao})",
                            f"Com Mercado P2P — {nome} ({estacao})",
                        ],
                    )
                    _add_perfil_estado(fig_perfil, est_iso, 1, 1, showlegend=True)
                    _add_perfil_estado(fig_perfil, est, 2, 1, showlegend=False)

                    # Garante legenda para séries que só aparecem no cenário P2P
                    nomes_leg = {tr.name for tr in fig_perfil.data if tr.showlegend}
                    for tr in fig_perfil.data:
                        if tr.name not in nomes_leg:
                            tr.showlegend = True
                            nomes_leg.add(tr.name)

                    fig_perfil.update_layout(
                        font=dict(color="black", size=14, family="Arial, sans-serif"),
                        height=650,
                        hovermode="x unified",
                        legend=dict(font=dict(color="black", size=13)),
                    )
                    for annotation in fig_perfil['layout']['annotations']:
                        annotation['font'] = dict(size=16, color='black', family="Arial, sans-serif")
                    fig_perfil.update_xaxes(_XAXIS_HORAS, row=2, col=1)
                    for r in (1, 2):
                        fig_perfil.update_yaxes(
                            title_text="<b>Potência (kW)</b>",
                            title_font=dict(color="black", size=14),
                            tickfont=dict(color="black", size=13),
                            row=r, col=1,
                        )
                    st.plotly_chart(fig_perfil, width='stretch', key=f"saz_perfil_{estacao}_{idx_mg}")

                    # --- NÍVEIS DE ARMAZENAMENTO (separados) ---
                    st.markdown("##### Níveis de Armazenamento")

                    _xaxis_cfg_niveis = dict(
                        title=dict(text="<b>Hora do Dia</b>", font=dict(color="black", size=14)),
                        tickfont=dict(color="black", size=13),
                        tickmode="array",
                        tickvals=list(range(0, 25, 2)),
                        ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
                    )

                    # Gráfico da Bateria
                    if est.hist_nivel_bateria.sum() > 0 or est_iso.hist_nivel_bateria.sum() > 0:
                        fig_bat = go.Figure()
                        fig_bat.add_trace(go.Scatter(
                            x=horas, y=est_iso.hist_nivel_bateria, mode="lines", name="Operação Isolada",
                            line=dict(color=COR_SEM_TRANSACAO, width=2),
                        ))
                        fig_bat.add_trace(go.Scatter(
                            x=horas, y=est.hist_nivel_bateria, mode="lines", name="Com Mercado P2P",
                            line=dict(color=COR_COM_P2P, width=2, dash="dash"),
                        ))
                        fig_bat.update_layout(
                            title=dict(text=f"<b>Nível da Bateria — {nome} ({estacao})</b>", font=dict(color="black", size=16)),
                            font=dict(color="black", size=14, family="Arial, sans-serif"),
                            yaxis=dict(
                                title=dict(text="<b>Nível de Energia (kWh)</b>", font=dict(color="black", size=14)),
                                tickfont=dict(color="black", size=13),
                            ),
                            xaxis=_xaxis_cfg_niveis,
                            legend=dict(font=dict(color="black", size=13)),
                            hovermode="x unified",
                            height=300,
                        )
                        st.plotly_chart(fig_bat, width='stretch', key=f"saz_niv_bat_{estacao}_{idx_mg}")

                    # Gráfico de Diesel
                    if est.hist_nivel_diesel.sum() > 0 or est_iso.hist_nivel_diesel.sum() > 0:
                        fig_diesel = go.Figure()
                        fig_diesel.add_trace(go.Scatter(
                            x=horas, y=est_iso.hist_nivel_diesel, mode="lines", name="Operação Isolada",
                            line=dict(color=COR_SEM_TRANSACAO, width=2),
                        ))
                        fig_diesel.add_trace(go.Scatter(
                            x=horas, y=est.hist_nivel_diesel, mode="lines", name="Com Mercado P2P",
                            line=dict(color=COR_COM_P2P, width=2, dash="dash"),
                        ))
                        _xaxis_cfg_diesel = dict(
                            title=dict(text="<b>Tempo (h)</b>", font=dict(color="black", size=14)),
                            tickfont=dict(color="black", size=13),
                            tickmode="array",
                            tickvals=list(range(0, 25, 2)),
                            ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
                        )
                        fig_diesel.update_layout(
                            title=dict(text=f"<b>Nível do Diesel (L x Tempo) — {nome}</b>", font=dict(color="black", size=16)),
                            font=dict(color="black", size=14, family="Arial, sans-serif"),
                            yaxis=dict(
                                title=dict(text="<b>Volume (L)</b>", font=dict(color="black", size=14)),
                                tickfont=dict(color="black", size=13),
                            ),
                            xaxis=_xaxis_cfg_diesel,
                            legend=dict(font=dict(color="black", size=13)),
                            hovermode="x unified",
                            height=300,
                        )
                        st.plotly_chart(fig_diesel, width='stretch', key=f"saz_niv_diesel_{estacao}_{idx_mg}")

                    # Mini-métricas por MG
                    c1m, c2m = st.columns(2)
                    c1m.metric(
                        "Diesel Final",
                        f"{est.hist_nivel_diesel[-1]:,.2f} L",
                    )
                    c2m.metric(
                        "Bateria Final",
                        f"{est.hist_nivel_bateria[-1]:,.2f} kWh",
                    )

    # ============================================================
    # COMPARAÇÃO ENTRE ESTAÇÕES
    # ============================================================

    st.divider()
    st.header("Comparação entre Estações")

    if len(estacoes_simuladas) >= 2:
        # --- TABELA COMPARATIVA ---
        st.subheader("Resumo Comparativo")

        dados_comp = []
        for estacao in estacoes_simuladas:
            res = resultados_sazonais[estacao]["resultado"]
            custo_iso = sum(res.custo_isolado_por_mg.values())
            custo_p2p = sum(res.custo_total_por_mg.values())
            dados_comp.append(
                {
                    "Estação": f"{estacao}",
                    "Custo Isolado (R$)": custo_iso,
                    "Custo com Mercado (R$)": custo_p2p,
                    "Economia (R$)": res.economia_total,
                    "Economia (%)": (
                        (res.economia_total / custo_iso * 100) if custo_iso > 0 else 0
                    ),
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
                }
            ),
            width='stretch',
            hide_index=True,
        )

        st.divider()

        # --- GRÁFICO CUSTOS POR ESTAÇÃO ---
        st.subheader("Custos por Estação")

        fig_comp_custos = go.Figure()
        nomes_est = [f"{e}" for e in estacoes_simuladas]
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
                textfont=dict(color="black", size=13),
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
                textfont=dict(color="black", size=13),
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
                textfont=dict(color="black", size=13),
            )
        )
        fig_comp_custos.update_layout(
            font=dict(color="black", size=14, family="Arial, sans-serif"),
            barmode="group",
            yaxis=dict(
                title=dict(text="<b>Valor (R$)</b>", font=dict(color="black", size=14)),
                tickfont=dict(color="black", size=13),
            ),
            xaxis=dict(
                tickfont=dict(color="black", size=13),
            ),
            legend=dict(font=dict(color="black", size=13)),
            height=450,
        )
        st.plotly_chart(
            fig_comp_custos,
            width='stretch',
            key="saz_comp_custos",
        )

        st.divider()

        # ============================================================
        # SEM TRANSAÇÃO x COM MERCADO P2P — ENTRE ESTAÇÕES
        # ============================================================
        st.subheader("Sem Transação vs Com Mercado P2P por Estação")
        st.caption(
            "Comparação do custo total e da energia da concessionária entre o cenário "
            "simulado sem transação entre as microrredes e o cenário com mercado P2P."
        )

        dados_sc_est = []
        for estacao in estacoes_simuladas:
            res_p2p = resultados_sazonais[estacao]["resultado"]
            res_iso_e = resultados_sazonais[estacao].get("resultado_isolado")
            if res_iso_e is None:
                continue
            c_sem = sum(res_iso_e.custo_total_por_mg.values())
            c_com = sum(res_p2p.custo_total_por_mg.values())
            dados_sc_est.append({
                "Estação": estacao,
                "Custo Sem Transação (R$)": c_sem,
                "Custo Com P2P (R$)": c_com,
                "Ganho (R$)": c_sem - c_com,
                "Ganho (%)": ((c_sem - c_com) / c_sem * 100) if c_sem > 0 else 0,
                "Concessionária Sem (kWh)": sum(_kwh(e.uso_concessionaria) for e in res_iso_e.estados.values()),
                "Concessionária Com (kWh)": sum(_kwh(e.uso_concessionaria) for e in res_p2p.estados.values()),
                "Volume P2P (kWh)": res_p2p.volume_total_kwh,
            })

        if dados_sc_est:
            df_sc_est = pd.DataFrame(dados_sc_est)
            st.dataframe(
                df_sc_est.style.format({
                    "Custo Sem Transação (R$)": "R$ {:,.2f}",
                    "Custo Com P2P (R$)": "R$ {:,.2f}",
                    "Ganho (R$)": "R$ {:,.2f}",
                    "Ganho (%)": "{:.1f}%",
                    "Concessionária Sem (kWh)": "{:,.1f}",
                    "Concessionária Com (kWh)": "{:,.1f}",
                    "Volume P2P (kWh)": "{:,.1f}",
                }),
                width='stretch',
                hide_index=True,
            )

            col_se1, col_se2 = st.columns(2)
            with col_se1:
                fig_sc_est = go.Figure()
                for col_nome, rotulo, cor in [
                    ("Custo Sem Transação (R$)", "Sem Transação", COR_SEM_TRANSACAO),
                    ("Custo Com P2P (R$)", "Com Mercado P2P", COR_COM_P2P),
                    ("Ganho (R$)", "Ganho do Mercado", "#636EFA"),
                ]:
                    fig_sc_est.add_trace(go.Bar(
                        name=rotulo, x=df_sc_est["Estação"], y=df_sc_est[col_nome],
                        marker_color=cor,
                        text=[f"R$ {v:,.2f}" for v in df_sc_est[col_nome]],
                        textposition="auto", textfont=dict(color="black", size=13),
                    ))
                fig_sc_est.update_layout(
                    title=dict(text="<b>Custo Total por Estação</b>", font=dict(color="black", size=16)),
                    font=dict(color="black", size=14, family="Arial, sans-serif"),
                    barmode="group",
                    yaxis=dict(
                        title=dict(text="<b>Valor (R$)</b>", font=dict(color="black", size=14)),
                        tickfont=dict(color="black", size=13),
                    ),
                    xaxis=dict(tickfont=dict(color="black", size=13)),
                    legend=dict(font=dict(color="black", size=13)),
                    height=450,
                )
                st.plotly_chart(fig_sc_est, width='stretch', key="m3_semcom_estacoes_custo")
            with col_se2:
                fig_sc_est_conc = go.Figure()
                for col_nome, rotulo, cor in [
                    ("Concessionária Sem (kWh)", "Sem Transação", COR_SEM_TRANSACAO),
                    ("Concessionária Com (kWh)", "Com Mercado P2P", COR_COM_P2P),
                ]:
                    fig_sc_est_conc.add_trace(go.Bar(
                        name=rotulo, x=df_sc_est["Estação"], y=df_sc_est[col_nome],
                        marker_color=cor,
                        text=[f"{v:,.1f} kWh" for v in df_sc_est[col_nome]],
                        textposition="auto", textfont=dict(color="black", size=13),
                    ))
                fig_sc_est_conc.update_layout(
                    title=dict(text="<b>Energia da Concessionária por Estação</b>", font=dict(color="black", size=16)),
                    font=dict(color="black", size=14, family="Arial, sans-serif"),
                    barmode="group",
                    yaxis=dict(
                        title=dict(text="<b>Energia (kWh/dia)</b>", font=dict(color="black", size=14)),
                        tickfont=dict(color="black", size=13),
                    ),
                    xaxis=dict(tickfont=dict(color="black", size=13)),
                    legend=dict(font=dict(color="black", size=13)),
                    height=450,
                )
                st.plotly_chart(fig_sc_est_conc, width='stretch', key="m3_semcom_estacoes_conc")

        st.divider()

        # ============================================================
        # COMPARAÇÃO MG-A-MG ENTRE ESTAÇÕES (MESMA MG EM ESTAÇÕES DIFERENTES)
        # ============================================================

        st.header("Comparação por Microrrede entre Estações")
        st.caption(
            "Compare a mesma microrrede (por nome base) em estações diferentes. "
            "Microrredes com o mesmo nome em estações distintas são agrupadas."
        )

        # Agrupar por nome base (sem a estação)
        nomes_base = defaultdict(dict)
        for estacao in estacoes_simuladas:
            res = resultados_sazonais[estacao]["resultado"]
            res_iso_b = resultados_sazonais[estacao].get("resultado_isolado")
            mgs_est = resultados_sazonais[estacao].get("mgs", [])
            for mg in mgs_est:
                nome_base = mg.nome  # O nome base da MG (sem estação)
                mg_display = f"Microrrede: {mg.nome}"
                if mg_display in res.custo_isolado_por_mg:
                    nomes_base[nome_base][estacao] = {
                        "display": mg_display,
                        "custo_isolado": res.custo_isolado_por_mg[mg_display],
                        "custo_sem_transacao": (
                            res_iso_b.custo_total_por_mg.get(mg_display, 0.0)
                            if res_iso_b is not None else res.custo_isolado_por_mg[mg_display]
                        ),
                        "estado_sem_transacao": (
                            res_iso_b.estados.get(mg_display) if res_iso_b is not None else None
                        ),
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
            tabs_comp_mg = st.tabs([f"{n}" for n in nomes_comparaveis.keys()])

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
                    st.markdown("#### Custos por Estação")
                    dados_tabela = []
                    for est in estacoes_desta_mg:
                        d = dados_estacoes[est]
                        dados_tabela.append({
                            "Estação": f"{est}",
                            "Custo Isolado (R$)": d["custo_isolado"],
                            "Custo Sem Transação (R$)": d["custo_sem_transacao"],
                            "Custo c/ Mercado (R$)": d["custo_p2p"],
                            "Receita Vendas (R$)": d["receita"],
                            "Gasto Compras (R$)": d["gasto_compras"],
                            "Economia (R$)": d["economia"],
                            "Ganho vs Sem Transação (R$)": d["custo_sem_transacao"] - d["custo_p2p"],
                        })
                    df_mg_comp = pd.DataFrame(dados_tabela)
                    st.dataframe(
                        df_mg_comp.style.format({
                            "Custo Isolado (R$)": "R$ {:,.2f}",
                            "Custo Sem Transação (R$)": "R$ {:,.2f}",
                            "Custo c/ Mercado (R$)": "R$ {:,.2f}",
                            "Receita Vendas (R$)": "R$ {:,.2f}",
                            "Gasto Compras (R$)": "R$ {:,.2f}",
                            "Economia (R$)": "R$ {:,.2f}",
                            "Ganho vs Sem Transação (R$)": "R$ {:,.2f}",
                        }),
                        width='stretch',
                        hide_index=True,
                    )

                    # --- GRÁFICO COMPARATIVO DE CUSTOS ---
                    fig_mg_custos = go.Figure()
                    nomes_est_mg = [f"{e}" for e in estacoes_desta_mg]

                    fig_mg_custos.add_trace(go.Bar(
                        name="Custo Isolado",
                        x=nomes_est_mg,
                        y=[dados_estacoes[e]["custo_isolado"] for e in estacoes_desta_mg],
                        marker_color="#EF553B",
                        text=[f"R$ {dados_estacoes[e]['custo_isolado']:,.2f}" for e in estacoes_desta_mg],
                        textposition="auto",
                        textfont=dict(color="black", size=13),
                    ))
                    fig_mg_custos.add_trace(go.Bar(
                        name="Sem Transação",
                        x=nomes_est_mg,
                        y=[dados_estacoes[e]["custo_sem_transacao"] for e in estacoes_desta_mg],
                        marker_color=COR_SEM_TRANSACAO,
                        text=[f"R$ {dados_estacoes[e]['custo_sem_transacao']:,.2f}" for e in estacoes_desta_mg],
                        textposition="auto",
                        textfont=dict(color="black", size=13),
                    ))
                    fig_mg_custos.add_trace(go.Bar(
                        name="Custo c/ Mercado",
                        x=nomes_est_mg,
                        y=[dados_estacoes[e]["custo_p2p"] for e in estacoes_desta_mg],
                        marker_color="#00CC96",
                        text=[f"R$ {dados_estacoes[e]['custo_p2p']:,.2f}" for e in estacoes_desta_mg],
                        textposition="auto",
                        textfont=dict(color="black", size=13),
                    ))
                    fig_mg_custos.update_layout(
                        title=dict(text=f"<b>Custos — {nome_base}</b>", font=dict(color="black", size=16)),
                        font=dict(color="black", size=14, family="Arial, sans-serif"),
                        barmode="group",
                        yaxis=dict(
                            title=dict(text="<b>Valor (R$)</b>", font=dict(color="black", size=14)),
                            tickfont=dict(color="black", size=13),
                        ),
                        xaxis=dict(
                            tickfont=dict(color="black", size=13),
                        ),
                        legend=dict(font=dict(color="black", size=13)),
                        height=400,
                    )
                    st.plotly_chart(fig_mg_custos, width='stretch', key=f"comp_mg_custos_{idx_tab}")

                    st.divider()

                    # --- PERFIS ENERGÉTICOS SOBREPOSTOS ---
                    st.markdown("#### Perfis de Demanda Sobrepostos")

                    horas = np.arange(1440) / 60
                    fig_demanda = go.Figure()

                    for est in estacoes_desta_mg:
                        estado = dados_estacoes[est]["estado"]
                        fig_demanda.add_trace(
                            go.Scatter(
                                x=horas,
                                y=estado.curva_carga,
                                mode="lines",
                                name=f"{est}",
                                line=dict(
                                    color=cores_estacao.get(est, "#888"),
                                    width=2,
                                ),
                            )
                        )

                    fig_demanda.update_layout(
                        title=dict(text=f"<b>Curva de Carga — {nome_base} (por Estação)</b>", font=dict(color="black", size=16)),
                        font=dict(color="black", size=14, family="Arial, sans-serif"),
                        xaxis=dict(
                            title=dict(text="<b>Hora do Dia</b>", font=dict(color="black", size=14)),
                            tickfont=dict(color="black", size=13),
                            tickmode="array",
                            tickvals=list(range(0, 25, 2)),
                            ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
                        ),
                        yaxis=dict(
                            title=dict(text="<b>Potência (kW)</b>", font=dict(color="black", size=14)),
                            tickfont=dict(color="black", size=13),
                        ),
                        legend=dict(font=dict(color="black", size=13)),
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
                        st.markdown("#### Geração Solar Sobreposta")
                        fig_solar = go.Figure()

                        for est in estacoes_desta_mg:
                            curva = dados_estacoes[est]["curva_solar"]
                            fig_solar.add_trace(
                                go.Scatter(
                                    x=horas,
                                    y=curva,
                                    mode="lines",
                                    name=f"{est}",
                                    line=dict(
                                        color=cores_estacao.get(est, "#888"),
                                        width=2,
                                    ),
                                )
                            )

                        fig_solar.update_layout(
                            title=dict(text=f"<b>Geração Solar — {nome_base} (por Estação)</b>", font=dict(color="black", size=16)),
                            font=dict(color="black", size=14, family="Arial, sans-serif"),
                            xaxis=dict(
                                title=dict(text="<b>Hora do Dia</b>", font=dict(color="black", size=14)),
                                tickfont=dict(color="black", size=13),
                                tickmode="array",
                                tickvals=list(range(0, 25, 2)),
                                ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
                            ),
                            yaxis=dict(
                                title=dict(text="<b>Potência (kW)</b>", font=dict(color="black", size=14)),
                                tickfont=dict(color="black", size=13),
                            ),
                            legend=dict(font=dict(color="black", size=13)),
                            hovermode="x unified",
                            height=400,
                        )
                        st.plotly_chart(fig_solar, width='stretch', key=f"comp_mg_solar_{idx_tab}")

                        # --- TOTAL DE GERAÇÃO SOLAR ---
                        st.markdown("#### Total de Geração Solar Diária")
                        fig_solar_total = go.Figure()
                        totais_solar = []
                        for est in estacoes_desta_mg:
                            curva = dados_estacoes[est]["curva_solar"]
                            total_kwh = curva.sum() / 60
                            totais_solar.append(total_kwh)
                            
                        fig_solar_total.add_trace(go.Bar(
                            name="Energia Solar Diária",
                            x=[f"{e}" for e in estacoes_desta_mg],
                            y=totais_solar,
                            marker_color="#FFD700",
                            text=[f"{v:,.1f} kWh" for v in totais_solar],
                            textposition="auto",
                            textfont=dict(color="black", size=13),
                        ))
                        fig_solar_total.update_layout(
                            title=dict(text=f"<b>Energia Solar Total Diária — {nome_base} (por Estação)</b>", font=dict(color="black", size=16)),
                            font=dict(color="black", size=14, family="Arial, sans-serif"),
                            yaxis=dict(
                                title=dict(text="<b>Energia (kWh/dia)</b>", font=dict(color="black", size=14)),
                                tickfont=dict(color="black", size=13),
                            ),
                            xaxis=dict(
                                tickfont=dict(color="black", size=13),
                            ),
                            legend=dict(font=dict(color="black", size=13)),
                            height=400,
                        )
                        st.plotly_chart(fig_solar_total, width='stretch', key=f"comp_mg_solar_tot_{idx_tab}")

                    # --- PERFIL ENERGÉTICO (MIX) LADO A LADO ---
                    st.markdown("#### Perfil Energético (Mix) por Estação")
                    cols_mix = st.columns(2)
                    
                    for i, est in enumerate(estacoes_desta_mg):
                        estado = dados_estacoes[est]["estado"]
                        estado_iso = dados_estacoes[est].get("estado_sem_transacao", estado)
                        
                        fig_mix = make_subplots(
                            rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                            subplot_titles=[f"{est} - Isolada", f"{est} - P2P"]
                        )
                        _add_perfil_estado(fig_mix, estado_iso, 1, 1, showlegend=False)
                        _add_perfil_estado(fig_mix, estado, 2, 1, showlegend=False)

                        fig_mix.update_layout(
                            font=dict(color="black", size=13, family="Arial, sans-serif"),
                            hovermode="x unified",
                            height=450,
                            margin=dict(l=20, r=20, t=40, b=20),
                            showlegend=False
                        )
                        for r in (1, 2):
                            fig_mix.update_yaxes(title_text="<b>kW</b>", title_font=dict(color="black", size=13), tickfont=dict(color="black", size=12), row=r, col=1)
                        fig_mix.update_xaxes(
                            title_text="<b>Hora</b>", title_font=dict(color="black", size=13),
                            tickmode="array", tickvals=list(range(0, 25, 4)), ticktext=[f"{h:02d}:00" for h in range(0, 25, 4)],
                            tickfont=dict(color="black", size=12), row=2, col=1
                        )
                        
                        with cols_mix[i % 2]:
                            st.plotly_chart(fig_mix, width='stretch', key=f"comp_mg_mix_{idx_tab}_{est}")

                    # --- MÉTRICAS COMPARATIVAS ---
                    st.markdown("#### Métricas Comparativas")
                    cols_met = st.columns(len(estacoes_desta_mg))
                    for idx_e, est in enumerate(estacoes_desta_mg):
                        d = dados_estacoes[est]
                        with cols_met[idx_e]:
                            st.markdown(f"**{est}**")
                            st.metric("Economia", f"R$ {d['economia']:,.2f}")

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
    st.header("Otimização Pós-Dia")
    st.markdown(
        "Desloca cargas flexíveis (prioridade 2 e 3) para horários mais baratos "
        "e otimiza o uso de geradores. A otimização é aplicada **por estação**."
    )

    st.markdown("##### Métodos incluídos na comparação completa")
    st.caption(
        "**Regras** e **MILP Local + Refino** sempre rodam nos cenários Isolado e P2P. "
        "**MILP Local** = só o MILP por microrrede, sem a busca greedy de refinamento. "
        "**MILP Centralizado** = um único MILP com todas as MGs e as trocas P2P "
        "(só existe no cenário P2P: sem trocas ele se decompõe nos MILPs locais). "
        "Atenção: cada chamada ao solver CBC tem limite de 600 s."
    )
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        incluir_milp_puro = st.checkbox(
            "Incluir MILP Local (sem refinamento) — Isolado e P2P",
            value=True, key="m3_inc_milp_puro",
        )
    with col_opt2:
        incluir_milp_central = st.checkbox(
            "Incluir MILP Centralizado — P2P",
            value=True, key="m3_inc_milp_central",
        )

    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        otimizar_heuristica = st.button(
            "Otimização por Regras", type="secondary",
            width='stretch', key="saz_otm_heur",
        )
    with col_btn2:
        otimizar_milp = st.button(
            "Otimização MILP", type="secondary",
            width='stretch', key="saz_otm_milp",
        )
    with col_btn3:
        comparar_todos = st.button(
            "Comparar Todos os Métodos", type="primary",
            width='stretch', key="saz_otm_comp_todos",
        )

    otimizar = otimizar_heuristica or otimizar_milp

    def _mgs_frescas_estacao(estacao):
        """
        Recarrega as MGs da estação e reaplica as MESMAS modificações sazonais
        usadas na simulação base (curva solar da estação e fator de carga).

        Retorna cópias Pydantic desacopladas da sessão SQLAlchemy. Assim:
        - todos os otimizadores partem exatamente do cenário que gerou o
          resultado original (antes, o rollback descartava a curva sazonal);
        - a leitura do banco fica FORA do tempo medido de cada método.
        """
        mgs_por_est = st.session_state.get("m3_mgs_por_estacao", {})
        curvas = resultados_sazonais[estacao].get("curvas_solares", {})
        fator = st.session_state.get("m3_fatores_carga", {}).get(estacao, 0.0)
        copias = []
        with _crud.session.no_autoflush:
            for mg_ref in mgs_por_est.get(estacao, []):
                mg = Ler_Objeto(Microrrede, mg_ref.id)
                if mg.id in curvas and mg.solar:
                    mg.solar.curva_geracao = json.dumps(np.asarray(curvas[mg.id]).tolist())
                if fator != 0.0 and mg.carga:
                    for carga_fixa in mg.carga.cargaFixa:
                        carga_fixa.potencia = carga_fixa.potencia * (1 + fator)
                copias.append(MicrorredeSchema.model_validate(mg))
        _crud.session.rollback()
        return copias

    if comparar_todos:
        from mercado.simulacao_simultanea import (
            OtimizadorPosDia, OtimizadorMILPPosDia, OtimizadorMILPCentralizadoPosDia,
        )
        start_comparacao = time.perf_counter()
        comp_otm_sazonais = {}
        erros_comp = []
        status_otm = st.empty()

        for idx_est, estacao in enumerate(estacoes_simuladas):
            dados_est = resultados_sazonais[estacao]
            res_p2p_base = dados_est["resultado"]
            res_iso_base = dados_est["resultado_isolado"]

            cs = {
                "original": res_p2p_base,
                "original_iso": res_iso_base,
                "tempos": {
                    "original": {
                        "total": dados_est.get("tempo_sim_p2p", 0.0),
                        "simulacao_final": dados_est.get("tempo_sim_p2p", 0.0),
                        "n_simulacoes": 1, "n_milp": 0,
                    },
                    "original_iso": {
                        "total": dados_est.get("tempo_sim_iso", 0.0),
                        "simulacao_final": dados_est.get("tempo_sim_iso", 0.0),
                        "n_simulacoes": 1, "n_milp": 0,
                    },
                },
                "erros": {},
            }

            iso_kw = dict(simulador_cls=SimuladorSemTransacao)
            plano = [
                ("heuristica_iso", OtimizadorPosDia, res_iso_base, iso_kw),
            ]
            if incluir_milp_puro:
                plano.append(("milp_puro_iso", OtimizadorMILPPosDia, res_iso_base, dict(iso_kw, refinamento=False)))
            plano.append(("milp_iso", OtimizadorMILPPosDia, res_iso_base, iso_kw))
            plano.append(("heuristica", OtimizadorPosDia, res_p2p_base, {}))
            if incluir_milp_puro:
                plano.append(("milp_puro", OtimizadorMILPPosDia, res_p2p_base, dict(refinamento=False)))
            plano.append(("milp", OtimizadorMILPPosDia, res_p2p_base, {}))
            if incluir_milp_central:
                plano.append(("milp_central", OtimizadorMILPCentralizadoPosDia, res_p2p_base, {}))

            for chave, cls_otm, base, kwargs in plano:
                rotulo = _rotulo_metodo(chave)
                status_otm.info(f"{estacao} ({idx_est + 1}/{len(estacoes_simuladas)}) — {rotulo}...")

                def callback_otm(msg, _e=estacao, _r=rotulo):
                    status_otm.info(f"{_e} — {_r}: {msg}")

                # Leitura do BD fora do cronômetro
                mgs_metodo = _mgs_frescas_estacao(estacao)
                otm = cls_otm(
                    microrredes=mgs_metodo, config=config,
                    margem_venda=margem, coef_perda_km=coef_perda, **kwargs,
                )
                t0 = time.perf_counter()
                try:
                    res_m = otm.otimizar(base, callback=callback_otm)
                except Exception as exc:  # noqa: BLE001 — registra e segue p/ os demais métodos
                    cs["erros"][chave] = str(exc)
                    erros_comp.append(f"{estacao} — {rotulo}: {exc}")
                    continue
                t_parede = time.perf_counter() - t0

                tempos_m = dict(res_m.get("tempos", {}))
                tempos_m["parede"] = t_parede
                tempos_m.setdefault("total", t_parede)
                cs[chave] = res_m
                cs["tempos"][chave] = tempos_m

            comp_otm_sazonais[estacao] = cs

        st.session_state["m3_comparacao_otm_sazonais"] = comp_otm_sazonais
        if "m3_resultados_otm_sazonais" in st.session_state:
            del st.session_state["m3_resultados_otm_sazonais"]
        st.session_state["m3_tempo_comparacao_total"] = time.perf_counter() - start_comparacao
        if erros_comp:
            status_otm.warning("Comparação concluída com falhas:\n\n- " + "\n- ".join(erros_comp))
        else:
            status_otm.success("Comparação concluída!")

    if otimizar:
        from mercado.simulacao_simultanea import OtimizadorPosDia, OtimizadorMILPPosDia
        start_otimizacao = time.perf_counter()
        cls_otm_ind = OtimizadorMILPPosDia if otimizar_milp else OtimizadorPosDia
        metodo_ind = "MILP Local + Refino" if otimizar_milp else "Regras"
        tempos_ind = {}

        resultados_otm_sazonais = {}
        status_otm = st.empty()

        for idx_est, estacao in enumerate(estacoes_simuladas):
            status_otm.info(
                f"Otimizando {estacao} "
                f"({idx_est + 1}/{len(estacoes_simuladas)})..."
            )

            resultado_est = resultados_sazonais[estacao]["resultado"]
            resultado_isolado = resultados_sazonais[estacao]["resultado_isolado"]

            def callback_otm(msg, _e=estacao):
                status_otm.info(f"{_e}: {msg}")

            otimizador = cls_otm_ind(
                microrredes=_mgs_frescas_estacao(estacao),
                config=config,
                margem_venda=margem,
                coef_perda_km=coef_perda,
            )
            otimizador_iso = cls_otm_ind(
                microrredes=_mgs_frescas_estacao(estacao),
                config=config,
                margem_venda=margem,
                coef_perda_km=coef_perda,
                simulador_cls=SimuladorSemTransacao,
            )

            # Tempos medidos separadamente para P2P e Isolado
            t0 = time.perf_counter()
            resultado_otm = otimizador.otimizar(resultado_est, callback=callback_otm)
            t_p2p = time.perf_counter() - t0
            t0 = time.perf_counter()
            resultado_otm_iso = otimizador_iso.otimizar(resultado_isolado, callback=callback_otm)
            t_iso = time.perf_counter() - t0
            tempos_ind[estacao] = {"P2P": t_p2p, "Isolado": t_iso}

            resultados_otm_sazonais[estacao] = {
                "p2p": resultado_otm,
                "iso": resultado_otm_iso,
            }

        st.session_state["m3_resultados_otm_sazonais"] = resultados_otm_sazonais
        st.session_state["m3_tempos_otim_individual"] = tempos_ind
        st.session_state["m3_metodo_otim_individual"] = metodo_ind
        st.session_state["m3_tempo_otim_individual"] = sum(
            v["P2P"] + v["Isolado"] for v in tempos_ind.values()
        )
        st.session_state["m3_tempo_otimizacao_total"] = time.perf_counter() - start_otimizacao
        status_otm.success("Otimização concluída para todas as estações!")

    # Exibe resultados da otimização
    if "m3_resultados_otm_sazonais" in st.session_state:
        resultados_otm_sazonais = st.session_state["m3_resultados_otm_sazonais"]

        st.subheader("Resultados da Otimização por Estação")

        # --- RESUMO GLOBAL DA OTIMIZAÇÃO ---
        dados_resumo_otm = []
        for estacao in estacoes_simuladas:
            if estacao not in resultados_otm_sazonais:
                continue
            res_otm = resultados_otm_sazonais[estacao]["p2p"]
            res_otm_iso = resultados_otm_sazonais[estacao]["iso"]
            
            res_orig = res_otm["original"]
            res_otim = res_otm["otimizado"]
            custo_antes = sum(res_orig.custo_total_por_mg.values())
            custo_depois = sum(res_otim.custo_total_por_mg.values())
            economia_otm = custo_antes - custo_depois
            
            res_orig_iso = res_otm_iso["original"]
            res_otim_iso = res_otm_iso["otimizado"]
            custo_antes_iso = sum(res_orig_iso.custo_total_por_mg.values())
            custo_depois_iso = sum(res_otim_iso.custo_total_por_mg.values())
            
            dados_resumo_otm.append({
                "Estação": f"{estacao}",
                "Custo Antes Iso (R$)": custo_antes_iso,
                "Custo Depois Iso (R$)": custo_depois_iso,
                "Custo Antes P2P (R$)": custo_antes,
                "Custo Depois P2P (R$)": custo_depois,
                "Economia Otm P2P (R$)": economia_otm,
                "Economia Otm P2P (%)": (economia_otm / custo_antes * 100) if custo_antes > 0 else 0,
                "Cargas Movidas P2P": len(res_otm.get("cargas_movidas", [])),
            })

        if dados_resumo_otm:
            df_resumo_otm = pd.DataFrame(dados_resumo_otm)
            st.dataframe(
                df_resumo_otm.style.format({
                    "Custo Antes Iso (R$)": "R$ {:,.2f}",
                    "Custo Depois Iso (R$)": "R$ {:,.2f}",
                    "Custo Antes P2P (R$)": "R$ {:,.2f}",
                    "Custo Depois P2P (R$)": "R$ {:,.2f}",
                    "Economia Otm P2P (R$)": "R$ {:,.2f}",
                    "Economia Otm P2P (%)": "{:.1f}%",
                    "Cargas Movidas P2P": "{:,}",
                }),
                width='stretch',
                hide_index=True,
            )

        st.divider()

        # --- DETALHES POR ESTAÇÃO ---
        tabs_otm = st.tabs(
            [f"{e}" for e in estacoes_simuladas if e in resultados_otm_sazonais]
        )

        for idx_est, estacao in enumerate([e for e in estacoes_simuladas if e in resultados_otm_sazonais]):
            with tabs_otm[idx_est]:
                res_otm = resultados_otm_sazonais[estacao]["p2p"]
                res_orig = res_otm["original"]
                res_otim = res_otm["otimizado"]
                nomes_otm = list(res_orig.custo_total_por_mg.keys())

                res_otm_iso = resultados_otm_sazonais[estacao]["iso"]
                res_orig_iso = res_otm_iso["original"]
                res_otim_iso = res_otm_iso["otimizado"]
                
                # Métricas globais
                custo_antes = sum(res_orig.custo_total_por_mg.values())
                custo_depois = sum(res_otim.custo_total_por_mg.values())
                economia_otm = custo_antes - custo_depois
                
                custo_antes_iso = sum(res_orig_iso.custo_total_por_mg.values())
                custo_depois_iso = sum(res_otim_iso.custo_total_por_mg.values())

                c1o, c2o, c3o, c4o, c5o = st.columns(5)
                c1o.metric("Custo Antes (Iso)", f"R$ {custo_antes_iso:,.2f}")
                c2o.metric("Custo Depois (Iso)", f"R$ {custo_depois_iso:,.2f}")
                c3o.metric("Custo Antes (P2P)", f"R$ {custo_antes:,.2f}")
                c4o.metric("Custo Depois (P2P)", f"R$ {custo_depois:,.2f}")
                c5o.metric(
                    "Economia P2P",
                    f"R$ {economia_otm:,.2f}",
                    f"{(economia_otm / custo_antes * 100):.1f}%" if custo_antes > 0 else "0%",
                )

                st.divider()

                # Tabela comparativa por MG
                st.markdown("#### Comparação por Microrrede")
                df_comp_otm = pd.DataFrame({
                    "Microrrede": nomes_otm,
                    "Antes Iso (R$)": [res_orig_iso.custo_total_por_mg[n] for n in nomes_otm],
                    "Depois Iso (R$)": [res_otim_iso.custo_total_por_mg[n] for n in nomes_otm],
                    "Antes P2P (R$)": [res_orig.custo_total_por_mg[n] for n in nomes_otm],
                    "Depois P2P (R$)": [res_otim.custo_total_por_mg[n] for n in nomes_otm],
                })
                
                st.dataframe(
                    df_comp_otm.style.format({
                        "Antes Iso (R$)": "R$ {:,.2f}",
                        "Depois Iso (R$)": "R$ {:,.2f}",
                        "Antes P2P (R$)": "R$ {:,.2f}",
                        "Depois P2P (R$)": "R$ {:,.2f}",
                    }),
                    width='stretch', hide_index=True
                )

                # Gráfico comparativo
                fig_otm = px.bar(
                    df_comp_otm,
                    x="Microrrede",
                    y=["Antes Iso (R$)", "Depois Iso (R$)", "Antes P2P (R$)", "Depois P2P (R$)"],
                    barmode="group",
                    text_auto=".2s",
                    color_discrete_map={
                        "Antes Iso (R$)": "#EF553B",
                        "Depois Iso (R$)": "#FFA15A",
                        "Antes P2P (R$)": "#00CC96",
                        "Depois P2P (R$)": "#19D3F3",
                    },
                )
                fig_otm.update_layout(
                    font=dict(color="black", size=14, family="Arial, sans-serif"),
                    yaxis=dict(
                        title=dict(text="<b>Custo (R$)</b>", font=dict(color="black", size=14)),
                        tickfont=dict(color="black", size=13),
                    ),
                    xaxis=dict(
                        tickfont=dict(color="black", size=13),
                    ),
                    legend=dict(font=dict(color="black", size=13)),
                    height=400
                )
                st.plotly_chart(fig_otm, width='stretch', key=f"saz_otm_custos_{estacao}")

                st.divider()

                # Cargas movidas
                if res_otm.get("cargas_movidas"):
                    st.markdown("#### Cargas Deslizadas")
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
                st.subheader("Fluxo de Energia P2P Pós-Otimização")
                
                fluxos_otm = {}
                for t in res_otim.trades:
                    key = (t.vendedor_nome, t.comprador_nome)
                    fluxos_otm[key] = fluxos_otm.get(key, 0.0) + (t.energia_enviada_kw / 60)
                
                if fluxos_otm:
                    nomes_unicos_otm = list(set([k[0] for k in fluxos_otm] + [k[1] for k in fluxos_otm]))
                    idx_nome_otm = {n: i for i, n in enumerate(nomes_unicos_otm)}
                    
                    fig_sankey_otm = go.Figure(data=[go.Sankey(
                        node=dict(
                            pad=25,
                            thickness=35,
                            line=dict(color="black", width=2),
                            label=[f"<b>{n}</b>" for n in nomes_unicos_otm],
                            color=["#4A90E2", "#50E3C2", "#F5A623", "#E3507A", "#9013FE", "#7ED321"][:len(nomes_unicos_otm)]
                        ),
                        link=dict(
                            source=[idx_nome_otm[k[0]] for k in fluxos_otm],
                            target=[idx_nome_otm[k[1]] for k in fluxos_otm],
                            value=list(fluxos_otm.values()),
                            color="rgba(160, 160, 160, 0.4)",
                            hovertemplate="<b>%{source.label} ➔ %{target.label}</b><br>Energia: %{value:,.2f} kWh<extra></extra>",
                        ),
                        textfont=dict(size=16, color="black", family="Arial Black, sans-serif"),
                    )])
                    fig_sankey_otm.update_layout(
                        font=dict(size=16, color="black", family="Arial Black, sans-serif"),
                        height=550,
                        margin=dict(l=30, r=30, t=35, b=30)
                    )
                    st.plotly_chart(fig_sankey_otm, width='stretch', key=f"saz_sankey_otm_{estacao}")
                else:
                    st.info("Não houve transações P2P neste cenário otimizado.")

                st.divider()

                # Perfis energéticos pós-otimização
                st.markdown("#### Perfil Energético Pós-Otimização")

                tabs_mg_otm = st.tabs([str(n) for n in nomes_otm])

                for idx_mg, nome in enumerate(nomes_otm):
                    with tabs_mg_otm[idx_mg]:
                        est_otm = res_otim.estados[nome]
                        est_otm_iso = res_otim_iso.estados[nome]
                        horas = np.arange(1440) / 60

                        fig_perfil_otm = make_subplots(
                            rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.10,
                            subplot_titles=[
                                f"Operação Isolada (Otimizada) — {nome} ({estacao})",
                                f"Com Mercado P2P (Otimizado) — {nome} ({estacao})",
                            ],
                        )
                        _add_perfil_estado(fig_perfil_otm, est_otm_iso, 1, 1, showlegend=True)
                        _add_perfil_estado(fig_perfil_otm, est_otm, 2, 1, showlegend=False)

                        # Garante legenda
                        nomes_leg = {tr.name for tr in fig_perfil_otm.data if tr.showlegend}
                        for tr in fig_perfil_otm.data:
                            if tr.name not in nomes_leg:
                                tr.showlegend = True
                                nomes_leg.add(tr.name)

                        fig_perfil_otm.update_layout(
                            font=dict(color="black", size=14, family="Arial, sans-serif"),
                            height=650,
                            hovermode="x unified",
                            legend=dict(font=dict(color="black", size=13)),
                        )
                        for annotation in fig_perfil_otm['layout']['annotations']:
                            annotation['font'] = dict(size=16, color='black', family="Arial, sans-serif")
                        fig_perfil_otm.update_xaxes(_XAXIS_HORAS, row=2, col=1)
                        for r in (1, 2):
                            fig_perfil_otm.update_yaxes(
                                title_text="<b>Potência (kW)</b>",
                                title_font=dict(color="black", size=14),
                                tickfont=dict(color="black", size=13),
                                row=r, col=1,
                            )
                        st.plotly_chart(
                            fig_perfil_otm, width='stretch',
                            key=f"saz_otm_perfil_{estacao}_{idx_mg}",
                        )

                        # --- NÍVEIS DE ARMAZENAMENTO (PÓS-OTIMIZAÇÃO, separados) ---
                        st.markdown("##### Níveis de Armazenamento (Pós-Otimização)")

                        _xaxis_cfg_otm = dict(
                            title=dict(text="<b>Hora do Dia</b>", font=dict(color="black", size=14)),
                            tickfont=dict(color="black", size=13),
                            tickmode="array",
                            tickvals=list(range(0, 25, 2)),
                            ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
                        )

                        # Gráfico da Bateria
                        if est_otm.hist_nivel_bateria.sum() > 0 or est_otm_iso.hist_nivel_bateria.sum() > 0:
                            fig_bat_otm = go.Figure()
                            fig_bat_otm.add_trace(go.Scatter(
                                x=horas, y=est_otm_iso.hist_nivel_bateria, mode="lines", name="Operação Isolada",
                                line=dict(color=COR_SEM_TRANSACAO, width=2),
                            ))
                            fig_bat_otm.add_trace(go.Scatter(
                                x=horas, y=est_otm.hist_nivel_bateria, mode="lines", name="Com Mercado P2P",
                                line=dict(color=COR_COM_P2P, width=2, dash="dash"),
                            ))
                            fig_bat_otm.update_layout(
                                title=dict(text=f"<b>Nível da Bateria (Otimizado) — {nome} ({estacao})</b>", font=dict(color="black", size=16)),
                                font=dict(color="black", size=14, family="Arial, sans-serif"),
                                yaxis=dict(
                                    title=dict(text="<b>Nível de Energia (kWh)</b>", font=dict(color="black", size=14)),
                                    tickfont=dict(color="black", size=13),
                                ),
                                xaxis=_xaxis_cfg_otm,
                                legend=dict(font=dict(color="black", size=13)),
                                hovermode="x unified",
                                height=300,
                            )
                            st.plotly_chart(fig_bat_otm, width='stretch', key=f"saz_otm_niv_bat_{estacao}_{idx_mg}")

                        # Gráfico de Diesel
                        if est_otm.hist_nivel_diesel.sum() > 0 or est_otm_iso.hist_nivel_diesel.sum() > 0:
                            fig_diesel_otm = go.Figure()
                            fig_diesel_otm.add_trace(go.Scatter(
                                x=horas, y=est_otm_iso.hist_nivel_diesel, mode="lines", name="Operação Isolada",
                                line=dict(color=COR_SEM_TRANSACAO, width=2),
                            ))
                            fig_diesel_otm.add_trace(go.Scatter(
                                x=horas, y=est_otm.hist_nivel_diesel, mode="lines", name="Com Mercado P2P",
                                line=dict(color=COR_COM_P2P, width=2, dash="dash"),
                            ))
                            _xaxis_cfg_otm_diesel = dict(
                                title=dict(text="<b>Tempo (h)</b>", font=dict(color="black", size=14)),
                                tickfont=dict(color="black", size=13),
                                tickmode="array",
                                tickvals=list(range(0, 25, 2)),
                                ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
                            )
                            fig_diesel_otm.update_layout(
                                title=dict(text=f"<b>Nível do Diesel (L x Tempo) — {nome}</b>", font=dict(color="black", size=16)),
                                font=dict(color="black", size=14, family="Arial, sans-serif"),
                                yaxis=dict(
                                    title=dict(text="<b>Volume (L)</b>", font=dict(color="black", size=14)),
                                    tickfont=dict(color="black", size=13),
                                ),
                                xaxis=_xaxis_cfg_otm_diesel,
                                legend=dict(font=dict(color="black", size=13)),
                                hovermode="x unified",
                                height=300,
                            )
                            st.plotly_chart(fig_diesel_otm, width='stretch', key=f"saz_otm_niv_diesel_{estacao}_{idx_mg}")

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
                            "Diesel Final",
                            f"{est_otm.hist_nivel_diesel[-1]:,.2f} L",
                        )
                        c5o.metric(
                            "Bateria Final",
                            f"{est_otm.hist_nivel_bateria[-1]:,.2f} kWh",
                        )


    if "m3_comparacao_otm_sazonais" in st.session_state:
        comp_sazonais = st.session_state["m3_comparacao_otm_sazonais"]
        st.divider()
        st.subheader("Comparação de Todos os Métodos (Regras, MILP, Isolado e P2P)")

        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        # ── RESUMO GLOBAL: TODOS OS MÉTODOS ──────────────────────────
        st.markdown(
            "Todos os métodos partem do **mesmo cenário sazonal**. A coluna "
            "**Econ. vs Sem Transação** usa o cenário isolado sem otimização como "
            "referência única, permitindo comparar diretamente métodos isolados e P2P. "
            "**Tempo Algoritmo** exclui leitura do banco e cópia das MGs; nas linhas "
            "*base* é o tempo da simulação do dia."
        )

        linhas_all = []
        for estacao in estacoes_simuladas:
            if estacao not in comp_sazonais:
                continue
            cs = comp_sazonais[estacao]
            tempos_cs = cs.get("tempos", {})
            ref_sem = sum(cs["original_iso"].custo_total_por_mg.values())
            for chave, rot, cen, cor, base in _metodos_disponiveis(cs):
                res_m = _res_metodo(cs, chave)
                base_cen = cs["original_iso"] if cen == "Isolado" else cs["original"]
                c_base_cen = sum(base_cen.custo_total_por_mg.values())
                custo = sum(res_m.custo_total_por_mg.values())
                tp = tempos_cs.get(chave, {})
                t_total = tp.get("total", float("nan"))
                linhas_all.append({
                    "Estação": estacao,
                    "chave": chave,
                    "Método": _rotulo_metodo(chave),
                    "Cenário": cen,
                    "Custo (R$)": custo,
                    "Econ. vs Base do Cenário (R$)": c_base_cen - custo,
                    "Econ. vs Sem Transação (R$)": ref_sem - custo,
                    "Econ. vs Sem Transação (%)": ((ref_sem - custo) / ref_sem * 100) if ref_sem > 0 else 0.0,
                    "Concessionária (kWh)": sum(_kwh(e.uso_concessionaria) for e in res_m.estados.values()),
                    "Volume P2P (kWh)": getattr(res_m, "volume_total_kwh", 0.0) if cen == "P2P" else 0.0,
                    "Cargas Movidas": len(_cargas_metodo(cs, chave)),
                    "Tempo Algoritmo (s)": t_total - tp.get("preparacao", 0.0),
                    "Tempo Total (s)": t_total,
                    "Simulações": int(tp.get("n_simulacoes", 0)),
                    "MILPs": int(tp.get("n_milp", 0)),
                })

            if cs.get("erros"):
                st.warning(
                    f"**{estacao}** — métodos que falharam: "
                    + "; ".join(f"{_rotulo_metodo(k)}: {v}" for k, v in cs["erros"].items())
                )

        fmt_all = {
            "Custo (R$)": "R$ {:,.2f}",
            "Econ. vs Base do Cenário (R$)": "R$ {:,.2f}",
            "Econ. vs Sem Transação (R$)": "R$ {:,.2f}",
            "Econ. vs Sem Transação (%)": "{:.1f}%",
            "Concessionária (kWh)": "{:,.1f}",
            "Volume P2P (kWh)": "{:,.1f}",
            "Cargas Movidas": "{:,}",
            "Tempo Algoritmo (s)": "{:,.2f}",
            "Tempo Total (s)": "{:,.2f}",
            "Simulações": "{:,}",
            "MILPs": "{:,}",
        }

        if linhas_all:
            df_all = pd.DataFrame(linhas_all)
            df_all["Ranking"] = (
                df_all.groupby("Estação")["Custo (R$)"].rank(method="min").astype(int)
            )
            ordem_chaves = [m[0] for m in METODOS_COMP]
            cores_metodo = {_rotulo_metodo(m[0]): m[3] for m in METODOS_COMP}

            # ── Consolidado (soma das estações) ───────────────────────
            st.markdown("#### Consolidado — Soma de Todas as Estações")
            df_cons = (
                df_all.groupby(["chave", "Método", "Cenário"], as_index=False)
                .agg({
                    "Custo (R$)": "sum",
                    "Econ. vs Base do Cenário (R$)": "sum",
                    "Econ. vs Sem Transação (R$)": "sum",
                    "Concessionária (kWh)": "sum",
                    "Volume P2P (kWh)": "sum",
                    "Cargas Movidas": "sum",
                    "Tempo Algoritmo (s)": "sum",
                    "Tempo Total (s)": "sum",
                    "Simulações": "sum",
                    "MILPs": "sum",
                })
            )
            ref_sem_total = df_cons.loc[df_cons["chave"] == "original_iso", "Custo (R$)"].sum()
            df_cons["Econ. vs Sem Transação (%)"] = (
                df_cons["Econ. vs Sem Transação (R$)"] / ref_sem_total * 100 if ref_sem_total > 0 else 0.0
            )
            df_cons["Ranking"] = df_cons["Custo (R$)"].rank(method="min").astype(int)
            # Velocidade relativa ao método por Regras do mesmo cenário
            t_regras = {
                "Isolado": df_cons.loc[df_cons["chave"] == "heuristica_iso", "Tempo Algoritmo (s)"].sum(),
                "P2P": df_cons.loc[df_cons["chave"] == "heuristica", "Tempo Algoritmo (s)"].sum(),
            }
            df_cons["Tempo / Regras (x)"] = [
                (t / t_regras[c]) if (t_regras.get(c, 0) > 0 and not k.startswith("original")) else float("nan")
                for t, c, k in zip(df_cons["Tempo Algoritmo (s)"], df_cons["Cenário"], df_cons["chave"])
            ]
            df_cons["_ord"] = df_cons["chave"].map({k: i for i, k in enumerate(ordem_chaves)})
            df_cons = df_cons.sort_values("_ord").drop(columns=["_ord"])

            st.dataframe(
                df_cons.drop(columns=["chave"]).style.format({**fmt_all, "Tempo / Regras (x)": "{:,.2f}x"}, na_rep="—")
                .highlight_min(subset=["Custo (R$)"], color="#C6F6D5")
                .highlight_min(subset=["Tempo Algoritmo (s)"], color="#BEE3F8"),
                width='stretch', hide_index=True,
            )

            melhor_cons = df_cons.loc[df_cons["Custo (R$)"].idxmin()]
            otim_cons = df_cons[~df_cons["chave"].str.startswith("original")]
            rapido_cons = otim_cons.loc[otim_cons["Tempo Algoritmo (s)"].idxmin()] if not otim_cons.empty else None
            cm1, cm2, cm3 = st.columns(3)
            cm1.metric("Menor Custo (todas as estações)", melhor_cons["Método"], f"R$ {melhor_cons['Custo (R$)']:,.2f}")
            cm2.metric(
                "Economia vs Sem Transação",
                f"R$ {melhor_cons['Econ. vs Sem Transação (R$)']:,.2f}",
                f"{melhor_cons['Econ. vs Sem Transação (%)']:.1f}%",
            )
            if rapido_cons is not None:
                cm3.metric("Otimizador Mais Rápido", rapido_cons["Método"], f"{rapido_cons['Tempo Algoritmo (s)']:,.2f} s")

            col_cg1, col_cg2 = st.columns(2)
            with col_cg1:
                fig_cons_custo = go.Figure(go.Bar(
                    x=df_cons["Método"], y=df_cons["Custo (R$)"],
                    marker_color=[cores_metodo.get(m, "#888") for m in df_cons["Método"]],
                    text=[f"R$ {v:,.2f}" for v in df_cons["Custo (R$)"]],
                    textposition="auto", textfont=dict(color="black", size=12),
                ))
                fig_cons_custo.update_layout(
                    title=dict(text="<b>Custo Total por Método</b>", font=dict(color="black", size=16)),
                    font=dict(color="black", size=13, family="Arial, sans-serif"),
                    yaxis=dict(title=dict(text="<b>Custo (R$)</b>", font=dict(color="black", size=14)), tickfont=dict(color="black", size=12)),
                    xaxis=dict(tickfont=dict(color="black", size=11), tickangle=-30),
                    height=450, showlegend=False,
                )
                st.plotly_chart(fig_cons_custo, width='stretch', key="m3_all_cons_custo")
            with col_cg2:
                fig_cons_t = go.Figure(go.Bar(
                    x=df_cons["Método"], y=df_cons["Tempo Algoritmo (s)"],
                    marker_color=[cores_metodo.get(m, "#888") for m in df_cons["Método"]],
                    text=[f"{v:,.2f} s" for v in df_cons["Tempo Algoritmo (s)"]],
                    textposition="auto", textfont=dict(color="black", size=12),
                ))
                fig_cons_t.update_layout(
                    title=dict(text="<b>Tempo de Execução por Método (escala log)</b>", font=dict(color="black", size=16)),
                    font=dict(color="black", size=13, family="Arial, sans-serif"),
                    yaxis=dict(type="log", title=dict(text="<b>Tempo (s)</b>", font=dict(color="black", size=14)), tickfont=dict(color="black", size=12)),
                    xaxis=dict(tickfont=dict(color="black", size=11), tickangle=-30),
                    height=450, showlegend=False,
                )
                st.plotly_chart(fig_cons_t, width='stretch', key="m3_all_cons_tempo")

            # Custo x Tempo (fronteira custo-benefício)
            fig_ct = go.Figure()
            for _, row in df_cons.iterrows():
                fig_ct.add_trace(go.Scatter(
                    x=[max(row["Tempo Algoritmo (s)"], 1e-3)], y=[row["Custo (R$)"]],
                    mode="markers+text", name=row["Método"],
                    text=[row["Método"]], textposition="top center",
                    marker=dict(size=16, color=cores_metodo.get(row["Método"], "#888"),
                                symbol="circle" if row["Cenário"] == "P2P" else "diamond",
                                line=dict(color="black", width=1)),
                ))
            fig_ct.update_layout(
                title=dict(text="<b>Custo x Tempo de Execução</b> (◆ Isolado, ● P2P)", font=dict(color="black", size=16)),
                font=dict(color="black", size=13, family="Arial, sans-serif"),
                xaxis=dict(type="log", title=dict(text="<b>Tempo do Algoritmo (s, log)</b>", font=dict(color="black", size=14)), tickfont=dict(color="black", size=12)),
                yaxis=dict(title=dict(text="<b>Custo Total (R$)</b>", font=dict(color="black", size=14)), tickfont=dict(color="black", size=12)),
                height=500, showlegend=False,
            )
            st.plotly_chart(fig_ct, width='stretch', key="m3_all_custo_tempo")

            # ── Por estação ───────────────────────────────────────────
            st.markdown("#### Todos os Métodos por Estação")
            st.dataframe(
                df_all.drop(columns=["chave"]).style.format(fmt_all, na_rep="—"),
                width='stretch', hide_index=True,
            )

            # Melhor método por estação
            linhas_best = []
            for estacao in df_all["Estação"].unique():
                d = df_all[df_all["Estação"] == estacao]
                d_iso = d[d["Cenário"] == "Isolado"]
                d_p2p = d[d["Cenário"] == "P2P"]
                d_otm = d[~d["chave"].str.startswith("original")]
                b = d.loc[d["Custo (R$)"].idxmin()]
                bi = d_iso.loc[d_iso["Custo (R$)"].idxmin()]
                bp = d_p2p.loc[d_p2p["Custo (R$)"].idxmin()]
                rp = d_otm.loc[d_otm["Tempo Algoritmo (s)"].idxmin()] if not d_otm.empty else None
                linhas_best.append({
                    "Estação": estacao,
                    "Melhor Geral": b["Método"],
                    "Custo Melhor (R$)": b["Custo (R$)"],
                    "Melhor Isolado": bi["Método"],
                    "Custo Isolado (R$)": bi["Custo (R$)"],
                    "Melhor P2P": bp["Método"],
                    "Custo P2P (R$)": bp["Custo (R$)"],
                    "Ganho P2P vs Isolado (R$)": bi["Custo (R$)"] - bp["Custo (R$)"],
                    "Otimizador Mais Rápido": rp["Método"] if rp is not None else "—",
                    "Tempo (s)": rp["Tempo Algoritmo (s)"] if rp is not None else float("nan"),
                })
            st.markdown("##### Melhor Método por Estação")
            st.dataframe(
                pd.DataFrame(linhas_best).style.format({
                    "Custo Melhor (R$)": "R$ {:,.2f}",
                    "Custo Isolado (R$)": "R$ {:,.2f}",
                    "Custo P2P (R$)": "R$ {:,.2f}",
                    "Ganho P2P vs Isolado (R$)": "R$ {:,.2f}",
                    "Tempo (s)": "{:,.2f}",
                }, na_rep="—"),
                width='stretch', hide_index=True,
            )

            col_eg1, col_eg2 = st.columns(2)
            with col_eg1:
                fig_est_c = go.Figure()
                for chave in ordem_chaves:
                    d = df_all[df_all["chave"] == chave]
                    if d.empty:
                        continue
                    rot = _rotulo_metodo(chave)
                    fig_est_c.add_trace(go.Bar(
                        name=rot, x=d["Estação"], y=d["Custo (R$)"],
                        marker_color=cores_metodo.get(rot, "#888"),
                        hovertemplate=f"<b>{rot}</b><br>%{{x}}: R$ %{{y:,.2f}}<extra></extra>",
                    ))
                fig_est_c.update_layout(
                    title=dict(text="<b>Custo por Estação e Método</b>", font=dict(color="black", size=16)),
                    font=dict(color="black", size=13, family="Arial, sans-serif"),
                    barmode="group", height=480,
                    yaxis=dict(title=dict(text="<b>Custo (R$)</b>", font=dict(color="black", size=14)), tickfont=dict(color="black", size=12)),
                    xaxis=dict(tickfont=dict(color="black", size=13)),
                    legend=dict(font=dict(color="black", size=11)),
                )
                st.plotly_chart(fig_est_c, width='stretch', key="m3_all_est_custo")
            with col_eg2:
                fig_est_t = go.Figure()
                for chave in ordem_chaves:
                    if chave.startswith("original"):
                        continue
                    d = df_all[df_all["chave"] == chave]
                    if d.empty:
                        continue
                    rot = _rotulo_metodo(chave)
                    fig_est_t.add_trace(go.Bar(
                        name=rot, x=d["Estação"], y=d["Tempo Algoritmo (s)"],
                        marker_color=cores_metodo.get(rot, "#888"),
                        hovertemplate=f"<b>{rot}</b><br>%{{x}}: %{{y:,.2f}} s<extra></extra>",
                    ))
                fig_est_t.update_layout(
                    title=dict(text="<b>Tempo por Estação e Método (log)</b>", font=dict(color="black", size=16)),
                    font=dict(color="black", size=13, family="Arial, sans-serif"),
                    barmode="group", height=480,
                    yaxis=dict(type="log", title=dict(text="<b>Tempo (s)</b>", font=dict(color="black", size=14)), tickfont=dict(color="black", size=12)),
                    xaxis=dict(tickfont=dict(color="black", size=13)),
                    legend=dict(font=dict(color="black", size=11)),
                )
                st.plotly_chart(fig_est_t, width='stretch', key="m3_all_est_tempo")

        st.divider()


        # ── DETALHES POR ESTAÇÃO ─────────────────────────────────────
        est_comp = [e for e in estacoes_simuladas if e in comp_sazonais]
        if est_comp:
            tabs_comp = st.tabs([f"{e}" for e in est_comp])

            for idx_est, estacao in enumerate(est_comp):
                with tabs_comp[idx_est]:
                    cs = comp_sazonais[estacao]
                    res_orig = cs["original"]
                    res_heur = cs["heuristica"]["otimizado"]
                    res_milp = cs["milp"]["otimizado"]
                    nomes_mg = list(res_orig.custo_total_por_mg.keys())

                    # ── Métricas dinâmicas de todos os métodos ─────────────────
                    metodos_est = _metodos_disponiveis(cs)
                    custos_met = {}
                    for chave, rot, cen, cor, base in metodos_est:
                        r = _res_metodo(cs, chave)
                        if r is not None and hasattr(r, "custo_total_por_mg"):
                            custos_met[(chave, rot, cen)] = sum(r.custo_total_por_mg.values())

                    c_orig_iso = custos_met.get(("original_iso", "Sem Transação", "Isolado"), 0.0)
                    c_orig_p2p = custos_met.get(("original", "Original", "P2P"), 0.0)

                    # Top cards
                    if custos_met:
                        melhor_chave_tuple = min(custos_met, key=custos_met.get)
                        melhor_custo = custos_met[melhor_chave_tuple]
                        melhor_rotulo = f"{melhor_chave_tuple[1]} ({melhor_chave_tuple[2]})"

                        cols_m = st.columns(min(len(custos_met), 5))
                        # Mostrar principais: Sem Transação, Base P2P, e o Vencedor
                        if len(cols_m) >= 4:
                            cols_m[0].metric("Sem Transação (Base)", f"R$ {c_orig_iso:,.2f}")
                            cols_m[1].metric("P2P Sem Otimização", f"R$ {c_orig_p2p:,.2f}", f"R$ {c_orig_p2p - c_orig_iso:,.2f}")
                            cols_m[2].metric("🏆 Menor Custo da Estação", melhor_rotulo, f"R$ {melhor_custo:,.2f}")
                            econ_max = c_orig_iso - melhor_custo
                            cols_m[3].metric("Maior Economia vs Base", f"R$ {econ_max:,.2f}", f"{(econ_max/c_orig_iso*100) if c_orig_iso > 0 else 0:.1f}%")

                    st.divider()

                    # ── Tabela comparativa por MG (Todos os Métodos) ───────
                    st.markdown("#### Comparação por Microrrede — Todos os Métodos")
                    colunas_comp_mg = {"Microrrede": nomes_mg}
                    formatos_comp_mg = {}
                    for chave, rot, cen, cor, base in metodos_est:
                        r = _res_metodo(cs, chave)
                        if r is not None and hasattr(r, "custo_total_por_mg"):
                            col_nome = f"{rot} ({cen})"
                            colunas_comp_mg[col_nome] = [
                                r.custo_total_por_mg.get(n, float("nan"))
                                for n in nomes_mg
                            ]
                            formatos_comp_mg[col_nome] = "R$ {:,.2f}"

                    df_comp_mg = pd.DataFrame(colunas_comp_mg)
                    st.dataframe(
                        df_comp_mg.style.format(formatos_comp_mg, na_rep="—"),
                        width='stretch', hide_index=True
                    )

                    # Gráfico de barras por MG (Todos os Métodos)
                    fig_mg = go.Figure()
                    for chave, rot, cen, cor, base in metodos_est:
                        r = _res_metodo(cs, chave)
                        if r is not None and hasattr(r, "custo_total_por_mg"):
                            valores = [r.custo_total_por_mg.get(n, 0.0) for n in nomes_mg]
                            fig_mg.add_trace(go.Bar(
                                name=f"{rot} ({cen})",
                                x=nomes_mg,
                                y=valores,
                                marker_color=cor,
                                text=[f"R$ {v:,.2f}" for v in valores],
                                textposition='auto',
                                textfont=dict(color="black", size=11),
                            ))

                    fig_mg.update_layout(
                        font=dict(color="black", size=13, family="Arial, sans-serif"),
                        barmode='group',
                        yaxis=dict(
                            title=dict(text="<b>Custo (R$)</b>", font=dict(color="black", size=14)),
                            tickfont=dict(color="black", size=12),
                        ),
                        xaxis=dict(tickfont=dict(color="black", size=12)),
                        legend=dict(font=dict(color="black", size=11), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        height=480,
                        title=dict(text=f"<b>Custo por Microrrede — {estacao}</b>", font=dict(color="black", size=16))
                    )
                    st.plotly_chart(fig_mg, width='stretch', key=f"comp_mg_{estacao}")

                    st.divider()

                    # ── Cargas Deslizadas por Método ───────────────────
                    st.markdown("#### Cargas Deslizadas por Método")
                    metodos_com_cargas = []
                    for chave, rot, cen, cor, base in metodos_est:
                        cargas = _cargas_metodo(cs, chave)
                        if cargas:
                            metodos_com_cargas.append((f"{rot} ({cen})", cargas))

                    if metodos_com_cargas:
                        cols_cargas = st.columns(len(metodos_com_cargas))
                        for idx_c, (rot_c, cargas_c) in enumerate(metodos_com_cargas):
                            with cols_cargas[idx_c]:
                                st.markdown(f"**{rot_c}** ({len(cargas_c)} cargas)")
                                df_c = pd.DataFrame(cargas_c)
                                if len(df_c.columns) >= 5:
                                    df_c.columns = ["Microrrede", "Carga", "De", "Para", "Dur (min)"]
                                st.dataframe(df_c, width='stretch', hide_index=True)
                    else:
                        st.info("Nenhuma carga foi deslizada pelos otimizadores nesta estação.")

                    st.divider()

                    # ── Diagramas Sankey de todos os Métodos P2P ───────
                    st.markdown("#### Fluxo de Energia P2P")

                    def _make_sankey(trades, title, key):
                        fluxos = {}
                        for t in trades:
                            k = (t.vendedor_nome, t.comprador_nome)
                            fluxos[k] = fluxos.get(k, 0.0) + (t.energia_enviada_kw / 60)
                        if fluxos:
                            nomes_u = list(set([k[0] for k in fluxos] + [k[1] for k in fluxos]))
                            idx_n = {n: i for i, n in enumerate(nomes_u)}
                            cores = ["#4A90E2", "#50E3C2", "#F5A623", "#E3507A", "#9013FE", "#7ED321"]
                            fig = go.Figure(data=[go.Sankey(
                                node=dict(
                                    pad=25,
                                    thickness=35,
                                    line=dict(color="black", width=2),
                                    label=[f"<b>{n}</b>" for n in nomes_u],
                                    color=cores[:len(nomes_u)]
                                ),
                                link=dict(
                                    source=[idx_n[k[0]] for k in fluxos],
                                    target=[idx_n[k[1]] for k in fluxos],
                                    value=list(fluxos.values()),
                                    color="rgba(160, 160, 160, 0.4)",
                                    hovertemplate="<b>%{source.label} ➔ %{target.label}</b><br>Energia: %{value:,.2f} kWh<extra></extra>",
                                ),
                                textfont=dict(size=14, color="black", family="Arial Black, sans-serif"),
                            )])
                            fig.update_layout(
                                title=dict(text=f"<b>{title}</b>", font=dict(size=16, color="black", family="Arial Black, sans-serif")),
                                font=dict(size=14, color="black", family="Arial Black, sans-serif"),
                                height=480,
                                margin=dict(l=20, r=20, t=40, b=20)
                            )
                            st.plotly_chart(fig, width='stretch', key=key)
                        else:
                            st.info(f"Sem transações P2P ({title})")

                    metodos_com_trades = []
                    for chave, rot, cen, cor, base in metodos_est:
                        if cen == "P2P":
                            r = _res_metodo(cs, chave)
                            if r is not None and hasattr(r, "trades") and r.trades:
                                metodos_com_trades.append((f"{rot}", r.trades, f"comp_sankey_{chave}_{estacao}"))

                    if metodos_com_trades:
                        cols_sankey = st.columns(min(len(metodos_com_trades), 4))
                        for idx_s, (nome_s, trades_s, key_s) in enumerate(metodos_com_trades):
                            with cols_sankey[idx_s % len(cols_sankey)]:
                                _make_sankey(trades_s, nome_s, key_s)

                    st.divider()

                    # ── Perfis Energéticos por MG ─────────────────────
                    st.markdown("#### Perfil Energético (Comparativo)")

                    tabs_mg_comp = st.tabs([str(n) for n in nomes_mg])

                    for idx_mg, nome in enumerate(nomes_mg):
                        with tabs_mg_comp[idx_mg]:
                            horas = np.arange(1440) / 60
                            _xaxis_cfg = dict(
                                title=dict(text="<b>Hora do Dia</b>", font=dict(color="black", size=14)),
                                tickfont=dict(color="black", size=13),
                                tickmode="array",
                                tickvals=list(range(0, 25, 2)),
                                ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
                            )

                            def _add_perfil(fig, est, row, col):
                                fig.add_trace(go.Scatter(x=horas, y=est.uso_solar, mode="lines", name="Solar",
                                    line=dict(width=0), stackgroup=f"uso_{row}", fillcolor="rgba(255,215,0,0.6)",
                                    showlegend=(row == 1)), row=row, col=col)
                                fig.add_trace(go.Scatter(x=horas, y=est.uso_bateria, mode="lines", name="Bateria",
                                    line=dict(width=0), stackgroup=f"uso_{row}", fillcolor="rgba(50,205,50,0.6)",
                                    showlegend=(row == 1)), row=row, col=col)
                                fig.add_trace(go.Scatter(x=horas, y=est.uso_diesel, mode="lines", name="Diesel",
                                    line=dict(width=0), stackgroup=f"uso_{row}", fillcolor="rgba(169,169,169,0.6)",
                                    showlegend=(row == 1)), row=row, col=col)
                                fig.add_trace(go.Scatter(x=horas, y=est.uso_concessionaria, mode="lines", name="Concess.",
                                    line=dict(width=0), stackgroup=f"uso_{row}", fillcolor="rgba(65,105,225,0.6)",
                                    showlegend=(row == 1)), row=row, col=col)
                                fig.add_trace(go.Scatter(x=horas, y=est.energia_comprada, mode="lines", name="Compra P2P",
                                    line=dict(width=0), stackgroup=f"uso_{row}", fillcolor="rgba(255,105,180,0.6)",
                                    showlegend=(row == 1)), row=row, col=col)
                                fig.add_trace(go.Scatter(x=horas, y=est.curva_carga, mode="lines", name="Demanda",
                                    line=dict(color="red", width=2, dash="dash"),
                                    showlegend=(row == 1)), row=row, col=col)
                                if est.energia_vendida.sum() > 0:
                                    fig.add_trace(go.Scatter(x=horas, y=-est.energia_vendida, mode="lines", name="Venda P2P",
                                        line=dict(color="#FF4500", width=1), fill="tozeroy", fillcolor="rgba(255,69,0,0.3)",
                                        showlegend=(row == 1)), row=row, col=col)

                            est_heur = res_heur.estados[nome]
                            est_milp = res_milp.estados[nome]
                            est_heur_iso = cs["heuristica_iso"]["otimizado"].estados[nome]
                            est_milp_iso = cs["milp_iso"]["otimizado"].estados[nome]

                            fig_perfil = make_subplots(rows=4, cols=1,
                                subplot_titles=[f"Regras (Isolada) — {nome}", f"MILP (Isolada) — {nome}", f"Regras (P2P) — {nome}", f"MILP (P2P) — {nome}"],
                                shared_xaxes=True, vertical_spacing=0.06)
                            _add_perfil(fig_perfil, est_heur_iso, 1, 1)
                            _add_perfil(fig_perfil, est_milp_iso, 2, 1)
                            _add_perfil(fig_perfil, est_heur, 3, 1)
                            _add_perfil(fig_perfil, est_milp, 4, 1)
                            fig_perfil.update_layout(
                                font=dict(color="black", size=14, family="Arial, sans-serif"),
                                height=1000,
                                hovermode="x unified",
                                legend=dict(font=dict(color="black", size=13))
                            )
                            for annotation in fig_perfil['layout']['annotations']:
                                annotation['font'] = dict(size=16, color='black', family="Arial, sans-serif")
                            fig_perfil.update_xaxes(_xaxis_cfg, row=4, col=1)
                            for r in range(1, 5):
                                fig_perfil.update_yaxes(title_text="<b>Potência (kW)</b>", title_font=dict(color="black", size=14), tickfont=dict(color="black", size=13), row=r, col=1)
                            st.plotly_chart(fig_perfil, width='stretch', key=f"comp_perfil_{estacao}_{idx_mg}")

                            # ── Níveis de Armazenamento ──────────────
                            st.markdown("##### Níveis de Armazenamento")

                            # Bateria
                            if est_heur.hist_nivel_bateria.sum() > 0 or est_milp.hist_nivel_bateria.sum() > 0 or est_heur_iso.hist_nivel_bateria.sum() > 0 or est_milp_iso.hist_nivel_bateria.sum() > 0:
                                fig_bat = go.Figure()
                                fig_bat.add_trace(go.Scatter(x=horas, y=est_heur_iso.hist_nivel_bateria, mode="lines",
                                    name="Regras Iso", line=dict(color="#F6AD55", width=2, dash="dot")))
                                fig_bat.add_trace(go.Scatter(x=horas, y=est_milp_iso.hist_nivel_bateria, mode="lines",
                                    name="MILP Iso", line=dict(color="#805AD5", width=2, dash="dot")))
                                fig_bat.add_trace(go.Scatter(x=horas, y=est_heur.hist_nivel_bateria, mode="lines",
                                    name="Regras P2P", line=dict(color="#F6AD55", width=2)))
                                fig_bat.add_trace(go.Scatter(x=horas, y=est_milp.hist_nivel_bateria, mode="lines",
                                    name="MILP P2P", line=dict(color="#805AD5", width=2)))
                                fig_bat.update_layout(
                                    title=dict(text=f"<b>Bateria — {nome}</b>", font=dict(color="black", size=16)),
                                    font=dict(color="black", size=14, family="Arial, sans-serif"),
                                    xaxis=_xaxis_cfg,
                                    yaxis=dict(
                                        title=dict(text="<b>Nível (kWh)</b>", font=dict(color="black", size=14)),
                                        tickfont=dict(color="black", size=13),
                                    ),
                                    legend=dict(font=dict(color="black", size=13)),
                                    height=300,
                                    hovermode="x unified"
                                )
                                st.plotly_chart(fig_bat, width='stretch', key=f"comp_bat_{estacao}_{idx_mg}")

                            # Diesel
                            _tem_d = est_heur.hist_nivel_diesel.sum() > 0 or est_milp.hist_nivel_diesel.sum() > 0 or est_heur_iso.hist_nivel_diesel.sum() > 0 or est_milp_iso.hist_nivel_diesel.sum() > 0

                            if _tem_d:
                                fig_d = go.Figure()
                                fig_d.add_trace(go.Scatter(x=horas, y=est_heur_iso.hist_nivel_diesel, mode="lines",
                                    name="Regras Iso", line=dict(color="#F6AD55", width=2, dash="dot")))
                                fig_d.add_trace(go.Scatter(x=horas, y=est_milp_iso.hist_nivel_diesel, mode="lines",
                                    name="MILP Iso", line=dict(color="#805AD5", width=2, dash="dot")))
                                fig_d.add_trace(go.Scatter(x=horas, y=est_heur.hist_nivel_diesel, mode="lines",
                                    name="Regras P2P", line=dict(color="#F6AD55", width=2)))
                                fig_d.add_trace(go.Scatter(x=horas, y=est_milp.hist_nivel_diesel, mode="lines",
                                    name="MILP P2P", line=dict(color="#805AD5", width=2)))
                                _xaxis_cfg_d = dict(
                                    title=dict(text="<b>Tempo (h)</b>", font=dict(color="black", size=14)),
                                    tickfont=dict(color="black", size=13),
                                    tickmode="array",
                                    tickvals=list(range(0, 25, 2)),
                                    ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
                                )
                                fig_d.update_layout(
                                    title=dict(text=f"<b>Nível do Diesel (L x Tempo) — {nome}</b>", font=dict(color="black", size=16)),
                                    font=dict(color="black", size=14, family="Arial, sans-serif"),
                                    xaxis=_xaxis_cfg_d,
                                    yaxis=dict(
                                        title=dict(text="<b>Volume (L)</b>", font=dict(color="black", size=14)),
                                        tickfont=dict(color="black", size=13),
                                    ),
                                    legend=dict(font=dict(color="black", size=13)),
                                    height=300,
                                    hovermode="x unified"
                                )
                                st.plotly_chart(fig_d, width='stretch', key=f"comp_diesel_{estacao}_{idx_mg}")

                            # ── Mini-métricas ────────────────────────
                            st.markdown("##### Métricas por MG")
                            col_h, col_p = st.columns(2)
                            with col_h:
                                st.markdown("**Regras**")
                                ch1, ch2, ch3 = st.columns(3)
                                ch1.metric("Vendido", f"{est_heur.energia_vendida.sum()/60:,.1f} kWh")
                                ch2.metric("Comprado", f"{est_heur.energia_comprada.sum()/60:,.1f} kWh")
                                saldo_h = res_heur.receita_por_mg.get(nome, 0) - res_heur.gasto_compras_por_mg.get(nome, 0)
                                ch3.metric("Saldo P2P", f"R$ {saldo_h:,.2f}")
                            with col_p:
                                st.markdown("**MILP**")
                                cm1, cm2, cm3 = st.columns(3)
                                cm1.metric("Vendido", f"{est_milp.energia_vendida.sum()/60:,.1f} kWh")
                                cm2.metric("Comprado", f"{est_milp.energia_comprada.sum()/60:,.1f} kWh")
                                saldo_m = res_milp.receita_por_mg.get(nome, 0) - res_milp.gasto_compras_por_mg.get(nome, 0)
                                cm3.metric("Saldo P2P", f"R$ {saldo_m:,.2f}")

        # ============================================================
        # COMPARAÇÃO DE OTIMIZAÇÃO POR MICRORREDE (SAZONALIDADE)
        # ============================================================
        st.divider()
        st.subheader("Comparação Sazonal por Microrrede (Regras vs MILP)")
        st.caption("Veja o desempenho da mesma microrrede nas diferentes estações, comparando as otimizações.")

        # Agrupar por nome da microrrede
        nomes_base_otm = defaultdict(dict)
        for estacao in estacoes_simuladas:
            if estacao not in comp_sazonais:
                continue
            cs = comp_sazonais[estacao]
            nomes_mg = list(cs["original"].custo_total_por_mg.keys())
            for nome_mg in nomes_mg:
                nomes_base_otm[nome_mg][estacao] = {
                    "heuristica": cs["heuristica"]["otimizado"],
                    "milp": cs["milp"]["otimizado"],
                }

        if nomes_base_otm:
            tabs_mg_saz = st.tabs([f"{n}" for n in nomes_base_otm.keys()])
            
            for idx_tab, (nome_mg, dados_estacoes) in enumerate(nomes_base_otm.items()):
                with tabs_mg_saz[idx_tab]:
                    estacoes_mg = sorted(dados_estacoes.keys(), key=lambda e: ["Verão", "Outono", "Inverno", "Primavera"].index(e) if e in ["Verão", "Outono", "Inverno", "Primavera"] else 99)
                    
                    st.markdown(f"### Microrrede: {nome_mg}")
                    
                    for est in estacoes_mg:
                        st.markdown(f"#### {est}")
                        est_heur = dados_estacoes[est]["heuristica"].estados[nome_mg]
                        est_milp = dados_estacoes[est]["milp"].estados[nome_mg]
                        est_heur_iso = comp_sazonais[est]["heuristica_iso"]["otimizado"].estados[nome_mg]
                        est_milp_iso = comp_sazonais[est]["milp_iso"]["otimizado"].estados[nome_mg]
                        
                        fig_perfil = make_subplots(rows=4, cols=1,
                            subplot_titles=[f"Regras (Isolada) - {nome_mg} ({est})", f"MILP (Isolada) - {nome_mg} ({est})", f"Regras (P2P) - {nome_mg} ({est})", f"MILP (P2P) - {nome_mg} ({est})"],
                            shared_xaxes=True, vertical_spacing=0.06)
                        
                        horas = np.arange(1440) / 60
                        
                        def _add_perfil_saz(fig, est_obj, row, col):
                            fig.add_trace(go.Scatter(x=horas, y=est_obj.uso_solar, mode="lines", name="Solar", line=dict(width=0), stackgroup=f"u_{row}", fillcolor="rgba(255,215,0,0.6)", showlegend=(row==1)), row=row, col=col)
                            fig.add_trace(go.Scatter(x=horas, y=est_obj.uso_bateria, mode="lines", name="Bateria", line=dict(width=0), stackgroup=f"u_{row}", fillcolor="rgba(50,205,50,0.6)", showlegend=(row==1)), row=row, col=col)
                            fig.add_trace(go.Scatter(x=horas, y=est_obj.uso_diesel, mode="lines", name="Diesel", line=dict(width=0), stackgroup=f"u_{row}", fillcolor="rgba(169,169,169,0.6)", showlegend=(row==1)), row=row, col=col)
                            fig.add_trace(go.Scatter(x=horas, y=est_obj.uso_concessionaria, mode="lines", name="Grid", line=dict(width=0), stackgroup=f"u_{row}", fillcolor="rgba(65,105,225,0.6)", showlegend=(row==1)), row=row, col=col)
                            fig.add_trace(go.Scatter(x=horas, y=est_obj.energia_comprada, mode="lines", name="Compra P2P", line=dict(width=0), stackgroup=f"u_{row}", fillcolor="rgba(255,105,180,0.6)", showlegend=(row==1)), row=row, col=col)
                            fig.add_trace(go.Scatter(x=horas, y=est_obj.curva_carga, mode="lines", name="Demanda", line=dict(color="red", width=2, dash="dash"), showlegend=(row==1)), row=row, col=col)
                            if est_obj.energia_vendida.sum() > 0:
                                fig.add_trace(go.Scatter(x=horas, y=-est_obj.energia_vendida, mode="lines", name="Venda P2P", line=dict(color="#FF4500", width=1), fill="tozeroy", fillcolor="rgba(255,69,0,0.3)", showlegend=(row==1)), row=row, col=col)

                        _add_perfil_saz(fig_perfil, est_heur_iso, 1, 1)
                        _add_perfil_saz(fig_perfil, est_milp_iso, 2, 1)
                        _add_perfil_saz(fig_perfil, est_heur, 3, 1)
                        _add_perfil_saz(fig_perfil, est_milp, 4, 1)
                        
                        _xaxis_cfg = dict(
                            title=dict(text="<b>Hora do Dia</b>", font=dict(color="black", size=14)),
                            tickfont=dict(color="black", size=13),
                            tickmode="array",
                            tickvals=list(range(0, 25, 2)),
                            ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)]
                        )
                        fig_perfil.update_layout(
                            font=dict(color="black", size=14, family="Arial, sans-serif"),
                            height=1000,
                            hovermode="x unified",
                            margin=dict(t=50, b=30),
                            legend=dict(font=dict(color="black", size=13))
                        )
                        for annotation in fig_perfil['layout']['annotations']:
                            annotation['font'] = dict(size=16, color='black', family="Arial, sans-serif")
                        fig_perfil.update_xaxes(_xaxis_cfg, row=4, col=1)
                        for r in range(1, 5):
                            fig_perfil.update_yaxes(title_text="<b>Potência (kW)</b>", title_font=dict(color="black", size=14), tickfont=dict(color="black", size=13), row=r, col=1)

                        st.plotly_chart(fig_perfil, width='stretch', key=f"saz_perfil_hm_{nome_mg}_{est}")

                        if est_heur.hist_nivel_diesel.sum() > 0 or est_milp.hist_nivel_diesel.sum() > 0 or est_heur_iso.hist_nivel_diesel.sum() > 0 or est_milp_iso.hist_nivel_diesel.sum() > 0:
                            fig_d_saz = go.Figure()
                            fig_d_saz.add_trace(go.Scatter(x=horas, y=est_heur_iso.hist_nivel_diesel, mode="lines",
                                name="Regras Iso", line=dict(color="#F6AD55", width=2, dash="dot")))
                            fig_d_saz.add_trace(go.Scatter(x=horas, y=est_milp_iso.hist_nivel_diesel, mode="lines",
                                name="MILP Iso", line=dict(color="#805AD5", width=2, dash="dot")))
                            fig_d_saz.add_trace(go.Scatter(x=horas, y=est_heur.hist_nivel_diesel, mode="lines",
                                name="Regras P2P", line=dict(color="#F6AD55", width=2)))
                            fig_d_saz.add_trace(go.Scatter(x=horas, y=est_milp.hist_nivel_diesel, mode="lines",
                                name="MILP P2P", line=dict(color="#805AD5", width=2)))
                            fig_d_saz.update_layout(
                                title=dict(text=f"<b>Nível do Diesel (L x Tempo) — {nome_mg} ({est})</b>", font=dict(color="black", size=16)),
                                font=dict(color="black", size=14, family="Arial, sans-serif"),
                                xaxis=dict(
                                    title=dict(text="<b>Tempo (h)</b>", font=dict(color="black", size=14)),
                                    tickfont=dict(color="black", size=13),
                                    tickmode="array",
                                    tickvals=list(range(0, 25, 2)),
                                    ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
                                ),
                                yaxis=dict(
                                    title=dict(text="<b>Volume (L)</b>", font=dict(color="black", size=14)),
                                    tickfont=dict(color="black", size=13),
                                ),
                                legend=dict(font=dict(color="black", size=13)),
                                height=300,
                                hovermode="x unified"
                            )
                            st.plotly_chart(fig_d_saz, width='stretch', key=f"saz_diesel_hm_{nome_mg}_{est}")

                    st.divider()
                    st.markdown("#### Quadro Comparativo de Custos por Período")
                    dados_tabela_custos = []
                    for est in estacoes_mg:
                        custo_heur = dados_estacoes[est]["heuristica"].custo_total_por_mg.get(nome_mg, 0)
                        custo_milp = dados_estacoes[est]["milp"].custo_total_por_mg.get(nome_mg, 0)
                        dados_tabela_custos.append({
                            "Período": f"{est}",
                            "Custo Regras (R$)": custo_heur,
                            "Custo MILP (R$)": custo_milp,
                            "Diferença (MILP - Regras)": custo_milp - custo_heur
                        })
                    
                    df_custos = pd.DataFrame(dados_tabela_custos)
                    
                    def color_diff(val):
                        if pd.isna(val):
                            return ''
                        if float(val) < -0.01:
                            return 'color: green'
                        elif float(val) > 0.01:
                            return 'color: red'
                        return ''

                    st.dataframe(
                        df_custos.style.format({
                            "Custo Regras (R$)": "R$ {:,.2f}",
                            "Custo MILP (R$)": "R$ {:,.2f}",
                            "Diferença (MILP - Regras)": "R$ {:,.2f}"
                        }).map(color_diff, subset=['Diferença (MILP - Regras)']),
                        width='stretch', hide_index=True
                    )
                    
                    fig_custos_saz = go.Figure()
                    fig_custos_saz.add_trace(go.Bar(
                        name="Regras", 
                        x=[d["Período"] for d in dados_tabela_custos], 
                        y=[d["Custo Regras (R$)"] for d in dados_tabela_custos], 
                        marker_color='#FFA15A', 
                        text=[f"R$ {d['Custo Regras (R$)']:,.2f}" for d in dados_tabela_custos], 
                        textposition="auto",
                        textfont=dict(color="black", size=13)
                    ))
                    fig_custos_saz.add_trace(go.Bar(
                        name="MILP", 
                        x=[d["Período"] for d in dados_tabela_custos], 
                        y=[d["Custo MILP (R$)"] for d in dados_tabela_custos], 
                        marker_color='#805AD5', 
                        text=[f"R$ {d['Custo MILP (R$)']:,.2f}" for d in dados_tabela_custos], 
                        textposition="auto",
                        textfont=dict(color="black", size=13)
                    ))
                    fig_custos_saz.update_layout(
                        font=dict(color="black", size=14, family="Arial, sans-serif"),
                        barmode='group', 
                        title=dict(text=f"<b>Evolução de Custos - {nome_mg}</b>", font=dict(color="black", size=16)), 
                        yaxis=dict(
                            title=dict(text="<b>Custo Diário (R$)</b>", font=dict(color="black", size=14)),
                            tickfont=dict(color="black", size=13)
                        ),
                        xaxis=dict(
                            tickfont=dict(color="black", size=13)
                        ),
                        legend=dict(font=dict(color="black", size=13)),
                        height=450
                    )
                    st.plotly_chart(fig_custos_saz, width='stretch', key=f"saz_custos_hm_{nome_mg}")

# ============================================================
# EXIBIÇÃO DOS TEMPOS DE EXECUÇÃO
# ============================================================
st.divider()
st.subheader("⏱️ Detalhamento dos Tempos de Execução dos Métodos")
st.markdown(
    "Comparativo detalhado do tempo computacional (em segundos medidos com `perf_counter`). "
    "Permite distinguir o tempo gasto pelo **Solver MILP (CBC)** do tempo gasto em **Simulações de Mercado / Busca Heurística**."
)

comp_saz_tempos = st.session_state.get("m3_comparacao_otm_sazonais")
if comp_saz_tempos:
    linhas_t = []
    # Acumular por método
    estacoes_com_t = list(comp_saz_tempos.keys())
    for chave, rot, cen, cor, base in METODOS_COMP:
        t_total_met = 0.0
        t_prep_met = 0.0
        t_mod_met = 0.0
        t_solv_met = 0.0
        t_busca_met = 0.0
        n_sim_met = 0
        n_milp_met = 0
        est_count = 0

        for est, cs in comp_saz_tempos.items():
            entry = cs.get(chave)
            if entry is None:
                continue
            tm = entry.get("tempos", {}) if isinstance(entry, dict) else {}
            t_total_met += tm.get("total", 0.0)
            t_prep_met += tm.get("preparacao", 0.0)
            t_mod_met += tm.get("milp_modelagem", 0.0)
            t_solv_met += tm.get("milp_solver", 0.0)
            t_busca_met += tm.get("busca_simulacao", 0.0)
            n_sim_met += tm.get("n_simulacoes", 0)
            n_milp_met += tm.get("n_milp", 0)
            est_count += 1

        if est_count > 0 and t_total_met > 0:
            linhas_t.append({
                "Método": rot,
                "Cenário": cen,
                "Tempo Total (s)": t_total_met,
                "Média / Estação (s)": t_total_met / est_count,
                "Solver CBC (s)": t_solv_met,
                "Modelagem MILP (s)": t_mod_met,
                "Busca / Simulação (s)": t_busca_met,
                "Simulações P2P": n_sim_met,
                "Modelos MILP": n_milp_met,
            })

    if linhas_t:
        df_t = pd.DataFrame(linhas_t)
        st.dataframe(
            df_t.style.format({
                "Tempo Total (s)": "{:,.3f} s",
                "Média / Estação (s)": "{:,.3f} s",
                "Solver CBC (s)": "{:,.3f} s",
                "Modelagem MILP (s)": "{:,.3f} s",
                "Busca / Simulação (s)": "{:,.3f} s",
                "Simulações P2P": "{:d}",
                "Modelos MILP": "{:d}",
            }).highlight_min(subset=["Tempo Total (s)"], color="#BEE3F8"),
            width='stretch', hide_index=True
        )

        st.caption(
            "💡 **Dica de Desempenho:** O método *MILP Local (Puro)* resolve a programação inteira mista no solver CBC "
            "em poucos centésimos de segundo. O método *MILP Local + Refino* realiza centenas de iterações do "
            "`SimuladorMercado.simular()`, o que explica o tempo maior e a melhora adicional no custo."
        )

col_time1, col_time2, col_time3 = st.columns(3)

# Simulação
t_sim_mercado = st.session_state.get("m3_tempo_simulador_mercado", 0.0)
t_sim_iso = st.session_state.get("m3_tempo_simulador_isolado", 0.0)
t_sim_total = st.session_state.get("m3_tempo_simulacao_total", 0.0)

with col_time1:
    st.markdown("**1. Simulação Inicial**")
    st.metric("SimuladorMercado.simular()", f"{t_sim_mercado:.2f} s")
    st.metric("SimuladorSemTransacao.simular()", f"{t_sim_iso:.2f} s")
    st.metric("Total da Simulação", f"{t_sim_total:.2f} s")

# Comparação
t_comp_regras = st.session_state.get("m3_tempo_regras_comp", 0.0)
t_comp_milp = st.session_state.get("m3_tempo_milp_comp", 0.0)
t_comp_total = st.session_state.get("m3_tempo_comparacao_total", 0.0)

with col_time2:
    st.markdown("**2. Comparação (Regras vs MILP)**")
    st.metric("OtimizadorPosDia (Regras)", f"{t_comp_regras:.2f} s")
    st.metric("OtimizadorMILPPosDia (MILP)", f"{t_comp_milp:.2f} s")
    st.metric("Total da Comparação", f"{t_comp_total:.2f} s")

# Otimização individual
t_otim_ind = st.session_state.get("m3_tempo_otim_individual", 0.0)
t_otim_total = st.session_state.get("m3_tempo_otimizacao_total", 0.0)

with col_time3:
    st.markdown("**3. Otimização Individual**")
    st.metric("Método Otimizador", f"{t_otim_ind:.2f} s")
    st.metric("Total da Otimização", f"{t_otim_total:.2f} s")

