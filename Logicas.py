from models.Diesel import Diesel   
from models.Concessionaria import Concessionaria
from models.Carga import Carga
from models.Solar import Solar
from models.Bateria import BancoBateria

import pandas as pd

# Uso apenas da energia da rede
def Uso_rede(carga, concessionaria):
    valor = []
    curva_carga = carga
    for carga1 in carga:
        valor.append(concessionaria.Preco_concessionaria(carga1))
    return valor, curva_carga
    
# Uso apenas do gerador diesel
def Uso_diesel(diesel, carga):
    valor = []
    curva_carga = carga
    consumo_diesel = []
    for carga1 in carga:
        consumo_diesel.append(diesel.Consumo(carga1))
        valor.append(diesel.Preco_diesel(carga1))
    return valor, curva_carga, consumo_diesel

# Uso priorizando o uso do gerador solar e bateria e rede
def Otimizacao1(carga, diesel, solar, concessionaria, bateria):
    valor = []
    venda = []
    curva_carga = carga
    consumo_diesel = []
    nivel_bateria = []
    for i, carga1 in enumerate(carga):  
        
        # Geração solar disponível
        geracao_solar = solar.geracao_irradiacao(i)
        
        if geracao_solar > carga1:
            if bateria.nivel < bateria.capacidade_max:
                bateria.Carrega(geracao_solar - carga1)
            else:
                print("Vende para rede")
                venda.append(concessionaria.Vende(geracao_solar - carga1))
        else:
            # Energia necessária após a geração solar 
            energia_necessaria = carga1 - geracao_solar

        # Verifica se a bateria pode suprir a demanda
            if energia_necessaria > 0:
                energia_da_bateria = min(energia_necessaria, bateria.nivel)
                bateria.nivel -= energia_da_bateria
                energia_necessaria -= energia_da_bateria
            else:
                energia_da_bateria = 0
        
            # Se ainda houver necessidade de energia, utiliza o diesel
            if energia_necessaria > 0:
                consumo_diesel.append(diesel.Consumo(energia_necessaria))
                valor.append(diesel.Preco_diesel(energia_necessaria))
            else:
                consumo_diesel.append(0)
                valor.append(0)
            
            nivel_bateria.append(bateria.nivel)
    
    return valor, curva_carga, consumo_diesel, nivel_bateria
    


# Uso priorizando o custo
def Otimizacao2(carga, diesel, solar, concessionaria, bateria):
    valor = []
    curva_carga = carga
    consumo_diesel = []
    nivel_bateria = []
    for i, carga1 in enumerate(carga):
        # Geração solar disponível
        geracao_solar = solar.geracao_irradiacao(i)

        # Energia necessária após a geração solar
        energia_necessaria = carga1 - geracao_solar

        # Verifica se a bateria pode suprir a demanda
        if energia_necessaria > 0:
            energia_da_bateria = min(energia_necessaria, bateria.nivel)
            bateria.nivel -= energia_da_bateria
            energia_necessaria -= energia_da_bateria
        else:
            energia_da_bateria = 0

        # Se ainda houver necessidade de energia, utiliza o diesel
        if energia_necessaria > 0:
            consumo_diesel.append(diesel.Consumo(energia_necessaria))
            valor.append(diesel.Preco_diesel(energia_necessaria))
        else:
            consumo_diesel.append(0)
            valor.append(0)

        nivel_bateria.append(bateria.nivel)

    return valor, curva_carga, consumo_diesel, nivel_bateria