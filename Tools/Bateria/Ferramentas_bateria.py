import numpy as np
from models.Microrrede import Bateria
# Ciclo de vida do banco de bateria 
def Cap_Day(n_ciclos, vida_bateria, capacidade_bateria):
    capacidade_bateria = []
    for n in range(n_ciclos+1):
        theeta =[]
        for day in range(int(vida_bateria[n])):
            theeta.append(((float(day)/vida_bateria[n])*90)*np.pi/180)
            capacidade = (20*np.exp(0.000258*(day))*np.cos(theeta[day]))+80
            capacidade =(capacidade*vida_bateria[n])/100
            if len(capacidade_bateria)<=(20*365)-1:
                capacidade_bateria.append(capacidade)
            else:
                break
    return capacidade_bateria

def Tempo_Carga(bateria:Bateria):
    tempo_carga = (bateria.capacidade/bateria.potencia)*bateria.eficiencia*60/100
    return tempo_carga

def Carregar_bateria(nivel_atual,bateria:Bateria, potencia_injetada):
    nivel = nivel_atual
    alerta = ""
    energia_rejeitada = 0
    nivel += potencia_injetada*bateria.eficiencia/60
    if nivel >= bateria.capacidade_max:
        nivel = bateria.capacidade_max
        alerta = "Bateria cheia"
        energia_rejeitada = (nivel_atual + potencia_injetada*bateria.eficiencia/60) - bateria.capacidade_max
    return nivel, alerta, energia_rejeitada

def Descarrega_bateria(nivel_atual, potencia_consumida,bateria:Bateria,):
    nivel = nivel_atual
    nivel -= (potencia_consumida*bateria.eficiencia)/60
    return nivel 
