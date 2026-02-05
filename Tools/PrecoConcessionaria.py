from models.Microrrede import Concessionaria
# Função para somar o valor da geração concessionaria

def array_valores_acumulado(cargas, concessionaria:Concessionaria):
    valores = []
    acumulado = 0
    for carga in cargas:
        valor_atual = concessionaria.Preco_concessionaria(carga)
        acumulado +=  valor_atual
        valores.append(valor_atual)

    return valores, acumulado