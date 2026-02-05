# Essa classe analise como foi o dia anterior de operação da microrrede
# e ajusta as cargas para o dia alterando as cargas com prioridade 3, 4

class ControleCarga:
    def __init__(self, cargas, perfil_anterior):
        self.cargas = cargas
        self.perfil_anterior = perfil_anterior

    def tempo_ligado(self, carga):
        liga = carga.tempo_liga
        desliga = carga.tempo_desliga
        tempo_ativo = desliga - liga 
        return tempo_ativo
    
    def ajustar_tempo_liga(self, carga, demanda_sobrando):
        pass
        
    