import pandas as pd, os, unicodedata, shutil, json

def normalizar(t):
    return unicodedata.normalize('NFD', str(t).upper()).encode('ascii','ignore').decode()

PASTA = 'exemplos'
ESTACOES_MAP = {'VERAO':'Verao','OUTONO':'Outono','INVERNO':'Inverno','PRIMAVERA':'Primavera'}

resultados = {}

for arq_idx, arq in enumerate(['DADOS MR 1.xlsx','DADOS MR 2.xlsx','DADOS MR 3.xlsx','DADOS MR 4.xlsx'], 1):
    src = os.path.join(PASTA, arq)
    dst = f'_tmp_rev{arq_idx}.xlsx'
    shutil.copy2(src, dst)
    xl = pd.ExcelFile(dst)
    mg_key = f'MG-0{arq_idx}'
    resultados[mg_key] = {}

    for sheet in xl.sheet_names:
        nome_norm = normalizar(sheet)
        estacao = next((v for k, v in ESTACOES_MAP.items() if k in nome_norm), None)
        if not estacao:
            continue

        df = xl.parse(sheet, header=None)

        # Encontrar linha de fontes
        linha_fontes = None
        for i, row in df.iterrows():
            val = normalizar(str(row.iloc[0])) if pd.notna(row.iloc[0]) else ''
            if val in ('FONTE', 'PV', 'DIESEL', 'BATERIA'):
                linha_fontes = i + 1 if val == 'FONTE' else i
                break

        fim_cargas = linha_fontes - 1 if linha_fontes else len(df)

        # Cargas
        cargas = []
        for i in range(2, fim_cargas):
            if i >= len(df):
                break
            row = df.iloc[i]
            nome = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
            if not nome:
                continue
            try:
                pot  = float(row.iloc[1]) if pd.notna(row.iloc[1]) else 0.0
                liga = int(float(row.iloc[2])) if pd.notna(row.iloc[2]) else 0
                des  = int(float(row.iloc[3])) if pd.notna(row.iloc[3]) else 1440
                pri  = int(float(row.iloc[4])) if pd.notna(row.iloc[4]) else 1
                cargas.append({'nome': nome, 'pot': pot, 'liga': liga, 'desliga': des, 'pri': pri})
            except Exception:
                pass

        # Fontes
        solar = {}
        diesel = {}
        bateria = {}
        tarifa = None
        if linha_fontes is not None:
            for i in range(linha_fontes, len(df)):
                row = df.iloc[i]
                fonte = normalizar(str(row.iloc[0])) if pd.notna(row.iloc[0]) else ''
                if 'PV' in fonte or 'SOLAR' in fonte or 'FOTOVOLTAICO' in fonte:
                    try:
                        solar = {'pot': float(row.iloc[1]), 'custo': float(row.iloc[2])}
                    except Exception:
                        pass
                elif 'DIESEL' in fonte or 'GERADOR' in fonte:
                    try:
                        diesel = {
                            'pot':    float(row.iloc[1]),
                            'custo':  float(row.iloc[2]),
                            'tanque': float(row.iloc[4]) if pd.notna(row.iloc[4]) else None,
                            'c100':   float(row.iloc[5]) if pd.notna(row.iloc[5]) else None,
                            'c75':    float(row.iloc[6]) if pd.notna(row.iloc[6]) else None,
                            'c50':    float(row.iloc[7]) if pd.notna(row.iloc[7]) else None,
                        }
                    except Exception:
                        pass
                elif 'BATERIA' in fonte:
                    try:
                        bateria = {
                            'pot':  float(row.iloc[1]),
                            'custo': float(row.iloc[2]),
                            'cap':  float(row.iloc[8]) if pd.notna(row.iloc[8]) else None,
                            'dod':  str(row.iloc[9]) if pd.notna(row.iloc[9]) else None,
                        }
                    except Exception:
                        pass
                elif 'CONCESS' in fonte:
                    try:
                        tarifa = float(row.iloc[2])
                    except Exception:
                        pass

        resultados[mg_key][estacao] = {
            'n_cargas': len(cargas),
            'cargas':   cargas,
            'solar':    solar,
            'diesel':   diesel,
            'bateria':  bateria,
            'tarifa':   tarifa,
        }

    xl.close()
    os.remove(dst)

# Salvar JSON completo
with open('_revisao_exemplos.json', 'w', encoding='utf-8') as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)

# Imprimir resumo por MG e estação
for mg, estacoes in resultados.items():
    print(f'\n========== {mg} ==========')
    for est, dados in estacoes.items():
        s = dados['solar']
        d = dados['diesel']
        b = dados['bateria']
        n = dados['n_cargas']
        t = dados['tarifa']
        sp = s.get('pot', '?')
        sc = s.get('custo', '?')
        dp = d.get('pot', '?')
        dt = d.get('tanque', '?')
        bp = b.get('pot', '?')
        bc = b.get('cap', '?')
        bd = b.get('dod', '?')
        print(f'  [{est}] cargas={n} | Solar={sp}kW custo={sc} | Diesel={dp}kW tanque={dt}L | Bat={bp}kW cap={bc}kWh DOD={bd} | Tarifa={t}')
        for c in dados['cargas']:
            flag = ' <<IRRIGACAO>>' if normalizar(c['nome']).find('IRRIG') >= 0 else ''
            print(f'    {c["nome"][:50]:52s} {c["pot"]:6.2f}kW  {c["liga"]:4d}-{c["desliga"]:4d}  P{c["pri"]}{flag}')

print('\nJSONs salvo em _revisao_exemplos.json')
