path = r'c:\Users\lucas\OneDrive\Área de Trabalho\01 - DOCUMENTOS\claudia\claudia_tese v2\pages\Mercado2.py'
import re

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the MILP Sem Penalidades execution block
content = re.sub(r'# 3\. Executar MILP \(Sem Penalidades\).*?res_milp_sp = otm_milp_sp\.otimizar\(resultado_est, callback=callback_otm\)\n', '', content, flags=re.DOTALL)

# Remove references in dictionary
content = content.replace('\"milp_sem_penal\": res_milp_sp,', '')

# Remove in UI message
content = content.replace('vs MILP c/ Penalidades vs MILP Sem Penalidades', 'vs MILP')

# Remove UI metric columns
content = re.sub(r'economia_milp_sp =.*?\n', '', content)
content = re.sub(r'cols_otm\[\d\].metric\(\"Economia MILP \(Sem Penal\)\".*?\)\n', '', content, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Regex cleanup done.')
