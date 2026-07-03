import pandas as pd
import unicodedata

def _normalizar(texto: str) -> str:
    return unicodedata.normalize('NFD', str(texto).upper()).encode('ascii', 'ignore').decode()

df = pd.read_excel('exemplos/DADOS MR 4.xlsx', sheet_name=0, header=None)

linha_fontes = None
for i, row in df.iterrows():
    val = _normalizar(str(row.iloc[0])) if pd.notna(row.iloc[0]) else ''
    if val in ('FONTE', 'PV', 'DIESEL', 'BATERIA'):
        linha_fontes = i + 1 if val == 'FONTE' else i
        break

linha_inicio_cargas = 2
linha_fim_cargas = linha_fontes - 1 if linha_fontes is not None else len(df)

cargas = []
for i in range(linha_inicio_cargas, linha_fim_cargas):
    if i >= len(df):
        break
    row = df.iloc[i]
    
    if pd.isna(row.iloc[1:4]).all():
        print(f'Row {i} skipped: all NaN in 1:4 (nome: {row.iloc[0]})')
        continue
        
    nome = row.iloc[0]
    if pd.isna(nome) or str(nome).strip() == '':
        nome = f'Carga Extra {i}'
        
    def safe_float(v, default):
        if pd.isna(v): return default
        try: return float(v)
        except: return default
        
    potencia   = safe_float(row.iloc[1], 0.0)
    liga       = int(safe_float(row.iloc[2], 0.0))
    desliga    = int(safe_float(row.iloc[3], 1440.0))
    prioridade = int(safe_float(row.iloc[4], 1.0))
    
    if potencia == 0.0 and (pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() == ''):
        print(f'Row {i} skipped: pot=0 and no name')
        continue

    cargas.append({
        'i': i,
        'nome': str(nome).strip()[:100],
        'potencia': potencia,
    })

print('Cargas cadastradas:')
for c in cargas:
    print(f"{c['i']:2d}: {c['nome'][:30]:30s} -> {c['potencia']} kW")
