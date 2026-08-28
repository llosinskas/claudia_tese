import re

path = r'c:\Users\lucas\OneDrive\Área de Trabalho\01 - DOCUMENTOS\claudia\claudia_tese v2\pages\Mercado2.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Add the third button
btn_code = '''    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        otimizar_heuristica = st.button(
            "⚡ Otimização Heurística", type="secondary",
            width='stretch', key="saz_otm_heur",
        )
    with col_btn2:
        otimizar_milp = st.button(
            "🧠 Otimização MILP", type="secondary",
            width='stretch', key="saz_otm_milp",
        )
    with col_btn3:
        comparar_todos = st.button(
            "⚖️ Comparar Heurística vs MILP", type="primary",
            width='stretch', key="saz_otm_comp_todos",
        )
'''
# We will replace the existing col_btn1, col_btn2 block
text = re.sub(r'    col_btn1, col_btn2 = st\.columns\(2\).*?otimizar = otimizar_heuristica or otimizar_milp',
              btn_code + '\n    otimizar = otimizar_heuristica or otimizar_milp\n',
              text, flags=re.DOTALL)

# Now, add the execution block for comparar_todos
# We can put it right before if otimizar:
comp_exec = '''
    if comparar_todos:
        from mercado.simulacao_simultanea import OtimizadorPosDia, OtimizadorMILPPosDia
        comp_otm_sazonais = {}
        status_otm = st.empty()
        mgs_por_est = st.session_state.get("mgs_por_estacao", {})
        
        for idx_est, estacao in enumerate(estacoes_simuladas):
            status_otm.info(f"Comparando {ICONES_ESTACOES.get(estacao, '📅')} {estacao} ({idx_est + 1}/{len(estacoes_simuladas)})...")
            resultado_est = resultados_sazonais[estacao]["resultado"]
            mgs_da_estacao = mgs_por_est.get(estacao, [])
            
            def get_frescas():
                with _crud.session.no_autoflush:
                    frescas = [Ler_Objeto(Microrrede, mg.id) for mg in mgs_da_estacao]
                _crud.session.rollback()
                return frescas
                
            def callback_otm(msg):
                status_otm.info(f"{ICONES_ESTACOES.get(estacao, '📅')} {estacao}: {msg}")
                
            # Heuristica
            mgs_heur = get_frescas()
            otm_heur = OtimizadorPosDia(microrredes=mgs_heur, config=config, margem_venda=margem, coef_perda_km=coef_perda)
            callback_otm("Rodando Heurística...")
            res_heur = otm_heur.otimizar(resultado_est, callback=callback_otm)
            
            # MILP
            mgs_milp = get_frescas()
            otm_milp = OtimizadorMILPPosDia(microrredes=mgs_milp, config=config, margem_venda=margem, coef_perda_km=coef_perda, aplicar_penalidades=True)
            callback_otm("Rodando MILP...")
            res_milp = otm_milp.otimizar(resultado_est, callback=callback_otm)
            
            comp_otm_sazonais[estacao] = {
                "original": resultado_est,
                "heuristica": res_heur,
                "milp": res_milp
            }
            
        st.session_state["comparacao_otm_sazonais"] = comp_otm_sazonais
        if "resultados_otm_sazonais" in st.session_state:
            del st.session_state["resultados_otm_sazonais"]
        status_otm.success("Comparação Completa concluída!")

'''
text = text.replace('    if otimizar:\n', comp_exec + '    if otimizar:\n')

# UI Rendering for comp_otm_sazonais
ui_comp = '''
    if "comparacao_otm_sazonais" in st.session_state:
        comp_sazonais = st.session_state["comparacao_otm_sazonais"]
        st.subheader("📊 Comparação: Heurística vs MILP")
        
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
# Add rendering UI at the very end of the main column (before # --- RELATÓRIO P2P ---)
if '# --- RELATÓRIO P2P ---' in text:
    text = text.replace('# --- RELATÓRIO P2P ---', ui_comp + '\n        # --- RELATÓRIO P2P ---')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Comparacao button and UI injected.")
