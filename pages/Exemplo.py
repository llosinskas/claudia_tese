import streamlit as st
import json
from models.Microrrede import Microrrede, Bateria, Biogas, Diesel, Carga, Solar, Concessionaria, CargaFixa
from models.CRUD import Ler, Criar, Atualizar, Deletar
from Tools.geradorSolar import gerar_solar



@staticmethod
def exemplo_microrredes():
    microrrede1 = Microrrede(
        nome="MG - 01",
        coordenada_x=-31.85,
        coordenada_y=-52.90,
        bateria = Bateria(potencia=60, capacidade=350, bateria="LiFePO4", nivel=100, eficiencia=95, capacidade_min=10, capacidade_max=90, custo_kwh=0.8),
        solar=Solar(potencia=potencia_solar, custo_kwh=0.2, curva_geracao=curva_solar_json_str),

        concessionaria=Concessionaria(nome="CEEE - Equatorial",tarifa=0.8, demanda = 0, grupo="B"),
        #biogas = Biogas(potencia=150, custo_por_kWh=0.5,nivel=100, tanque=5000, geracao=2, consumo_50 = 3, consumo_75 = 4, consumo_100 = 5),
        diesel = Diesel(potencia=75, custo_por_kWh=1.7,nivel=100, tanque=500, consumo_50 = 0.125, consumo_75 = 0.1875, consumo_100 = 0.25),
        biogas = None, 
        carga = Carga(cargaFixa=
            [CargaFixa(nome="Ordenha Manhã", potencia=8.5, tempo_liga=300, tempo_desliga=420, prioridade=1), 
             CargaFixa(nome="Ordenha Tarde", potencia=8.5, tempo_liga=960, tempo_desliga=1080, prioridade=1), 
             CargaFixa(nome="Refrigerador", potencia=1, tempo_liga=0, tempo_desliga=1440, prioridade=1), 
             CargaFixa(nome="Irrigação", potencia=7, tempo_liga=600, tempo_desliga=1200, prioridade=2),
             CargaFixa(nome="Gado 1", potencia=5, tempo_liga=420, tempo_desliga=540, prioridade=3), 
             CargaFixa(nome="Gado 2", potencia=5, tempo_liga=780, tempo_desliga=960, prioridade=3), 
             CargaFixa(nome="Gado 3", potencia=1.5, tempo_liga=1080, tempo_desliga=1380, prioridade=3), 
             CargaFixa(nome="Gado 4", potencia=1, tempo_liga=0, tempo_desliga=1440, prioridade=3), 
             CargaFixa(nome="Residencial 1", potencia=26, tempo_liga=1020, tempo_desliga=1380, prioridade=4), 
             CargaFixa(nome="Residencial 2", potencia=13, tempo_liga=660, tempo_desliga=840, prioridade=3),          
             ])
    )
    Criar(microrrede1)

    # Microrrede 2
    coordenada_x = -31.85
    coordenada_y = -52.90
    potencia_solar = 80
    curva_solar = gerar_solar(potencia_solar,coordenada_x, coordenada_y)
    curva_solar_json = curva_solar.tolist()  # 
    curva_solar_json_str = json.dumps(curva_solar_json)  # Convertir a string JSON
   
    microrrede2 = Microrrede(
        nome="MG - 02",
        coordenada_x=coordenada_x,
        coordenada_y=coordenada_y,
        bateria = Bateria(potencia=80, capacidade=450, bateria="LiFePO4", nivel=100, eficiencia=95, capacidade_min=10, capacidade_max=90, custo_kwh=0.7),
        solar=Solar(potencia=potencia_solar, custo_kwh=0.1, curva_geracao=curva_solar_json_str),
        concessionaria=Concessionaria(nome="CEEE equatorial",tarifa=0.8, demanda = 100, grupo="B"),
        biogas = Biogas(potencia=75, custo_por_kWh=0.4,nivel=100, tanque=200, geracao=500, consumo_50 = 0.3, consumo_75 = 0.45, consumo_100 = 0.6),
        diesel = None,

        carga = Carga(cargaFixa=[
            CargaFixa(nome="Ordenha Manhã", potencia=10, tempo_liga=300, tempo_desliga=420, prioridade=1), 
            CargaFixa(nome="Ordenha Tarde", potencia=10, tempo_liga=960, tempo_desliga=1080, prioridade=1), 
            CargaFixa(nome="Refrigerador", potencia=4, tempo_liga=0, tempo_desliga=1440, prioridade=1), 
            CargaFixa(nome="Irrigação 1", potencia=7, tempo_liga=600, tempo_desliga=1200, prioridade=2),
            CargaFixa(nome="Irrigação 2", potencia=20, tempo_liga=600, tempo_desliga=1200, prioridade=2), 
            CargaFixa(nome="Gado Corte 1", potencia=3, tempo_liga=420, tempo_desliga=540, prioridade=3), 
            CargaFixa(nome="Gado Corte 2", potencia=3, tempo_liga=780, tempo_desliga=960, prioridade=3), 
            CargaFixa(nome="Gado Corte 3", potencia=0.5, tempo_liga=0, tempo_desliga=1440, prioridade=3),
            CargaFixa(nome="Residencial 1", potencia=28, tempo_liga=1020, tempo_desliga=1380, prioridade=4), 
            CargaFixa(nome="Residencial 2", potencia=14, tempo_liga=660, tempo_desliga=840, prioridade=4)
            ])
    )
    Criar(microrrede2)
    
    # Microrrede 3
    coordenada_x = -31.95
    coordenada_y = -52.85
    potencia_solar = 45
    curva_solar = gerar_solar(potencia_solar,coordenada_x, coordenada_y)
    curva_solar_json = curva_solar.tolist()  # 
    curva_solar_json_str = json.dumps(curva_solar_json)  # Convertir a string JSON
   
    microrrede3 = Microrrede(
        nome="MG - 03",
        coordenada_x=coordenada_x,
        coordenada_y=coordenada_y,
        bateria = Bateria(potencia=30, capacidade=70, bateria="LiFePO4", nivel=100, eficiencia=95, capacidade_min=10, capacidade_max=90, custo_kwh=0.7),
        solar=Solar(potencia=potencia_solar, custo_kwh=0.15, curva_geracao=curva_solar_json_str),
        concessionaria=Concessionaria(nome="CEEE equatorial",tarifa=0.8, demanda = 100, grupo="B"),
        biogas = Biogas(potencia=75, custo_por_kWh=0.4,nivel=100, tanque=200, geracao=500, consumo_50 = 0.3, consumo_75 = 0.45, consumo_100 = 0.6),
        diesel = Diesel(potencia=30, custo_por_kWh=2.5,nivel=100, tanque=300, consumo_50 = 0.15, consumo_75 = 0.225, consumo_100 = 0.3),

        carga = Carga(cargaFixa=[
            CargaFixa(nome="Ordenha Manhã", potencia=18.5, tempo_liga=300, tempo_desliga=420, prioridade=1), 
            CargaFixa(nome="Ordenha Tarde", potencia=18.5, tempo_liga=960, tempo_desliga=1080, prioridade=1), 
            CargaFixa(nome="Refrigerador", potencia=6, tempo_liga=0, tempo_desliga=1440, prioridade=1), 
            CargaFixa(nome="Residencial 1", potencia=18, tempo_liga=1020, tempo_desliga=1380, prioridade=4),
            CargaFixa(nome="Residencial 2", potencia=9, tempo_liga=660, tempo_desliga=840, prioridade=4), 
            ])
    )

    Criar(microrrede3)

    # Microrrede 4
    coordenada_x = -32.20
    coordenada_y = -53
    potencia_solar = 90
    curva_solar = gerar_solar(potencia_solar,coordenada_x, coordenada_y)
    curva_solar_json = curva_solar.tolist()  # 
    curva_solar_json_str = json.dumps(curva_solar_json)  # Convertir a string JSON
   
    microrrede4 = Microrrede(
        nome="MG - 04",
        coordenada_x=coordenada_x,
        coordenada_y=coordenada_y,
        bateria = Bateria(potencia=80, capacidade=450, bateria="LiFePO4", nivel=100, eficiencia=95, capacidade_min=10, capacidade_max=90, custo_kwh=0.7),
        solar=Solar(potencia=potencia_solar, custo_kwh=0.15, curva_geracao=curva_solar_json_str),
        concessionaria=Concessionaria(nome="CEEE equatorial",tarifa=0.8, demanda = 100, grupo="B"),
        biogas = Biogas(potencia=84, custo_por_kWh=0.4,nivel=100, tanque=500, geracao=462, consumo_50 = 0.3, consumo_75 = 0.45, consumo_100 = 0.6),
        diesel = Diesel(potencia=30, custo_por_kWh=2.5,nivel=100, tanque=300, consumo_50 = 0.15, consumo_75 = 0.225, consumo_100 = 0.3),

        carga = Carga(cargaFixa=[
            CargaFixa(nome="Irrigação 1", potencia=15, tempo_liga=600, tempo_desliga=1200, prioridade=2), 
            CargaFixa(nome="Irrigação 2", potencia=20, tempo_liga=600, tempo_desliga=1200, prioridade=2), 
            CargaFixa(nome="Irrigação 3", potencia=25, tempo_liga=600, tempo_desliga=1200, prioridade=2), 
            CargaFixa(nome="Residencial 1", potencia=24, tempo_liga=1020, tempo_desliga=1380, prioridade=4),
            CargaFixa(nome="Residencial 2", potencia=12, tempo_liga=660, tempo_desliga=840, prioridade=4), 
            ])
    )
    Criar(microrrede4)

