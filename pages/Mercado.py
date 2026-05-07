import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from models.Microrrede import Microrrede
from models.CRUD import Ler
from analises.config import ConfigAnalise
from analises.analise2 import Analise2
from analises.analise3 import Analise3
from analises.analise_milp import AnaliseMILP
from analises.analise_pso import AnalisePSO
from mercado import ResultadoAnalise, BalcaoEnergia

st.set_page_config(page_title="Mercado P2P", layout="wide")
st.title("🤝 Balcão de Energia (Mercado P2P)")
st.markdown("Otimização colaborativa entre microrredes baseada em proximidade geográfica e composição energética.")

# 1. Configurações Laterais
with st.sidebar:
    st.header("Configurações do Mercado")
    
    todas_microrredes = Ler(Microrrede)
    nomes_mg = [str(m) for m in todas_microrredes]
    
    mgs_selecionadas = st.multiselect(
        "Microrredes Participantes:", 
        todas_microrredes, 
        default=todas_microrredes,
        format_func=lambda x: str(x)
    )
    
    metodo = st.selectbox(
        "Método de Análise:",
        options=["Análise 3 (Heurística + Deslize)", "Análise 2 (Heurística)", "MILP", "PSO"]
    )
    
    st.divider()
    st.subheader("Parâmetros Financeiros e Técnicos")
    margem = st.slider("Margem de Lucro na Venda (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.5) / 100.0
    coef_perda = st.slider("Fator de Perda (% / km)", min_value=0.0, max_value=1.0, value=0.4, step=0.1) / 100.0
    
    st.divider()
    st.subheader("Fontes Habilitadas Globalmente")
    solar_ligado = st.checkbox("Solar", value=True)
    bateria_ligada = st.checkbox("Bateria", value=True)
    diesel_ligado = st.checkbox("Diesel", value=True)
    biogas_ligado = st.checkbox("Biogás", value=True)
    
    config = ConfigAnalise(
        solar_ligado=solar_ligado,
        bateria_ligada=bateria_ligada,
        diesel_ligado=diesel_ligado,
        biogas_ligado=biogas_ligado,
        margem_venda=margem,
        coef_perda_km=coef_perda,
        deslizamento_habilitado=(metodo == "Análise 3 (Heurística + Deslize)")
    )
    
    executar = st.button("🚀 Executar Balcão de Energia", type="primary", use_container_width=True)

if not mgs_selecionadas:
    st.warning("Selecione pelo menos uma microrrede para participar do mercado.")
    st.stop()

if executar:
    with st.spinner("1/3 Executando análises individuais..."):
        from models.CRUD import Ler_Objeto
        resultados_analise = []
        for mg_detached in mgs_selecionadas:
            mg = Ler_Objeto(Microrrede, mg_detached.id)
            if metodo == "Análise 2 (Heurística)":
                res = Analise2.executar(mg, config)
                ra = ResultadoAnalise.from_analise2_ou_3(mg, res, "heuristico")
            elif metodo == "Análise 3 (Heurística + Deslize)":
                res = Analise3.analise_3(mg, config)['otimizado']
                ra = ResultadoAnalise.from_analise2_ou_3(mg, res, "heuristico_deslize")
            elif metodo == "MILP":
                #df, custos, sol = AnaliseMILP.executar(mg, config)
                #ra = ResultadoAnalise.from_milp(mg, df)
                st.error("Integração do resultado MILP com o balcão em desenvolvimento.")
                st.stop()
            else:
                st.error("Método PSO em desenvolvimento.")
                st.stop()
                
            resultados_analise.append(ra)
            
    with st.spinner("2/3 Processando order book (Matching e Perdas)..."):
        balcao = BalcaoEnergia(resultados_analise, margem_venda=margem, coef_perda_km=coef_perda)
        resultado_mercado = balcao.executar()
        
    with st.spinner("3/3 Gerando visualizações..."):
        
        # --- MÉTRICAS GLOBAIS ---
        st.subheader("📊 Resumo do Mercado")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Economia Total", f"R$ {resultado_mercado.economia_total:,.2f}", 
                  f"{(resultado_mercado.economia_total / sum(resultado_mercado.custo_sem_balcao.values()) * 100):.1f}%" if sum(resultado_mercado.custo_sem_balcao.values()) > 0 else "0%")
        c2.metric("⚡ Volume Negociado", f"{resultado_mercado.volume_total_negociado:,.2f} kWh")
        c3.metric("📉 Perdas por Distância", f"{resultado_mercado.perdas_totais_kwh:,.2f} kWh")
        c4.metric("🔄 Qtd. Transações", f"{resultado_mercado.num_transacoes}")
        
        st.divider()
        
        # --- CUSTOS COMPARATIVOS ---
        st.subheader("💰 Comparação de Custos: Isolado vs Mercado")
        
        df_custos = pd.DataFrame({
            "Operação Isolada (R$)": pd.Series({str(mg): resultado_mercado.custo_sem_balcao[str(mg)] for mg in mgs_selecionadas}),
            "Com Mercado P2P (R$)": pd.Series({str(mg): resultado_mercado.custo_com_balcao[str(mg)] for mg in mgs_selecionadas})
        }).reset_index().rename(columns={"index": "Microrrede"})
        
        fig_custos = px.bar(df_custos, x="Microrrede", y=["Operação Isolada (R$)", "Com Mercado P2P (R$)"], 
                           barmode='group', text_auto='.2s',
                           color_discrete_map={"Operação Isolada (R$)": "#EF553B", "Com Mercado P2P (R$)": "#00CC96"})
        fig_custos.update_layout(yaxis_title="Custo Diário (R$)")
        st.plotly_chart(fig_custos, use_container_width=True)
        
        # --- MATRIZ ENERGÉTICA ---
        st.subheader("🥧 Composição Energética por Microrrede")
        cols = st.columns(len(mgs_selecionadas))
        
        cores_fontes = {
            'Solar': '#FFD700',
            'Bateria': '#32CD32',
            'Diesel': '#A9A9A9',
            'Biogás': '#8B4513',
            'Concessionária': '#4169E1'
        }
        
        for i, mg in enumerate(mgs_selecionadas):
            nome = str(mg)
            matriz = resultado_mercado.matrizes[nome]
            
            valores = [matriz.perc_solar, matriz.perc_bateria, matriz.perc_diesel, matriz.perc_biogas, matriz.perc_concessionaria]
            labels = ['Solar', 'Bateria', 'Diesel', 'Biogás', 'Concessionária']
            
            # Filtra fontes com % zero
            v_f = [(v, l) for v, l in zip(valores, labels) if v > 0.1]
            if not v_f:
                continue
                
            val_f, lab_f = zip(*v_f)
            
            fig_pie = go.Figure(data=[go.Pie(labels=lab_f, values=val_f, hole=.4, 
                                            marker=dict(colors=[cores_fontes[l] for l in lab_f]))])
            fig_pie.update_layout(title_text=f"{nome}<br>Custo Médio: R$ {matriz.custo_medio_kwh:.2f}/kWh",
                                  showlegend=False, margin=dict(t=50, b=0, l=0, r=0))
            
            with cols[i]:
                st.plotly_chart(fig_pie, use_container_width=True)
                
        # --- FLUXO DE ENERGIA SANKEY ---
        st.divider()
        st.subheader("🔄 Fluxo de Negociação de Energia (Sankey)")
        
        # Agrupar trades por vendedor->comprador para o dia todo
        fluxos = {}
        for t in resultado_mercado.trades:
            origem = str(t.vendedor)
            destino = str(t.comprador)
            key = (origem, destino)
            fluxos[key] = fluxos.get(key, 0.0) + (t.potencia_enviada_kw / 60) # kWh
            
        if fluxos:
            nomes_unicos = list(set([k[0] for k in fluxos.keys()] + [k[1] for k in fluxos.keys()]))
            indice_nome = {nome: i for i, nome in enumerate(nomes_unicos)}
            
            source = [indice_nome[k[0]] for k in fluxos.keys()]
            target = [indice_nome[k[1]] for k in fluxos.keys()]
            value = list(fluxos.values())
            
            fig_sankey = go.Figure(data=[go.Sankey(
                node = dict(
                  pad = 15,
                  thickness = 20,
                  line = dict(color = "black", width = 0.5),
                  label = nomes_unicos,
                  color = "blue"
                ),
                link = dict(
                  source = source,
                  target = target,
                  value = value
              ))])
            st.plotly_chart(fig_sankey, use_container_width=True)
        else:
            st.info("Não houve transações entre as microrredes neste cenário.")
            
        # --- TABELA DE TRADES ---
        if resultado_mercado.trades:
            st.subheader("📋 Histórico de Transações")
            
            df_trades = pd.DataFrame([{
                'Hora': f"{t.periodo//60:02d}:{t.periodo%60:02d}",
                'Vendedor': str(t.vendedor),
                'Comprador': str(t.comprador),
                'Distância (km)': f"{t.distancia_km:.2f}",
                'Energia Enviada (kW)': f"{t.potencia_enviada_kw:.2f}",
                'Energia Recebida (kW)': f"{t.potencia_recebida_kw:.2f}",
                'Perda (%)': f"{(t.fator_perda * 100):.1f}%",
                'Preço (R$/kWh)': f"R$ {t.preco_efetivo_kwh:.3f}",
                'Total Pago (R$)': f"R$ {t.valor_total:.2f}"
            } for t in resultado_mercado.trades[::15]]) # Amostrando a cada 15 min para não travar
            
            st.dataframe(df_trades, use_container_width=True)
            
            st.caption("Amostra de 1 transação a cada 15 minutos de simulação.")
