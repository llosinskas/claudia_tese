from models.CRUD import Atualizar
from models.Microrrede import Microrrede, CargaFixa, Carga, Bateria, Biogas, Diesel, Solar, Concessionaria
from models.CRUD import Ler, Ler_Objeto
from Tools.GerarCurvaCarga import CurvaCarga

from Tools.Diesel.Ferramentas_diesel import Consumo_diesel, Preco_tanque_diesel
from Tools.Biogas.Ferramentas_biogas import Consumo_biogas, Geracao_biogas_instantanea, Preco_tanque_biogas
from Tools.Bateria.Ferramentas_bateria import Cap_Day, Carregar_bateria, Descarrega_bateria, Tempo_Carga
from numba import njit

# Essa classe analise como foi o dia anterior de operação da microrrede
# e ajusta as cargas para o dia alterando as cargas com prioridade 2, 4
import numpy as np 
import json
import pandas as pd 
from numba import njit

def Tempo_ligado(cargaFixa):
    liga = cargaFixa.tempo_liga
    desliga = cargaFixa.tempo_desliga
    tempo_ativo = desliga - liga 
    return tempo_ativo

def atualizar_tempo_liga(inicio_novo, cargaFixa:CargaFixa):
    tempo_desliga = inicio_novo + Tempo_ligado(cargaFixa)
    cargaFixaAtualizada = CargaFixa(
        id = cargaFixa.carga_id,
        tempo_liga = inicio_novo, 
        tempo_desliga = tempo_desliga, 
        potencia = cargaFixa.potencia, 
        prioridade = cargaFixa.prioridade
        )
    Atualizar(CargaFixa, cargaFixa, cargaFixaAtualizada)



