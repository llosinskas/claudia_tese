from models.Microrrede import Microrrede, Carga, Concessionaria, Diesel, Bateria, Biogas, Solar, CargaFixa
from models.CRUD import Ler
import pandas as pd
import numpy as np 
from Tools.GerarCurvaCarga import Curva_carga

class Gerenciador:
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
    

    def curva_carga(microrrede):
        cargas = microrrede.carga.cargaFixa
        curva_carga = []
        curva_carga = np.zeros(1440)
        for carga in cargas:   
            
            curva_carga += np.array(Curva_carga(carga.potencia, carga.tempo_liga, carga.tempo_desliga))
            
        return curva_carga
    


    def uso_concessionaria(microrrede:Microrrede):
        print(f"Chegou aqui{microrrede.concessionaria}")
        demanda= []
        valor = []
        totalCarga=0 
        totalValor=0
        concessionaria = microrrede.concessionaria
        curva_carga = Gerenciador.curva_carga(microrrede)

        for i, carga in enumerate(curva_carga):
            demanda.append(carga)
            totalCarga += carga
            custo = carga*concessionaria.tarifa
            valor.append(custo)
            totalValor+=custo

        return demanda, totalCarga, valor, totalValor
    
    def uso_biogas(microrrede_id):
        carga= []
        valor = []
        totalCarga=0 
        totalValor=0
        nivel=[]
        nivelTotal=0

        return carga, totalCarga, valor, totalValor, nivel, nivelTotal
    
    def uso_diesel(microrrede_id):
        carga= []
        valor = []
        totalCarga=0 
        totalValor=0
        nivel=[]
        nivelTotal=0

        return carga, totalCarga, valor, totalValor, nivel, nivelTotal
    
    def uso_bateria_concessionaria(microrrede_id):
        carga= []
        valor = []
        totalCarga=0 
        totalValor=0


        return carga, totalCarga, valor, totalValor
    
    def uso_solar(microrrede_id):
        carga= []
        valor = []
        totalCarga=0 
        totalValor=0


        return carga, totalCarga, valor, totalValor
    