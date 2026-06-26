import json

with open('parsed_data.json', 'r', encoding='utf-8') as f:
    dados = json.load(f)

code = f'''import streamlit as st
import json
from models.Microrrede import Microrrede, Bateria, Biogas, Diesel, Carga, Solar, Concessionaria, CargaFixa
from models.CRUD import Ler, Criar, Criar_Varios, Atualizar, Deletar
from Tools.Solar.gerar_curva_solar_sazonal import gerar_curvas_sazonais

@staticmethod
def exemplo_microrredes():
    dados = {json.dumps(dados, ensure_ascii=False, indent=8)}
    
    coordenadas = {{
        \"MG - 01\": (-31.85, -52.90),
        \"MG - 02\": (-31.51, -52.49),
        \"MG - 03\": (-31.26, -53.06),
        \"MG - 04\": (-31.23, -52.40)
    }}

    mgs = []
    for mg_nome, mg_dados in dados.items():
        c_x, c_y = coordenadas.get(mg_nome, (-31.85, -52.90))
        
        p_sol_ref = mg_dados[\"Verão\"][\"solar\"][\"potencia\"]
        if p_sol_ref == 0: p_sol_ref = 100
        curvas = gerar_curvas_sazonais(latitude=c_x, longitude=c_y, potencia_kw=p_sol_ref, eficiencia=0.8, estacoes=[\"Verão\", \"Outono\", \"Inverno\", \"Primavera\"])
        
        for estacao, cfg in mg_dados.items():
            bateria = Bateria(
                potencia=cfg[\"bateria\"][\"potencia\"], 
                capacidade=cfg[\"bateria\"][\"capacidade\"], 
                bateria=\"LiFePO4\", nivel=100, eficiencia=95, capacidade_min=10, capacidade_max=90, 
                custo_kwh=cfg[\"bateria\"][\"custo\"]
            )
            solar = Solar(
                potencia=cfg[\"solar\"][\"potencia\"], 
                custo_kwh=cfg[\"solar\"][\"custo\"], 
                curva_geracao=json.dumps(curvas[estacao].tolist())
            )
            concessionaria = Concessionaria(
                nome=\"CEEE - Equatorial\", 
                tarifa=cfg[\"tarifa\"], 
                demanda=100, grupo=\"B\"
            )
            diesel = Diesel(
                potencia=cfg[\"diesel\"][\"potencia\"], 
                custo_por_kWh=cfg[\"diesel\"][\"custo\"], 
                nivel=100, tanque=500, consumo_50=0.125, consumo_75=0.1875, consumo_100=0.25
            )
            
            cargas_fixas = []
            for c in cfg[\"cargas\"]:
                cargas_fixas.append(
                    CargaFixa(nome=c[\"nome\"][:100], potencia=c[\"potencia\"], tempo_liga=c[\"liga\"], tempo_desliga=c[\"desliga\"], prioridade=c[\"prioridade\"])
                )
            
            mg = Microrrede(
                nome=mg_nome,
                estacao=estacao,
                coordenada_x=c_x,
                coordenada_y=c_y,
                bateria=bateria,
                solar=solar,
                concessionaria=concessionaria,
                diesel=diesel,
                biogas=None,
                carga=Carga(cargaFixa=cargas_fixas)
            )
            mgs.append(mg)
    Criar_Varios(mgs)

def microrrede_artigo():
    estacoes = [\"Verão\", \"Outono\", \"Inverno\", \"Primavera\"]
    coordenada_x = -31.85
    coordenada_y = -52.9
    potencia_solar = 100
    curvas = gerar_curvas_sazonais(latitude=coordenada_x, longitude=coordenada_y, potencia_kw=potencia_solar, eficiencia=0.8, estacoes=estacoes)
   
    for est in estacoes:
        MG1 = Microrrede(
            nome=\"MG - 01\",
            estacao=est,
            coordenada_x=coordenada_x,
            coordenada_y=coordenada_y,
            bateria=Bateria(potencia=30, capacidade=100, bateria=\"LiFePO4\", nivel=80, eficiencia=95, capacidade_min=20, capacidade_max=80, custo_kwh=0.5),
            solar=Solar(potencia=potencia_solar, custo_kwh=0.3, curva_geracao=json.dumps(curvas[est].tolist())),
            concessionaria=Concessionaria(nome=\"CEEE equatorial\", tarifa=0.87, demanda=100, grupo=\"B\"),
            biogas=Biogas(potencia=0, custo_por_kWh=0.4, nivel=100, tanque=500, geracao=0, consumo_50=0.3, consumo_75=0.45, consumo_100=0.6),
            diesel=Diesel(potencia=5.5, custo_por_kWh=2.0, nivel=100, tanque=40, consumo_50=0.4, consumo_75=0.35, consumo_100=0.3),
            carga=Carga(cargaFixa=[
                CargaFixa(nome=\"Ordenha manha\", potencia=3.75, tempo_liga=300, tempo_desliga=420, prioridade=1), 
                CargaFixa(nome=\"Ordenha tarde\", potencia=3.75, tempo_liga=960, tempo_desliga=1080, prioridade=1),
                CargaFixa(nome=\"Refriador pós ordenha manhã\", potencia=1.5, tempo_liga=420, tempo_desliga=600, prioridade=1),
                CargaFixa(nome=\"Resfriador\", potencia=0.75, tempo_liga=600, tempo_desliga=960, prioridade=1),
                CargaFixa(nome=\"Cerca elétrica\", potencia=0.01, tempo_liga=0, tempo_desliga=1439, prioridade=1)
            ])
        )
        Criar(MG1)


# Configuração da Interface Streamlit
st.set_page_config(page_title=\"Página de exemplo de sistema de microrredes\")
st.title(\"Exemplos de sistemas de microrredes\")

col1, col2 = st.columns([3, 2])

col1.subheader(\"Microrrede 1 - Cerrito\")
col1.write(\"\"\"
- **Localização:** Coordenadas (X: -31.85, Y: -52.90)
- **Componentes:** Gerados a partir do arquivo MR 1.xlsx
    \"\"\")

col1.subheader(\"Microrrede 2 - Pedro Osório\")
col1.write(\"\"\"
- **Localização:** Coordenadas (X: -31.51, Y: -52.49)
- **Componentes:** Gerados a partir do arquivo MR 2.xlsx
    \"\"\")

col1.subheader(\"Microrrede 3 - Piratini\")
col1.write(\"\"\"
- **Localização:** Coordenadas (X: -31.26, Y: -53.06)
- **Componentes:** Gerados a partir do arquivo MR 3.xlsx
    \"\"\")

col1.subheader(\"Microrrede 4 - Canguçu\")
col1.write(\"\"\"
- **Localização:** Coordenadas (X: -31.23, Y: -52.40)
- **Componentes:** Gerados a partir do arquivo MR 4.xlsx
    \"\"\")

if col2.button(\"Gerar Geração Solar (Teste)\"):
    curvas = gerar_curvas_sazonais(latitude=-31.85, longitude=-52.90, potencia_kw=100, eficiencia=0.8, estacoes=[\"Verão\"])
    print(\"Geração solar de exemplo gerada para a microrrede 1 (Verão)\")
    col2.line_chart(curvas[\"Verão\"])
    
if col2.button(\"Gerar Exemplo\"):
    with st.spinner(\"Gerando exemplos carregados das planilhas para Verão, Outono, Inverno e Primavera...\"):
        exemplo_microrredes()
    st.success(\"Exemplos criados com sucesso! Verifique a aba Microrredes ou Mercado 2.\")
'''

with open('pages/Exemplo.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Exemplo.py generated!')
