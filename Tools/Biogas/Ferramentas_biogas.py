from models.Microrrede import Biogas


def Preco_tanque_biogas(nivel,carga_instantanea,  biogas:Biogas): 
    valor = 0
    potencia = biogas.potencia
    consumo_50 = biogas.consumo_50
    consumo_75 = biogas.consumo_75
    consumo_100 = biogas.consumo_100
    custo = biogas.custo_por_kWh
    alerta =""
    
    if nivel > 0:
        if carga_instantanea <= potencia*0.5:
            valor = consumo_50* custo/60
            nivel = nivel - consumo_50/60
        if carga_instantanea > potencia*0.5 and carga_instantanea <= potencia*0.75:
            valor = consumo_75*custo/60
            nivel =nivel- consumo_75/60
        if carga_instantanea > potencia*0.75 :
            valor = consumo_100*custo/60
            nivel =nivel- consumo_100
    else:
        alerta = "Acabou o diesel"
    return alerta, nivel,valor 

def Consumo_biogas(nivel, carga_instantanea, biogas:Biogas):
    consumo = 0
    potencia = biogas.potencia
    consumo_50 = biogas.consumo_50
    consumo_75 = biogas.consumo_75
    consumo_100 = biogas.consumo_100
    
    alerta =""
    
    if nivel > 0:
        if carga_instantanea <= potencia*0.5:
            consumo = consumo_50/60
            nivel = nivel - consumo_50/60
        if carga_instantanea > potencia*0.5 and carga_instantanea <= potencia*0.75:
            consumo = consumo_75/60
            nivel =nivel- consumo_75/60
        if carga_instantanea > potencia*0.75 :
            consumo = consumo_100/60
            nivel =nivel- consumo_100/60
    else:
        alerta = "Acabou o biogas"
    return alerta, nivel,consumo

def Geracao_biogas_instantanea(biogas:Biogas):
    geracao_instantanea = biogas.geracao/1440
    return geracao_instantanea

def Geracao_biogas(nivel, biogas:Biogas):
    geracao = 0
    if nivel < biogas.tanque:
        geracao = biogas.geracao/60
        nivel = nivel + biogas.geracao/60
    return nivel, geracao