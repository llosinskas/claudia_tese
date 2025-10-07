class BancoBateria:
    def __init__(self, potencia, capacidade, eficiencia, capacidade_min, capacidade_max):
        self.potencia = potencia
        self.capacidade = capacidade
        self.nivel = capacidade
        self.eficiencia = eficiencia
        self.capacidade_min = capacidade_min
        self.capacidade_max = capacidade_max
    
    def Descarrega(self, potencia_consumida):
        nivel = self.nivel
        nivel =nivel - (potencia_consumida*self.eficiencia)/60

    def Nivel(self):
        return self.nivel        
    
    def Carregar(self, potencia):
        nivel = self.nivel
        nivel = nivel + (potencia*self.eficiencia)/60