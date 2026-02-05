import streamlit as st
import json
from models.Microrrede import Microrrede, Bateria, Biogas, Diesel, Carga, Solar, Concessionaria, CargaFixa
from models.CRUD import Ler, Criar, Atualizar, Deletar
from Tools.geradorSolar import gerar_solar
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
    curva_solar = gerar_solar(80, -31.19, -54.92)
    curva_solar_json = curva_solar.tolist()  # 
    curva_solar_json_str = json.dumps(curva_solar_json)  # Convertir a string JSON

    microrrede1 = Microrrede(
        nome="Microrrede 1",
        coordenada_x=-31.19,
        coordenada_y=-54.92,
        bateria = Bateria(potencia=100, capacidade=200, bateria="Li-ion", nivel=100, eficiencia=90, capacidade_min=20, capacidade_max=100, custo_kwh=0.2),
        solar=Solar(potencia=80, custo_kwh=0.1, curva_geracao=curva_solar_json_str),
        concessionaria=Concessionaria(nome="Enel-SP",tarifa=0.3, demanda = 100, grupo="B"),
        biogas = Biogas(potencia=150, custo_por_kWh=0.5,nivel=100, tanque=5000, geracao=2, consumo_50 = 3, consumo_75 = 4, consumo_100 = 5),
        diesel = Diesel(potencia=200, custo_por_kWh=0.7,nivel=100, tanque=8000, consumo_50 = 4, consumo_75 = 5, consumo_100 = 6),

        carga = Carga(cargaFixa=
            [CargaFixa(nome="Irrigação", potencia=150, tempo_liga=0, tempo_desliga=300, prioridade=1), 
             CargaFixa(nome="Iluminação", potencia=100, tempo_liga=0, tempo_desliga=200, prioridade=2), 
             CargaFixa(nome="Residencial", potencia=150, tempo_liga=0, tempo_desliga=700, prioridade=3), 
             CargaFixa(nome="Gado de corte", potencia=100, tempo_liga=0, tempo_desliga=1440, prioridade=4)])
    )



    Criar(microrrede1)
