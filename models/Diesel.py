
class Diesel: 
    def __init__(self, potencia, custo, consumo_50, consumo_75, consumo_100, tanque):
        self.potencia = potencia
        self.custo = custo
        self.consumo_50 = consumo_50
        self.consumo_75 = consumo_75
        self.consumo_100 = consumo_100
        self.tanque = tanque
        self.nivel = tanque
        # self.liga = liga


    def Preco_diesel(self, potencia): 
        valor = 0
        if potencia <= potencia*0.5:
            valor = self.consumo_50*self.custo/60
        if potencia > potencia*0.5 and potencia <= potencia*0.75:
            valor = self.consumo_75*self.custo/60
        if potencia > potencia*0.75 :
            valor = self.consumo_100*self.custo/60
        return valor 

    def Custo_50(self):
        custo_min = self.consumo_50 * self.custo / 60
        return custo_min
    
    def Custo_75(self):
        custo_min = self.consumo_75 * self.custo / 60
        return custo_min
    
    def Custo_100(self):
        custo_min = self.consumo_100 * self.custo / 60
        return custo_min
    
    def Nivel(self):
        return self.Nivel
    
    def Consumo(self, potencia):
        nivel = self.nivel
        if potencia <= potencia*0.5:
            nivel = nivel-self.consumo_50/60
        if potencia > potencia*0.5 and potencia <= potencia*0.75:
            nivel = nivel-self.consumo_75
        if potencia > potencia*0.75 :
            nivel = nivel-self.consumo_100
        self.nivel = nivel
        