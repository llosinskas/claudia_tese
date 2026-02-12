from models.Microrrede import Microrrede, Balcao, Trade
from models.CRUD import Criar
# Busca a melhor valor de energia para compra e venda 
# Pega as gerações e demanda de energia das microrredes e faz o comercial entre elas 

class Balcao:
    def __init__(self, microrredes,demandas, geracoes, custos_producoes):
        self.microrredes = microrredes
        self.demandas = demandas
        self.geracoes = geracoes
        self.custos_producoes = custos_producoes

    def analisar_ofertas(self):
        n_microrredes = len(self.microrredes)
        for i in range(n_microrredes):
            for tempo in range(1440):  # Supondo análise por minuto
                demanda = self.demandas[i][tempo]
                geracao = self.geracoes[i][tempo]
                custo_producao = self.custos_producoes[i]
                
                if geracao > demanda:
                    excesso = geracao - demanda
                    # Lógica para vender o excesso de energia
                    self.vender_energia(i, excesso, custo_producao, tempo)
                elif demanda > geracao:
                    falta = demanda - geracao
                    # Lógica para comprar energia para suprir a falta
                    self.comprar_energia(i, falta, custo_producao, tempo)