def microrrede_artigo():
    # MG1
    coordenada_x = -31.85
    coordenada_y = -52.9
    potencia_solar = 100
    curva_solar = gerar_solar(potencia_solar,coordenada_x, coordenada_y)
    curva_solar_json = curva_solar.tolist()  # 
    curva_solar_json_str = json.dumps(curva_solar_json)  # Convertir a string JSON
   
    MG1 = Microrrede(
        nome="MG - 01",
        coordenada_x=coordenada_x,
        coordenada_y=coordenada_y,
        bateria = Bateria(potencia=30, capacidade=1000, bateria="LiFePO4", nivel=80, eficiencia=95, capacidade_min=20, capacidade_max=80, custo_kwh=0.8),
        solar=Solar(potencia=potencia_solar, custo_kwh=0.3, curva_geracao=curva_solar_json_str),
        concessionaria=Concessionaria(nome="CEEE equatorial",tarifa=0.8, demanda = 100, grupo="B"),
        biogas = Biogas(potencia=0, custo_por_kWh=0.4,nivel=100, tanque=500, geracao=0, consumo_50 = 0.3, consumo_75 = 0.45, consumo_100 = 0.6),
        diesel = Diesel(potencia=5.5, custo_por_kWh=2.0,nivel=100, tanque=40, consumo_50 = 0.4, consumo_75 = 0.35, consumo_100 = 0.3),

        carga = Carga(cargaFixa=[
            #Propriedade 1
            CargaFixa(nome="Ordenha manha", potencia=3.75, tempo_liga=300, tempo_desliga=420, prioridade=1), 
            CargaFixa(nome="Ordenha tarde", potencia=3.75, tempo_liga=960, tempo_desliga=1080, prioridade=1),
            CargaFixa(nome="Refriador pós ordenha manhã", potencia=1.5, tempo_liga=420, tempo_desliga=600, prioridade=1),
            CargaFixa(nome="Resfriador", potencia=0.75, tempo_liga=600, tempo_desliga=960, prioridade=1),
            CargaFixa(nome="Resfriador pós ordenha tarde", potencia=1.5, tempo_liga=1080, tempo_desliga=1260, prioridade=1),
            CargaFixa(nome="Resfriador", potencia=0.75, tempo_liga=1260, tempo_desliga=1439, prioridade=1),
            CargaFixa(nome="Resfriador madrugada", potencia=0.75, tempo_liga=0, tempo_desliga=300, prioridade=1),
            # Propriedade 2
            CargaFixa(nome="Ordenha manhã", potencia=3.75, tempo_liga=300, tempo_desliga=420, prioridade=1),
            CargaFixa(nome="Ordenha tarde", potencia=3.75, tempo_liga=960, tempo_desliga=1080, prioridade=1),
            CargaFixa(nome="Resfriador pós ordenha manhã", potencia=1.5, tempo_liga=420, tempo_desliga=600, prioridade=1),
            CargaFixa(nome="Refrigerador tarde", potencia=0.75, tempo_liga=600, tempo_desliga=960, prioridade=1),
            CargaFixa(nome="Refrigerador ordenha pós ordenha tarde", potencia=1.5, tempo_liga=1080, tempo_desliga=1260, prioridade=1),
            CargaFixa(nome="Refrigarado noite", potencia=0.75, tempo_liga=1260, tempo_desliga=1439, prioridade=1),
            CargaFixa(nome="Refrigerador madrugada", potencia=0.75, tempo_liga=0, tempo_desliga=300, prioridade=1),
            # Propriedade 3
            CargaFixa(nome="Ordenha manhã", potencia=3.75, tempo_liga=300, tempo_desliga=420, prioridade=1),
            CargaFixa(nome="Ordenha tarde", potencia=3.75, tempo_liga=960, tempo_desliga=1080, prioridade=1),
            CargaFixa(nome="Resfriador pós ordenha manhã", potencia=1.5, tempo_liga=420, tempo_desliga=600, prioridade=1),
            CargaFixa(nome="Refrigerador tarde", potencia=0.75, tempo_liga=600, tempo_desliga=960, prioridade=1),
            CargaFixa(nome="Refrigerador ordenha pós ordenha tarde", potencia=1.5, tempo_liga=1080, tempo_desliga=1260, prioridade=1),
            CargaFixa(nome="Refrigarado noite", potencia=0.75, tempo_liga=1260, tempo_desliga=1439, prioridade=1),
            CargaFixa(nome="Refrigerador madrugada", potencia=0.75, tempo_liga=0, tempo_desliga=300, prioridade=1),
            # Propriedade 4
            CargaFixa(nome="Irrigação madrugada", potencia=22, tempo_liga=0, tempo_desliga=300, prioridade=2),
            CargaFixa(nome="Irrigação noite", potencia=22, tempo_liga=1260, tempo_desliga=1439, prioridade=2),
            #Propriedade 5
            CargaFixa(nome="Cerca elétrica", potencia=0.01, tempo_liga=0, tempo_desliga=1439, prioridade=1),
            CargaFixa(nome="Bomba d'água manhã", potencia=1, tempo_liga=360, tempo_desliga=400, prioridade=1),
            CargaFixa(nome="Bomba d'água tarde", potencia=1, tempo_liga=720, tempo_desliga=760, prioridade=2),
            CargaFixa(nome="Bomba d'água noite", potencia=1, tempo_liga=1020, tempo_desliga=1060, prioridade=1),
            CargaFixa(nome="Residencial 1 - pico", potencia=2, tempo_liga=1020, tempo_desliga=1380, prioridade=1),
            CargaFixa(nome="Residencial 2 - pico", potencia=2, tempo_liga=1020, tempo_desliga=1380, prioridade=1),
            CargaFixa(nome="Residencial 3 - pico", potencia=2, tempo_liga=1020, tempo_desliga=1380, prioridade=1),
            CargaFixa(nome="Residencial 4 - pico", potencia=3, tempo_liga=1020, tempo_desliga=1380, prioridade=1),
            CargaFixa(nome="Residencial 5 - pico", potencia=2, tempo_liga=1020, tempo_desliga=1380, prioridade=1),
            CargaFixa(nome="Residencial 1 - Base", potencia=0.4, tempo_liga=0, tempo_desliga=1439, prioridade=1),
            CargaFixa(nome="Residencial 2 - Base", potencia=0.4, tempo_liga=0, tempo_desliga=1439, prioridade=1),
            CargaFixa(nome="Residencial 3 - Base", potencia=0.4, tempo_liga=0, tempo_desliga=1439, prioridade=1),
            CargaFixa(nome="Residencial 4 - Base", potencia=0.5, tempo_liga=0, tempo_desliga=1439, prioridade=1),
            CargaFixa(nome="Residencial 5 - Base", potencia=0.3, tempo_liga=0, tempo_desliga=1439, prioridade=1),

            ])
    )
    Criar(MG1)
    # MG2
    coordenada_x = -31.91
    coordenada_y = -52.9
    potencia_solar = 100
    curva_solar = gerar_solar(potencia_solar,coordenada_x, coordenada_y)
    curva_solar_json = curva_solar.tolist()  # 
    curva_solar_json_str = json.dumps(curva_solar_json)  # Convertir a string JSON
   
    MG2 = Microrrede(
        nome="MG - 02",
        coordenada_x=coordenada_x,
        coordenada_y=coordenada_y,
        bateria = Bateria(potencia=30, capacidade=1000, bateria="LiFePO4", nivel=80, eficiencia=95, capacidade_min=20, capacidade_max=80, custo_kwh=0.8),
        solar=Solar(potencia=potencia_solar, custo_kwh=0.3, curva_geracao=curva_solar_json_str),
        concessionaria=Concessionaria(nome="CEEE equatorial",tarifa=0.8, demanda = 100, grupo="B"),
        biogas = Biogas(potencia=0, custo_por_kWh=0.4,nivel=100, tanque=500, geracao=0, consumo_50 = 0.3, consumo_75 = 0.45, consumo_100 = 0.6),
        diesel = Diesel(potencia=5.5, custo_por_kWh=2.0,nivel=100, tanque=40, consumo_50 = 0.4, consumo_75 = 0.35, consumo_100 = 0.3),

        carga = Carga(cargaFixa=[
            CargaFixa(nome="Ordenha manha", potencia=12.5, tempo_liga=300, tempo_desliga=420, prioridade=1), 
            CargaFixa(nome="Ordenha tarde", potencia=12.5, tempo_liga=960, tempo_desliga=1080, prioridade=1),
            CargaFixa(nome="Resfriador pós ordenha manhã", potencia=5, tempo_liga=420, tempo_desliga=600, prioridade=1),
            CargaFixa(nome="Resfriador", potencia=2.5, tempo_liga=600, tempo_desliga=960, prioridade=1),
            CargaFixa(nome="Resfriador pós ordenha Tarde", potencia=5, tempo_liga=1080, tempo_desliga=1260, prioridade=1),
            CargaFixa(nome="Refregerador Noite", potencia=2.5, tempo_liga=1260, tempo_desliga=1439, prioridade=1),
            CargaFixa(nome="Refrigerador Madrugada", potencia=2.5, tempo_liga=0, tempo_desliga=300, prioridade=1),
            #Propriedade 2
            CargaFixa(nome="Irrigação Madrugada", potencia=66.6, tempo_liga=0, tempo_desliga=300, prioridade=2),
            CargaFixa(nome="Irrigação madrugada", potencia=66.6, tempo_liga=1260, tempo_desliga=1439, prioridade=2),
            # Propriedade 3
            CargaFixa(nome="Irrigação Madrugada 1", potencia=5, tempo_liga=1260, tempo_desliga=1440, prioridade=2), 
            # Propriedade 4
            CargaFixa(nome="Cerca elétrica", potencia=0.01, tempo_liga=0, tempo_desliga=1439, prioridade=1),
            CargaFixa(nome="Bomba de água manhã", potencia=1, tempo_liga=360, tempo_desliga=400, prioridade=1),
            CargaFixa(nome="Bomba d'água Meio dia", potencia=1, tempo_liga=720, tempo_desliga=750, prioridade=2),
            CargaFixa(nome="Bomba d'água Noite", potencia=1, tempo_liga=1020, tempo_desliga=1060, prioridade=2),
            CargaFixa(nome="Residencial - Propriedade 1", potencia=4, tempo_liga=1020, tempo_desliga=1380, prioridade=1),
            CargaFixa(nome="Residencial - Propriedade 2", potencia=6, tempo_liga=1020, tempo_desliga=1380, prioridade=1),
            CargaFixa(nome="Residencial - Propriedade 3", potencia=8, tempo_liga=1020, tempo_desliga=1380, prioridade=1),
            CargaFixa(nome="Residencial - Propriedade 4", potencia=3, tempo_liga=1020, tempo_desliga=1380, prioridade=1),
            CargaFixa(nome="Residencial - Propriedade 1 - Base", potencia=0.5, tempo_liga=0, tempo_desliga=1439, prioridade=1),
            CargaFixa(nome="Residencial - Propriedade 2 - Base", potencia=0.6, tempo_liga=0, tempo_desliga=1439, prioridade=1),
            CargaFixa(nome="Residencial - Propriedade 3 - Base", potencia=0.8, tempo_liga=0, tempo_desliga=1439, prioridade=1),
            CargaFixa(nome="Residencial - Propriedade 2 - Base", potencia=0.5, tempo_liga=0, tempo_desliga=1439, prioridade=1),
            ])
    )
    Criar(MG2)