def Otimizar_carga(microrrede:Microrrede, curva_carga):
    bateria = microrrede.bateria
    biogas = microrrede.biogas
    diesel = microrrede.diesel
    concessionaria = microrrede.concessionaria
    solar = microrrede.solar
    
    curva_solar = []    
    if solar != None:
        curva_solar = json.loads(solar.curva_geracao)
    resultado_microrrede = pd.DataFrame(columns=['Carga', 'Bateria', 'Solar', 'Diesel', 'Biogas', 'Concessionaria'])
    
    resultado_microrrede['Carga'] = curva_carga
    tempo_recarga_bateria = 0
    custo_kwh = pd.DataFrame()
    if bateria != None:     
        custo_kwh_bateria = bateria.custo_kwh
        custo_kwh.loc[0, 'Bateria'] = custo_kwh_bateria
        tempo_recarga_bateria = Tempo_Carga(bateria)
        nivel_instantaneo_bateria = bateria.capacidade 
    elif bateria == None:
        custo_kwh.loc[0, 'Bateria'] = None
        
    if biogas != None:
        custo_kwh_biogas = biogas.custo_por_kWh
        custo_kwh.loc[0, 'Biogas'] = custo_kwh_biogas
        geracao_biogas = Geracao_biogas_instantanea(biogas)
        nivel_instantaneo_biogas = biogas.tanque

    elif biogas == None:
        custo_kwh.loc[0, 'Biogas'] = None
        
    if diesel != None:
        custo_kwh_diesel = diesel.custo_por_kWh
        custo_kwh.loc[0, 'Diesel'] = custo_kwh_diesel
        nivel_instantaneo_diesel = diesel.tanque
    elif diesel == None:
        custo_kwh.loc[0, 'Diesel'] = None
    if solar != None:  
        custo_kwh_solar = solar.custo_kwh
        custo_kwh.loc[0, 'Solar'] = custo_kwh_solar
    elif solar == None:
        custo_kwh.loc[0, 'Solar'] = None
    custo_kwh_ordenado = custo_kwh.sort_values(by=0, axis=1)
            
    nivel_bateria = np.zeros(len(curva_carga))
    nivel_biogas = np.zeros(len(curva_carga))
    nivel_diesel = np.zeros(len(curva_carga))
    
    uso_solar = np.zeros(len(curva_carga))
    uso_diesel=np.zeros(len(curva_carga))
    uso_biogas=np.zeros(len(curva_carga))   
    uso_bateria = np.zeros(len(curva_carga))
    uso_concessionaria = np.zeros(len(curva_carga))
    total_carga = 0
    sobra = []
   
    custo_solar = np.zeros(len(curva_carga))
    custo_diesel = np.zeros(len(curva_carga))
    custo_biogas = np.zeros(len(curva_carga))
    custo_bateria = np.zeros(len(curva_carga))
    custo_concessionaria = np.zeros(len(curva_carga))
    custo_total_instantaneo = np.zeros(len(curva_carga))
     

    for i, carga_instantanea in enumerate(curva_carga):
        carga_necessaria = carga_instantanea
        total_carga += carga_instantanea
        if biogas != None:
            if nivel_instantaneo_biogas < biogas.tanque:
                nivel_instantaneo_biogas += geracao_biogas
            nivel_biogas[i] = nivel_instantaneo_biogas
        if diesel != None:
            nivel_diesel[i] = nivel_instantaneo_diesel

        for fonte in custo_kwh_ordenado.columns:
            if carga_necessaria <= 0:
                break
            
            match fonte:
                case 'Solar':

                    if solar != None:
                        if curva_solar[i] >= carga_necessaria:
                            uso_solar[i] = carga_necessaria
                            custo_solar[i] = uso_solar[i]*solar.custo_kwh/60
                            carga_necessaria = 0
                            if bateria != None:
                                nivel_instantaneo_bateria, alerta, energia_rejeitada = Carregar_bateria(nivel_instantaneo_bateria, bateria, (curva_solar[i]-carga_necessaria)/60)
                                nivel_bateria[i] = nivel_instantaneo_bateria/60

                        elif curva_solar[i] < carga_necessaria:
                            custo_solar[i] = curva_solar[i]*solar.custo_kwh/60
                            uso_solar[i] = curva_solar[i]
                            carga_necessaria -= uso_solar[i]

                case 'Bateria':
                    if bateria != None:
                        if bateria.potencia >= carga_necessaria:
                            if nivel_instantaneo_bateria > bateria.capacidade_min:
                                
                                # uso_bateria[i] = carga_necessaria/(bateria.eficiencia/100)/60
                                uso_bateria[i] = carga_necessaria
                                custo_bateria[i] = uso_bateria[i]*bateria.custo_kwh/60
                                nivel_instantaneo_bateria = Descarrega_bateria(nivel_instantaneo_bateria, carga_necessaria/60, bateria)
                                nivel_bateria[i] = nivel_instantaneo_bateria
                                carga_necessaria = 0


                        elif bateria.potencia < carga_necessaria:
                            if nivel_instantaneo_bateria > bateria.capacidade_min:
                                uso_bateria[i] = bateria.potencia
                                custo_bateria[i] = uso_bateria[i]*bateria.custo_kwh/60
                                nivel_instantaneo_bateria = Descarrega_bateria(nivel_instantaneo_bateria, bateria.potencia/60, bateria)
                                nivel_bateria[i] = nivel_instantaneo_bateria                               
                                carga_necessaria -= bateria.potencia

                case 'Biogas':
                    if biogas != None:
                        if biogas.potencia >= carga_necessaria:
                            if nivel_instantaneo_biogas > 0:
                                uso_biogas[i] = carga_necessaria
                                custo_biogas[i] = uso_biogas[i]*biogas.custo_por_kWh/60
                                alerta, nivel_instantaneo_biogas,consumo=Consumo_biogas(nivel_instantaneo_biogas, carga_necessaria, biogas)

                                carga_necessaria = 0

                        elif biogas.potencia < carga_necessaria:
                            if nivel_instantaneo_biogas > 0:
                                uso_biogas[i] = biogas.potencia
                                custo_biogas[i] = uso_biogas[i]*biogas.custo_por_kWh/60
                                nivel_instantaneo_biogas -= uso_biogas[i]/60
                            carga_necessaria -= biogas.potencia
                case 'Diesel':
                    if fonte == 'Diesel' and diesel != None:
                        if diesel.potencia >= carga_necessaria:
                            if nivel_instantaneo_diesel > 0:
                                uso_diesel[i] = carga_necessaria    
                                custo_diesel[i] = uso_diesel[i]*diesel.custo_por_kWh/60
                                alerta, nivel_instantaneo_diesel, consumo = Consumo_diesel(nivel_instantaneo_diesel, carga_necessaria, diesel)
                                carga_necessaria = 0
                        
                        elif diesel.potencia < carga_necessaria:
                            if nivel_instantaneo_diesel > 0:
                                uso_diesel[i] = diesel.potencia
                                custo_diesel[i] = uso_diesel[i]*diesel.custo_por_kWh/60
                                alerta, nivel_instantaneo_diesel, consumo = Consumo_diesel(nivel_instantaneo_diesel, uso_diesel[i], diesel)
                                carga_necessaria -= diesel.potencia
            
            # Sobra de energia (venda para a rede)
            sobra_instantanea = 0
            if diesel != None:
                sobra_instantanea = diesel.potencia
            elif biogas != None:
                sobra_instantanea += biogas.potencia
            elif bateria != None:
                sobra_instantanea += bateria.potencia
            elif solar != None:
                sobra_instantanea += curva_solar[i]

            if sobra_instantanea > carga_instantanea:
                sobra.append(sobra_instantanea - carga_instantanea)
            
            custo_total_instantaneo[i] = custo_solar[i] + custo_bateria[i] + custo_biogas[i] + custo_diesel[i]+ custo_concessionaria[i]
            
            # Falta de energia (Compra da rede)            
            falta = curva_carga[i] - (uso_bateria[i]+uso_biogas[i]+uso_diesel[i]+uso_solar[i])   
            if curva_carga[i] >= falta:
                uso_concessionaria[i] = falta
                custo_concessionaria[i] = uso_concessionaria[i]*concessionaria.tarifa/60
                
    return custo_total_instantaneo

