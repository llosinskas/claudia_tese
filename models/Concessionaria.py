class Concessionaria:
    def __init__(self, tarifa, demanda, grupo):
        self.tarifa = tarifa
        self.demanda = demanda
        self.grupo = grupo

    def Preco_concessionaria(self, potencia):
        valor = potencia*self.tarifa/60
        return valor
    def Vende(self, potencia):
        valor = potencia*self.tarifa/60
        return valor