st.set_page_config(
    page_title="Página de exemplo de sistema de microrredes")

st.title("Exemplos de sistemas de microrredes")
col1, col2 = st.columns([3, 2])
# Microrrede 1:
col1.subheader("Microrrede 1")
col1.write("""
- **Localização:** Coordenadas (X: -31.19, Y: -54.92)
- **Componentes:**
    - Gerador Diesel: Não possui
    - Gerador Biogás: Não possui
    - Banco de Baterias: 200 kWh, Tipo: Li-ion
    - Fonte Solar: 80 kW
    - Demanda contratada: 50 kW
    - Cargas: 
        - Residencial: 150 kW
        - Comercial: 100 kW
    """)

col1.subheader("Microrrede 2")
col1.write("""
- **Localização:** Coordenadas (X: -30.00, Y: -54.92)
- **Componentes:**
    - Gerador Diesel: Não possui
    - Gerador Biogás: Não possui
    - Banco de Baterias: 200 kWh, Tipo: Li-ion
    - Fonte Solar: 80 kW
    - Demanda contratada: 50 kW
    - Cargas: 
        - Residencial: 150 kW
        - Comercial: 100 kW
    """)

col1.subheader("Microrrede 3")
col1.write("""
- **Localização:** Coordenadas (X: -32.00, Y: -54.92)
- **Componentes:**
    - Gerador Diesel: Não possui
    - Gerador Biogás: Não possui
    - Banco de Baterias: 200 kWh, Tipo: Li-ion
    - Fonte Solar: 80 kW
    - Demanda contratada: 50 kW
    - Cargas: 
        - Residencial: 150 kW
        - Comercial: 100 kW
    """)

col1.subheader("Microrrede 4")
col1.write("""
- **Localização:** Coordenadas (X: -34, Y: -54.92)
- **Componentes:**
    - Gerador Diesel: Não possui
    - Gerador Biogás: Não possui
    - Banco de Baterias: 200 kWh, Tipo: Li-ion
    - Fonte Solar: 80 kW
    - Demanda contratada: 50 kW
    - Cargas: 
        - Residencial: 150 kW
        - Comercial: 100 kW
    """)

if col2.button("Limpar"):
    gerador  = gerar_solar(80, -31.19, -54.92)
    print("Geração solar de exemplo gerada para a microrrede 1")
    col2.line_chart(gerador)
    
if col2.button("Gerar Exemplo"):
    # Microrrede 1
    potencia_solar = 60
    curva_solar = gerar_solar(potencia_solar, -31.85, -52.90)  
    curva_solar_json = curva_solar.tolist()  # 
    curva_solar_json_str = json.dumps(curva_solar_json)  # Convertir a string JSON
    microrrede_artigo()