def deslize_carga(cargas:Carga, curva_custo):
    curva_atualizada = np.zeros(len(curva_custo))
    for carga in cargas.cargaFixa:
        if carga.prioridade == 2 or carga.prioridade == 4:
            tempo_ligado= Tempo_ligado(carga)
            custo_min_total = float('inf')
            melhor_tempo_liga = -1

            for inicio in range(0, 1440 - tempo_ligado):
                custo_total = 0
                for i in range(inicio, inicio + tempo_ligado):
                    custo_total += curva_custo[i] * carga.potencia/60
                if custo_total < custo_min_total:
                    custo_min_total = custo_total
                    melhor_tempo_liga = inicio

            if melhor_tempo_liga != -1:
                novo_tempo_liga = melhor_tempo_liga
                novo_tempo_desliga = novo_tempo_liga + tempo_ligado
                #atualizar_tempo_liga(novo_tempo_liga, carga)
                for i in range(novo_tempo_liga, novo_tempo_desliga):
                    curva_atualizada[i] += carga.potencia
        else:
            for i in range(carga.tempo_liga, carga.tempo_desliga):
                curva_atualizada[i] += carga.potencia    

    return curva_atualizada


def Otimizado(microrrede:Microrrede):
        carga = microrrede.carga
        curva_carga = CurvaCarga(carga)
        curva_custo = Otimizar_carga(microrrede, curva_carga)
        curva_carga_otimizada = deslize_carga(carga, curva_custo)
        curva_custo_otimizado = Otimizar_carga(microrrede, curva_carga_otimizada)
        return curva_custo, curva_custo_otimizado, curva_carga, curva_carga_otimizada