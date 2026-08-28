import re

path = r'c:\Users\lucas\OneDrive\Área de Trabalho\01 - DOCUMENTOS\claudia\claudia_tese v2\pages\Mercado2.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Lines to remove entirely
lines = content.split('\n')
new_lines = []
skip = False
for i, line in enumerate(lines):
    l = line.lower()
    
    # 1. Remove the button for "Sem Penalidades"
    if 'otimizar_milp_sem_penal = st.button(' in line:
        skip = True
        continue
    if skip and ('key="saz_otm_milp_sem_penal"' in line or ')' in line):
        if ')' in line:
            skip = False
        continue
    if skip:
        continue
        
    # Remove the elif that handles otimizar_milp_sem_penal
    if 'elif otimizar_heuristica or otimizar_milp or otimizar_milp_sem_penal:' in line:
        line = line.replace(' or otimizar_milp_sem_penal', '')
        
    if 'if otimizar_milp_sem_penal:' in line:
        skip = True
        continue
    if skip and 'tipo_nome = "MILP (Sem Penalidades)"' in line:
        skip = False
        continue

    # Remove metrics calculations
    if 'sum(_get_custos_dict(comp_sazonais[e]["milp_sem_penal"]' in line:
        # Just skip these block stats. Usually they span multiple lines.
        continue
    if 'for e in estacoes_simuladas if e in comp_sazonais and "milp_sem_penal"' in line:
        continue
        
    if 'st.info(f"🎯 **Cargas MILP (Sem Penal.):**' in line:
        continue
        
    if 'c_msp = ' in line: continue
    if 'n_mov_msp = ' in line: continue
    if 'MILP Sem Penal. (R$)' in line: continue
    
    if 'custos_milp_sp_list =' in line: skip = True; continue
    if skip and 'estacoes_simuladas if e in comp_sazonais]' in line: skip = False; continue
    
    if 'name="MILP (Sem Penal.)"' in line: continue
    if 'name="Econ. MILP (Sem Penal.)"' in line: continue
    
    if 'res_msp = ' in line: continue
    
    if 'vencedor = "🎯 MILP (Sem Penal.)"' in line: continue
    
    if 'for m in d_est.get("milp_sem_penal"' in line: skip = True; continue
    if skip and 'h_milp_sp = ' in line: skip = False; continue
    
    if 'MILP Sem Penal.": h_milp_sp,' in line: continue
    
    if 'name="Demanda MILP (Sem Penal.)"' in line: continue
    if 'name="MILP (Sem Penal.)"' in line: continue
    
    if '("Otimização MILP (Sem Penalidades)", "milp_sem_penal"),' in line: continue
    
    if 'else: # milp_sem_penal' in line: skip = True; continue
    if skip and 'res_detalhe = ' in line and 'otimizado' in line: skip = False; continue
    
    if 'milp_sem_penal' in line.lower() and not line.strip().startswith('#'):
        # If there are still random ones, just comment them
        # line = '# ' + line
        pass
        
    new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print("Cleaned Mercado2 UI.")
