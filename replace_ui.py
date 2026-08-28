import pandas as pd
import re

path = r'c:\Users\lucas\OneDrive\Área de Trabalho\01 - DOCUMENTOS\claudia\claudia_tese v2\pages\Mercado2.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

start_idx = text.find('    if "comparacao_otm_sazonais" in st.session_state:')

ui_comp = '''    if "comparacao_otm_sazonais" in st.session_state:
        comp_sazonais = st.session_state["comparacao_otm_sazonais"]
        st.divider()
        st.subheader("📊 Comparação Lado a Lado: Heurística vs MILP (Com e Sem P2P)")
        
        import plotly.graph_objects as go
        import pandas as pd
        
        # Global Summary
        dados_resumo = []
        for estacao in estacoes_simuladas:
            if estacao not in comp_sazonais: continue
            # Isolado
            iso_orig = sum(comp_sazonais[estacao]["original"].custo_isolado_por_mg.values())
            iso_heur = sum(comp_sazonais[estacao]["heuristica"]["otimizado"].custo_isolado_por_mg.values())
            iso_milp = sum(comp_sazonais[estacao]["milp"]["otimizado"].custo_isolado_por_mg.values())
            
            # Com Comercialização
            com_orig = sum(comp_sazonais[estacao]["original"].custo_total_por_mg.values())
            com_heur = sum(comp_sazonais[estacao]["heuristica"]["otimizado"].custo_total_por_mg.values())
            com_milp = sum(comp_sazonais[estacao]["milp"]["otimizado"].custo_total_por_mg.values())
            
            dados_resumo.append({
                "Estação": f"{ICONES_ESTACOES.get(estacao, '📅')} {estacao}",
                "Orig (Iso)": iso_orig,
                "Orig (P2P)": com_orig,
                "Heur (Iso)": iso_heur,
                "Heur (P2P)": com_heur,
                "MILP (Iso)": iso_milp,
                "MILP (P2P)": com_milp,
            })
            
        if dados_resumo:
            df_resumo = pd.DataFrame(dados_resumo)
            st.dataframe(
                df_resumo.style.format({
                    "Orig (Iso)": "R$ {:,.2f}",
                    "Orig (P2P)": "R$ {:,.2f}",
                    "Heur (Iso)": "R$ {:,.2f}",
                    "Heur (P2P)": "R$ {:,.2f}",
                    "MILP (Iso)": "R$ {:,.2f}",
                    "MILP (P2P)": "R$ {:,.2f}",
                }),
                width='stretch', hide_index=True
            )
            
            # Bar chart comparing P2P vs Isolated
            st.markdown("#### Custos: Operação Isolada (Sem Mercado)")
            nomes_est = [d["Estação"] for d in dados_resumo]
            
            # Custo Isolado
            fig_iso = go.Figure()
            fig_iso.add_trace(go.Bar(name="Original (Isolado)", x=nomes_est, y=[d["Orig (Iso)"] for d in dados_resumo], marker_color='gray'))
            fig_iso.add_trace(go.Bar(name="Heurística (Isolado)", x=nomes_est, y=[d["Heur (Iso)"] for d in dados_resumo], marker_color='orange'))
            fig_iso.add_trace(go.Bar(name="MILP (Isolado)", x=nomes_est, y=[d["MILP (Iso)"] for d in dados_resumo], marker_color='purple'))
            fig_iso.update_layout(barmode='group')
            st.plotly_chart(fig_iso, use_container_width=True)
            
            # Custo Mercado P2P
            st.markdown("#### Custos: Com Mercado P2P")
            fig_p2p = go.Figure()
            fig_p2p.add_trace(go.Bar(name="Original (P2P)", x=nomes_est, y=[d["Orig (P2P)"] for d in dados_resumo], marker_color='lightgray'))
            fig_p2p.add_trace(go.Bar(name="Heurística (P2P)", x=nomes_est, y=[d["Heur (P2P)"] for d in dados_resumo], marker_color='gold'))
            fig_p2p.add_trace(go.Bar(name="MILP (P2P)", x=nomes_est, y=[d["MILP (P2P)"] for d in dados_resumo], marker_color='blue'))
            fig_p2p.update_layout(barmode='group')
            st.plotly_chart(fig_p2p, use_container_width=True)
'''

text = text[:start_idx] + ui_comp

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("UI component replaced successfully")
