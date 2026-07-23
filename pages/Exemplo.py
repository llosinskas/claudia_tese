import streamlit as st
import json
import os
import pandas as pd
from models.Microrrede import Microrrede, Bateria, Biogas, Diesel, Carga, Solar, Concessionaria, CargaFixa
from models.CRUD import Criar_Varios
from Tools.Solar.gerar_curva_solar_sazonal import gerar_curvas_sazonais

st.set_page_config(page_title="Exemplos de Microrredes", layout="wide")
st.title("📋 Exemplos de Sistemas de Microrredes")
st.markdown(
    "Gera as 4 microrredes da pesquisa com dados das planilhas da pasta `exemplos/`, "
    "criando uma versão para cada estação do ano (Verão, Outono, Inverno, Primavera)."
)

# ─────────────────────────────────────────────
# CONFIGURAÇÃO DAS MICRORREDES
# ─────────────────────────────────────────────
MICRORREDES_CONFIG = {
    "MG - 01": {
        "arquivo": "DADOS MR 1.xlsx",
        "prefixo_abas": "MR 1",
        "coordenadas": (-31.85, -52.90),
        "localidade": "Cerrito",
    },
    "MG - 02": {
        "arquivo": "DADOS MR 2.xlsx",
        "prefixo_abas": "MR 2",
        "coordenadas": (-31.51, -52.49),
        "localidade": "Pedro Osório",
    },
    "MG - 03": {
        "arquivo": "DADOS MR 3.xlsx",
        "prefixo_abas": "MR 3",
        "coordenadas": (-31.26, -53.06),
        "localidade": "Piratini",
    },
    "MG - 04": {
        "arquivo": "DADOS MR 4.xlsx",
        "prefixo_abas": "MR 4",
        "coordenadas": (-31.23, -52.40),
        "localidade": "Canguçu",
    },
}

MAPA_ESTACOES = {
    "VERAO":     "Verão",
    "OUTONO":    "Outono",
    "INVERNO":   "Inverno",
    "PRIMAVERA": "Primavera",
}

PASTA_EXEMPLOS = os.path.join(os.path.dirname(__file__), "..", "exemplos")


def _normalizar(texto: str) -> str:
    """Remove acentos e maiúsculas para comparação segura."""
    import unicodedata
    return unicodedata.normalize("NFD", str(texto).upper()).encode("ascii", "ignore").decode()


