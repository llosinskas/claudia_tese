from models.Microrrede import Microrrede, Carga, Concessionaria, Diesel, Bateria, Biogas, Solar, CargaFixa
from models.CRUD import Ler
import pandas as pd

def calcular_demanda_geracao(microrrede_id):
    tempo_dia = 1440    
    demanda=[]
    geracao=[]
    balanco=[]
    custo_diario = 0
    valor = []

    concessionaria = Ler(Concessionaria).filter(Concessionaria.microrrede_id == microrrede_id).all()
    diesel = Ler(Diesel).filter(Diesel.microrrede_id == microrrede_id).all()
    bateria = Ler(Bateria).filter(Bateria.microrrede_id == microrrede_id).all()
    biogas = Ler(Biogas).filter(Biogas.microrrede_id == microrrede_id).all()
    solar = Ler(Solar).filter(Solar.microrrede_id == microrrede_id).all()      

    valor_concessionaria = concessionaria[0].custo_kwh if concessionaria else 0
    valor_diesel = diesel[0].custo_por_kWh if diesel else 0
    valor_biogas = biogas[0].custo_por_kWh if biogas else 0
    valor_solar = solar[0].custo_kwh if solar else 0
    valor_bateria = bateria[0].custo_kwh if bateria else 0
    valores = {
        "fonte": ["concessionaria", "diesel", "biogas", "solar", "bateria"],
        "custo": [valor_concessionaria, valor_diesel, valor_biogas, valor_solar, valor_bateria],
    }
    dataframe_valores = pd.DataFrame(valores)
    valores_oredenados = dataframe_valores.sort_values(by="custo", ascending=True)
    

    curva_carga = curva_carga(microrrede_id)

    return demanda, geracao, balanco, valor, custo_diario


def teste_producao():
    pass 

#def Uso_fonte(microrrede_id, curva_carga):
    

def curva_carga(microrrede_id):
    carga = Ler(Carga).filter(Carga.microrrede_id == microrrede_id).all()
    cargas = Ler(CargaFixa).filter(CargaFixa.carga_id == carga.id).all()
    curva_carga = []
    for t in range(1440):
        potencia = 0
        for carga_fixa in cargas:
            if carga_fixa.tempo_liga <= t < carga_fixa.tempo_desliga:
                potencia += carga_fixa.potencia
        curva_carga.append(potencia)
        
    return curva_carga