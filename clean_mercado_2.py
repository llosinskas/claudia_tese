import re

path = r'c:\Users\lucas\OneDrive\Área de Trabalho\01 - DOCUMENTOS\claudia\claudia_tese v2\pages\Mercado2.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace block where OtimizadorMILPPosDia is called for Sem Penalidades
pattern_exec = r'# 3\. Executar MILP \(Sem Penalidades\).*?res_milp_sp = otm_milp_sp\.otimizar\(resultado_est, callback=callback_otm\)\n'
text = re.sub(pattern_exec, '', text, flags=re.DOTALL)

# Remove from dictionary:
text = text.replace('\"milp_sem_penal\": res_milp_sp,', '')

# Remove button
pattern_btn = r'with col_btn3:.*?width=\'stretch\', key=\"saz_otm_milp_sem_penal\",\n\s+\)'
text = re.sub(pattern_btn, '', text, flags=re.DOTALL)

# Replace 'or otimizar_milp_sem_penal'
text = text.replace(' or otimizar_milp_sem_penal', '')

# In 'if otimizar_milp_sem_penal:' blocks, we just remove the block
pattern_if = r'if otimizar_milp_sem_penal:\s+tipo_nome = \"MILP \(Sem Penalidades\)\"'
text = re.sub(pattern_if, '', text)

# Success message
text = text.replace('vs MILP c/ Penalidades vs MILP Sem Penalidades', 'vs MILP')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Regex safe cleanup done')