def _parse_sheet(df: pd.DataFrame) -> dict:
    """
    Lê um DataFrame (sem cabeçalho) no formato dos arquivos DADOS MR X.xlsx
    e retorna um dict com 'cargas', 'solar', 'diesel', 'bateria', 'tarifa'.
    
    Estrutura esperada:
      - Linha 0: título (ignorado)
      - Linha 1: cabeçalho cargas  ["Descrição", "Potência (kW)", "Minuto liga", "Minuto desliga", "Prioridade", ...]
      - Linhas 2..N-1: cargas (até linha em branco ou até linha da tabela de fontes)
      - Linha com "Fonte" ou "PV"/"Diesel"/...: tabela de fontes
    """
    # Encontra onde começa a tabela de fontes (linha com "Fonte" ou "PV" na col 0)
    linha_fontes = None
    for i, row in df.iterrows():
        val = _normalizar(str(row.iloc[0])) if pd.notna(row.iloc[0]) else ""
        if val in ("FONTE", "PV", "DIESEL", "BATERIA"):
            # Se for "FONTE", é o cabeçalho da tabela de fontes
            if val == "FONTE":
                linha_fontes = i + 1  # dados começam na linha seguinte
            else:
                linha_fontes = i  # já é dado
            break

    # --- CARGAS ---
    cargas = []
    # Linha 1 é o cabeçalho das cargas, dados começam na linha 2
    linha_inicio_cargas = 2
    linha_fim_cargas = linha_fontes - 1 if linha_fontes is not None else len(df)

    for i in range(linha_inicio_cargas, linha_fim_cargas):
        if i >= len(df):
            break
        row = df.iloc[i]
        
        # Check if the row has any valid data in the numeric columns
        if pd.isna(row.iloc[1:4]).all():
            continue
            
        nome = row.iloc[0]
        if pd.isna(nome) or str(nome).strip() == "":
            nome = f"Carga Extra {i}"
            
        def safe_float(v, default):
            if pd.isna(v): return default
            try: return float(v)
            except: return default
            
        potencia   = safe_float(row.iloc[1], 0.0)
        liga       = int(safe_float(row.iloc[2], 0.0))
        desliga    = int(safe_float(row.iloc[3], 1440.0))
        prioridade = int(safe_float(row.iloc[4], 1.0))
        
        if potencia == 0.0 and (pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() == ""):
            continue

        cargas.append({
            "nome": str(nome).strip()[:100],
            "potencia": potencia,
            "liga": liga,
            "desliga": desliga,
            "prioridade": prioridade,
        })

    # --- FONTES ---
    solar    = {"potencia": 60.0, "custo": 0.24}
    diesel   = {"potencia": 5.0,  "custo": 2.0,
                "tanque": 40, "consumo_50": 1.3, "consumo_75": 2.0, "consumo_100": 2.6}
    bateria  = {"potencia": 12.0, "capacidade": 60.0, "custo": 0.8}
    tarifa   = 0.87

    if linha_fontes is not None:
        for i in range(linha_fontes, len(df)):
            row = df.iloc[i]
            fonte = _normalizar(str(row.iloc[0])) if pd.notna(row.iloc[0]) else ""
            if "PV" in fonte or "SOLAR" in fonte or "FOTOVOLTAICO" in fonte:
                try:
                    solar["potencia"] = float(row.iloc[1]) if pd.notna(row.iloc[1]) else solar["potencia"]
                    solar["custo"]    = float(row.iloc[2]) if pd.notna(row.iloc[2]) else solar["custo"]
                except (ValueError, TypeError):
                    pass
            elif "DIESEL" in fonte or "GERADOR" in fonte:
                try:
                    diesel["potencia"]    = float(row.iloc[1]) if pd.notna(row.iloc[1]) else diesel["potencia"]
                    diesel["custo"]       = float(row.iloc[2]) if pd.notna(row.iloc[2]) else diesel["custo"]
                    diesel["tanque"]      = float(row.iloc[4]) if pd.notna(row.iloc[4]) else diesel["tanque"]
                    diesel["consumo_100"] = float(row.iloc[5]) if pd.notna(row.iloc[5]) else diesel["consumo_100"]
                    diesel["consumo_75"]  = float(row.iloc[6]) if pd.notna(row.iloc[6]) else diesel["consumo_75"]
                    diesel["consumo_50"]  = float(row.iloc[7]) if pd.notna(row.iloc[7]) else diesel["consumo_50"]
                except (ValueError, TypeError):
                    pass
            elif "BATERIA" in fonte or "BATERIAS" in fonte:
                try:
                    bateria["potencia"]   = float(row.iloc[1]) if pd.notna(row.iloc[1]) else bateria["potencia"]
                    bateria["custo"]      = float(row.iloc[2]) if pd.notna(row.iloc[2]) else bateria["custo"]
                    # Coluna 8 = Cap de descarga (kWh)
                    bateria["capacidade"] = float(row.iloc[8]) if pd.notna(row.iloc[8]) else bateria["capacidade"]
                except (ValueError, TypeError):
                    pass
            elif "CONCESS" in fonte or "CONCESSIONARIA" in fonte:
                try:
                    tarifa = float(row.iloc[2]) if pd.notna(row.iloc[2]) else tarifa
                except (ValueError, TypeError):
                    pass

    return {
        "cargas":  cargas,
        "solar":   solar,
        "diesel":  diesel,
        "bateria": bateria,
        "tarifa":  tarifa,
    }


def _ler_dados_excel(pasta: str, config: dict) -> dict:
    """
    Lê um arquivo Excel e retorna um dict {estacao: dados}.
    """
    caminho = os.path.join(pasta, config["arquivo"])
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    xl = pd.ExcelFile(caminho)
    resultado = {}

    for sheet_name in xl.sheet_names:
        # Determina estação a partir do nome da aba
        nome_normalizado = _normalizar(sheet_name)
        estacao_encontrada = None
        for chave, estacao in MAPA_ESTACOES.items():
            if chave in nome_normalizado:
                estacao_encontrada = estacao
                break

        if estacao_encontrada is None:
            continue  # Aba não reconhecida, pula

        df = xl.parse(sheet_name, header=None)
        resultado[estacao_encontrada] = _parse_sheet(df)

    return resultado


