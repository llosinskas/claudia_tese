from models.Microrrede import Diesel


def Preco_tanque_diesel(nivel,carga_instantanea,  diesel:Diesel): 
    valor = 0
    potencia = diesel.potencia
    consumo_50 = diesel.consumo_50
    consumo_75 = diesel.consumo_75
    consumo_100 = diesel.consumo_100
    custo = diesel.custo_por_kWh
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