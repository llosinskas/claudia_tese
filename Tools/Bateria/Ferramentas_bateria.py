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

def gerenciar_bateria(nivel_atual: float, bateria: Bateria, carga_solicitada_kw: float = 0.0, geracao_excedente_kw: float = 0.0):
    """
    Gerencia a carga e descarga da bateria respeitando limites físicos de potência e capacidade.
    
    Args:
        nivel_atual: Nível de energia atual na bateria (em kWh).
        bateria: Objeto/modelo Bateria contendo potência, capacidade_min, capacidade_max, etc.
        carga_solicitada_kw: Quantidade de energia solicitada (para descarga) em kW.
        geracao_excedente_kw: Quantidade de energia excedente (para carga) em kW.
        
    Returns:
        novo_nivel (kWh), energia_fornecida_kw (kW), energia_armazenada_kw (kW), energia_rejeitada_kw (kW), alerta (str)
    """
    novo_nivel = nivel_atual
    energia_fornecida_kw = 0.0
    energia_armazenada_kw = 0.0
    energia_rejeitada_kw = 0.0
    alerta = ""
    
    # Limites físicos em kWh (assumindo que capacidade_min e capacidade_max são porcentagens, ex: 20 e 90)
    limite_min_kwh = bateria.capacidade * bateria.capacidade_min / 100.0
    limite_max_kwh = bateria.capacidade * bateria.capacidade_max / 100.0
    
    # 1. Tentar descarregar (atender a carga solicitada)
    if carga_solicitada_kw > 0:
        if novo_nivel > limite_min_kwh:
            # Não podemos descarregar mais do que a potência máxima
            descarga_kw = min(carga_solicitada_kw, bateria.potencia)
            
            # Energia consumida da bateria em kWh (1 minuto) considerando a eficiência
            # Nota: na lógica original a eficiência era multiplicada (perde mais carga para gerar X).
            descarga_kwh = (descarga_kw * bateria.eficiencia) / 60.0
            
            if novo_nivel - descarga_kwh < limite_min_kwh:
                # Bateria atingirá o limite mínimo durante este minuto
                descarga_kwh = novo_nivel - limite_min_kwh
                # Se descarregar apenas descarga_kwh, quanto entrega em kW?
                descarga_kw = (descarga_kwh * 60.0) / bateria.eficiencia
                alerta = "Bateria atingiu o limite mínimo."
            
            energia_fornecida_kw = descarga_kw
            novo_nivel -= descarga_kwh
        else:
            alerta = "Bateria não consegue suprir a carga (nível muito baixo)."
            
    # 2. Tentar carregar (absorver geração excedente)
    elif geracao_excedente_kw > 0:
        if novo_nivel < limite_max_kwh:
            # Não podemos carregar mais rápido do que a potência máxima
            carga_kw = min(geracao_excedente_kw, bateria.potencia)
            
            # Energia injetada na bateria em kWh (1 minuto) considerando eficiência
            carga_kwh = (carga_kw * bateria.eficiencia) / 60.0
            
            if novo_nivel + carga_kwh > limite_max_kwh:
                # Bateria atingirá o limite máximo durante este minuto
                carga_kwh = limite_max_kwh - novo_nivel
                # O que coube na bateria convertido para kW
                carga_kw = (carga_kwh * 60.0) / bateria.eficiencia
                alerta = "Bateria cheia."
                
            energia_armazenada_kw = carga_kw
            energia_rejeitada_kw = geracao_excedente_kw - energia_armazenada_kw
            novo_nivel += carga_kwh
        else:
            alerta = "Bateria cheia."
            energia_rejeitada_kw = geracao_excedente_kw

    return novo_nivel, energia_fornecida_kw, energia_armazenada_kw, energia_rejeitada_kw, alerta
