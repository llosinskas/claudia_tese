# Banco de dados
from sqlalchemy import MetaData
from models import init_db
from database.database_config import Configure
from models.Microrrede import Microrrede, Concessionaria, Solar, Biogas, Bateria, Diesel, Carga, CargaFixa
from sqlalchemy.orm import joinedload
from models.CRUD import Ler, Deletar, Ler_Objeto
#Interface
import streamlit as st
import plotly.graph_objects as go
import pydeck as pdk
# Tools
import numpy as np
import pandas as pd
import json
from collections import defaultdict
from Tools.GerarCurvaCarga import Curva_carga
from Tools.PrecoConcessionaria import array_valores_acumulado
from Tools.geradorSolar import Valor_solar
from GerenciadorMicrorrede.Gerenciador import Gerenciador

# Configuração do banco de dados
DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

st.set_page_config(layout="wide", page_title="Página principal")

st.title("⚡ Análises de Microrredes")

ICONES_ESTACOES = {
    "Verão":     "☀️",
    "Outono":    "🍂",
    "Inverno":   "❄️",
    "Primavera": "🌸",
}

ORDEM_ESTACOES = ["Verão", "Outono", "Inverno", "Primavera"]

coordenadas = []

try:
    microrredes = session.query(Microrrede).options(
        joinedload(Microrrede.concessionaria),
        joinedload(Microrrede.solar),
        joinedload(Microrrede.biogas),
        joinedload(Microrrede.diesel),
        joinedload(Microrrede.bateria),
        joinedload(Microrrede.carga).joinedload(Carga.cargaFixa)
    ).all()

    if not microrredes:
        st.info("Nenhuma microrrede cadastrada. Acesse a página **Exemplos** para gerar os dados de demonstração.")
    else:
        # ─── AGRUPAMENTO POR ESTAÇÃO ───────────────────────────────────────
        por_estacao = defaultdict(list)
        sem_estacao = []
        for mg in microrredes:
            est = mg.estacao
            if est and est in ORDEM_ESTACOES:
                por_estacao[est].append(mg)
            else:
                sem_estacao.append(mg)

        estacoes_presentes = [e for e in ORDEM_ESTACOES if e in por_estacao]
        if sem_estacao:
            estacoes_presentes.append("Sem estação")
            por_estacao["Sem estação"] = sem_estacao

        # ─── MÉTRICAS RESUMO ───────────────────────────────────────────────
        total_mgs = len(microrredes)
        nomes_unicos = len({mg.nome for mg in microrredes})
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("Total de microrredes", total_mgs)
        col_r2.metric("Nomes distintos", nomes_unicos)
        col_r3.metric("Estações com dados", len(estacoes_presentes))

        st.divider()

        # ─── TABS POR ESTAÇÃO ─────────────────────────────────────────────
        st.subheader("📋 Microrredes por Estação")

        tab_labels = [
            f"{ICONES_ESTACOES.get(e, '📅')} {e} ({len(por_estacao[e])})"
            for e in estacoes_presentes
        ]
        tabs = st.tabs(tab_labels)

        for tab_idx, estacao in enumerate(estacoes_presentes):
            with tabs[tab_idx]:
                mgs_estacao = por_estacao[estacao]

                for microrrede in mgs_estacao:
                    st.header(
                        f"{microrrede.nome}",
                        divider=True,
                    )

                    col1, col2 = st.columns([5, 5], border=True)

                    # ── Curva de carga ──
                    col1.text(
                        f"📍 lat: {microrrede.coordenada_x}  lon: {microrrede.coordenada_y}"
                    )
                    cargas = microrrede.carga.cargaFixa if microrrede.carga else []
                    col1.subheader("Curva de Carga")
                    curva_carga = np.zeros(1440)
                    cargas_nome, cargas_potencia, tempos_liga, tempos_desliga = [], [], [], []

                    for carga in cargas:
                        cargas_nome.append(carga.nome)
                        cargas_potencia.append(carga.potencia)
                        tempos_liga.append(carga.tempo_liga)
                        tempos_desliga.append(carga.tempo_desliga)
                        curva_carga += np.array(
                            Curva_carga(carga.potencia, carga.tempo_liga, carga.tempo_desliga)
                        )

                    df_cargas = pd.DataFrame({
                        "Carga": cargas_nome,
                        "Potência (kW)": cargas_potencia,
                        "Liga (min)": tempos_liga,
                        "Desliga (min)": tempos_desliga,
                    })
                    col1.line_chart(
                        curva_carga,
                        x_label="Tempo (min)",
                        y_label="Potência (kW)",
                    )
                    col1.dataframe(df_cargas, hide_index=True, width='stretch')

                    # ── Concessionária ──
                    col1.subheader("Concessionária")
                    if microrrede.concessionaria:
                        col1.text(
                            f"Nome: {microrrede.concessionaria.nome}\n"
                            f"Tarifa: R$ {microrrede.concessionaria.tarifa:,.2f}\n"
                            f"Grupo: {microrrede.concessionaria.grupo}"
                        )
                    coordenadas.append((microrrede.coordenada_x, microrrede.coordenada_y))

                    # ── Solar ──
                    if microrrede.solar:
                        col2.subheader("☀️ Solar")
                        col2.text(
                            f"Potência de pico: {microrrede.solar.potencia:,.2f} kW\n"
                            f"Custo por kWh: R$ {microrrede.solar.custo_kwh:,.2f}"
                        )
                        curva_solar = np.array(json.loads(microrrede.solar.curva_geracao))
                        df_solar = pd.DataFrame({
                            "Geração Solar (kW)": curva_solar,
                            "Carga (kW)": curva_carga,
                        })
                        col2.subheader("Geração vs. Carga")
                        col2.area_chart(
                            df_solar,
                            x_label="Tempo (min)",
                            y_label="Potência (kW)",
                        )
                    else:
                        col2.write("Sem gerador solar cadastrado.")

                    # ── Biogás ──
                    if microrrede.biogas:
                        col2.subheader("🌿 Biogás")
                        col2.text(
                            f"Potência: {microrrede.biogas.potencia:,.2f} kW\n"
                            f"Tanque: {microrrede.biogas.tanque:,.2f} m³\n"
                            f"Geração diária: {microrrede.biogas.geracao:,.2f} m³/dia\n"
                            f"Custo por kWh: {microrrede.biogas.custo_por_kWh:,.2f} R$/kWh"
                        )

                    # ── Diesel ──
                    if microrrede.diesel:
                        col1.subheader("⛽ Diesel")
                        col1.text(
                            f"Potência: {microrrede.diesel.potencia:,.2f} kW\n"
                            f"Tanque: {microrrede.diesel.tanque:,.2f} l\n"
                            f"Consumo 50%: {microrrede.diesel.consumo_50:,.2f} l/h\n"
                            f"Consumo 75%: {microrrede.diesel.consumo_75:,.2f} l/h\n"
                            f"Consumo 100%: {microrrede.diesel.consumo_100:,.2f} l/h\n"
                            f"Custo por kWh: {microrrede.diesel.custo_por_kWh:,.2f} R$/kWh"
                        )
                    else:
                        col1.write("Sem gerador a diesel.")

                    # ── Bateria ──
                    if microrrede.bateria:
                        col2.subheader("🔋 Bateria")
                        col2.text(
                            f"Potência: {microrrede.bateria.potencia:,.2f} kW\n"
                            f"Capacidade: {microrrede.bateria.capacidade:,.2f} kWh\n"
                            f"Tecnologia: {microrrede.bateria.bateria}\n"
                            f"Eficiência: {microrrede.bateria.eficiencia} %\n"
                            f"DOD: {microrrede.bateria.capacidade_min}% – {microrrede.bateria.capacidade_max}%\n"
                            f"Custo por kWh: {microrrede.bateria.custo_kwh} R$/kWh"
                        )
                    else:
                        col2.write("Sem bateria cadastrada.")

                    # ── Botão deletar ──
                    if col2.button("🗑️ Deletar", key=f"deletar_{microrrede.id}"):
                        Deletar(Microrrede, microrrede.id)
                        st.rerun()

except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.exception(e)

# ─── MAPA ───────────────────────────────────────────────────────────────
if coordenadas:
    st.divider()
    st.subheader("🗺️ Localização das Microrredes")
    df_mapa = pd.DataFrame(coordenadas, columns=["lat", "lon"])
    st.pydeck_chart(
        pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude=df_mapa["lat"].mean(),
                longitude=df_mapa["lon"].mean(),
                zoom=7,
                pitch=50,
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=df_mapa,
                    get_position="[lon, lat]",
                    get_color="[200, 30, 0, 160]",
                    get_radius=3000,
                ),
            ],
        )
    )

# ─── SIDEBAR: gerenciamento ───────────────────────────────────────────
st.sidebar.title("⚙️ Gerenciamento do Banco de Dados")
if st.sidebar.button("🗑️ Excluir Todo o Banco de Dados", type="primary"):
    try:
        meta = MetaData()
        meta.reflect(bind=engine)
        for table in reversed(meta.sorted_tables):
            session.execute(table.delete())
        session.commit()
        Base.metadata.drop_all(engine)
        st.sidebar.success("Todas as tabelas foram excluídas com sucesso!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Erro ao excluir o banco de dados: {e}")