def exemplo_microrredes():
    """Lê os arquivos Excel e cria as microrredes no banco de dados."""
    mgs_todos = []

    barra = st.progress(0, text="Iniciando...")
    total = len(MICRORREDES_CONFIG) * 4  # 4 microrredes × 4 estações
    contador = 0

    for mg_nome, cfg_mg in MICRORREDES_CONFIG.items():
        lat, lon = cfg_mg["coordenadas"]

        # Lê os dados do Excel desta microrrede
        try:
            dados_excel = _ler_dados_excel(PASTA_EXEMPLOS, cfg_mg)
        except FileNotFoundError as e:
            st.error(str(e))
            return

        if not dados_excel:
            st.warning(f"Nenhuma estação encontrada no arquivo de {mg_nome}. Verifique os nomes das abas.")
            continue

        # Gera curvas solares para as estações encontradas
        potencia_solar_ref = next(iter(dados_excel.values()))["solar"]["potencia"]
        estacoes_disponiveis = list(dados_excel.keys())

        try:
            curvas = gerar_curvas_sazonais(
                latitude=lat,
                longitude=lon,
                potencia_kw=potencia_solar_ref,
                eficiencia=0.8,
                estacoes=estacoes_disponiveis,
            )
        except Exception as e:
            st.warning(f"Erro ao gerar curvas solares para {mg_nome}: {e}. Usando curva zerada.")
            import numpy as np
            curvas = {est: np.zeros(1440) for est in estacoes_disponiveis}

        for estacao in ["Verão", "Outono", "Inverno", "Primavera"]:
            contador += 1
            barra.progress(
                contador / total,
                text=f"Gerando {mg_nome} — {estacao}... ({contador}/{total})"
            )

            # Se a estação não está no Excel, usa a mais próxima disponível
            dados = dados_excel.get(estacao, next(iter(dados_excel.values())))

            curva_est = curvas.get(estacao, curvas.get(estacoes_disponiveis[0]))

            bat_cfg    = dados["bateria"]
            sol_cfg    = dados["solar"]
            die_cfg    = dados["diesel"]

            bateria_obj = Bateria(
                potencia=bat_cfg["potencia"],
                capacidade=bat_cfg["capacidade"],
                bateria="LiFePO4",
                nivel=100,
                eficiencia=95,
                capacidade_min=10,
                capacidade_max=90,
                custo_kwh=bat_cfg["custo"],
            )
            solar_obj = Solar(
                potencia=sol_cfg["potencia"],
                custo_kwh=sol_cfg["custo"],
                curva_geracao=json.dumps(curva_est.tolist()),
            )
            conc_obj = Concessionaria(
                nome="CEEE - Equatorial",
                tarifa=dados["tarifa"],
                demanda=100,
                grupo="B",
            )
            diesel_obj = Diesel(
                potencia=die_cfg["potencia"],
                custo_por_kWh=die_cfg["custo"],
                nivel=100,
                tanque=die_cfg["tanque"],
                consumo_50=die_cfg["consumo_50"],
                consumo_75=die_cfg["consumo_75"],
                consumo_100=die_cfg["consumo_100"],
            )
            cargas_fixas = [
                CargaFixa(
                    nome=c["nome"],
                    potencia=c["potencia"],
                    tempo_liga=c["liga"],
                    tempo_desliga=c["desliga"],
                    prioridade=c["prioridade"],
                )
                for c in dados["cargas"]
            ]

            mg = Microrrede(
                nome=mg_nome,
                estacao=estacao,
                coordenada_x=lat,
                coordenada_y=lon,
                bateria=bateria_obj,
                solar=solar_obj,
                concessionaria=conc_obj,
                diesel=diesel_obj,
                biogas=None,
                carga=Carga(cargaFixa=cargas_fixas),
            )
            mgs_todos.append(mg)

    if mgs_todos:
        Criar_Varios(mgs_todos)
        barra.progress(1.0, text="Concluído!")
    else:
        st.error("Nenhuma microrrede foi gerada. Verifique os arquivos Excel.")


# ─────────────────────────────────────────────
# INTERFACE STREAMLIT
# ─────────────────────────────────────────────
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("Microrredes do Estudo")

    for mg_nome, cfg in MICRORREDES_CONFIG.items():
        lat, lon = cfg["coordenadas"]
        arquivo_existe = os.path.exists(os.path.join(PASTA_EXEMPLOS, cfg["arquivo"]))
        icone = "✅" if arquivo_existe else "❌"
        st.markdown(
            f"""
**{mg_nome} — {cfg["localidade"]}**  
- 📍 Coordenadas: ({lat}, {lon})  
- 📄 Arquivo: `{cfg["arquivo"]}` {icone}  
- 🗓️ Estações: Verão · Outono · Inverno · Primavera  
            """
        )

with col2:
    st.subheader("Ações")

    if st.button("☀️ Testar Geração Solar (MG-01 Verão)", width='stretch'):
        with st.spinner("Gerando curva..."):
            curvas = gerar_curvas_sazonais(
                latitude=-31.85, longitude=-52.90, potencia_kw=60, eficiencia=0.8, estacoes=["Verão"]
            )
        st.line_chart(curvas["Verão"])

    st.divider()

    if st.button("🚀 Gerar Exemplos (4 MGs × 4 Estações)", type="primary", width='stretch'):
        with st.spinner("Lendo arquivos Excel e cadastrando microrredes..."):
            try:
                exemplo_microrredes()
                st.success(
                    "✅ 16 microrredes criadas com sucesso!\n\n"
                    "Acesse **Mercado 2** para comparar as estações."
                )
            except Exception as e:
                st.error(f"Erro ao gerar exemplos: {e}")
                st.exception(e)
