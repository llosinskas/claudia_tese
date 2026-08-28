import pandas as pd
import re

path = r'c:\Users\lucas\OneDrive\Área de Trabalho\01 - DOCUMENTOS\claudia\claudia_tese v2\pages\Mercado2.py'

ui_comp = '''
    if "comparacao_otm_sazonais" in st.session_state:
        comp_sazonais = st.session_state["comparacao_otm_sazonais"]
        st.divider()
        st.subheader("📊 Comparação Lado a Lado: Heurística vs MILP")
        
        import plotly.graph_objects as go
        import pandas as pd
        
        # Global Summary
        dados_resumo = []
        for estacao in estacoes_simuladas:
            if estacao not in comp_sazonais: continue
            c_orig = sum(comp_sazonais[estacao]["original"].custo_total_por_mg.values())
            c_heur = sum(comp_sazonais[estacao]["heuristica"]["otimizado"].custo_total_por_mg.values())
            c_milp = sum(comp_sazonais[estacao]["milp"]["otimizado"].custo_total_por_mg.values())
            
            dados_resumo.append({
                "Estação": f"{ICONES_ESTACOES.get(estacao, '📅')} {estacao}",
                "Custo Original": c_orig,
                "Custo Heurística": c_heur,
                "Custo MILP": c_milp,
                "Econ. Heurística": c_orig - c_heur,
                "Econ. MILP": c_orig - c_milp,
                "Melhor Método": "MILP" if c_milp <= c_heur else "Heurística"
            })
            
        if dados_resumo:
            df_resumo = pd.DataFrame(dados_resumo)
            st.dataframe(
                df_resumo.style.format({
                    "Custo Original": "R$ {:,.2f}",
                    "Custo Heurística": "R$ {:,.2f}",
                    "Custo MILP": "R$ {:,.2f}",
                    "Econ. Heurística": "R$ {:,.2f}",
                    "Econ. MILP": "R$ {:,.2f}",
                }).highlight_max(subset=["Econ. Heurística", "Econ. MILP"], color="lightgreen", axis=1),
                width='stretch', hide_index=True
            )
            
            # Detailed comparison chart
            nomes_est = [d["Estação"] for d in dados_resumo]
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(name="Original", x=nomes_est, y=[d["Custo Original"] for d in dados_resumo]))
            fig_comp.add_trace(go.Bar(name="Heurística", x=nomes_est, y=[d["Custo Heurística"] for d in dados_resumo]))
            fig_comp.add_trace(go.Bar(name="MILP", x=nomes_est, y=[d["Custo MILP"] for d in dados_resumo]))
            fig_comp.update_layout(title="Custo Total por Estação (Comparativo)", barmode='group')
            st.plotly_chart(fig_comp, use_container_width=True)
'''

with open(path, 'a', encoding='utf-8') as f:
    f.write(ui_comp)

print("UI component appended to Mercado2.py")
