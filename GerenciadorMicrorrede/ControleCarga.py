from models.CRUD import Atualizar
from models.Microrrede import CargaFixa
# Essa classe analise como foi o dia anterior de operação da microrrede
# e ajusta as cargas para o dia alterando as cargas com prioridade 2, 4


def tempo_ligado(cargaFixa):
    liga = cargaFixa.tempo_liga
    desliga = cargaFixa.tempo_desliga
    tempo_ativo = desliga - liga 
    return tempo_ativo

def atualizar_tempo_liga(inicio_novo, cargaFixa:CargaFixa):
    tempo_desliga = inicio_novo + tempo_ligado(cargaFixa)
    cargaFixaAtualizada = CargaFixa(
        id = cargaFixa.carga_id,
        tempo_liga = inicio_novo, 
        tempo_desliga = tempo_desliga, 
        potencia = cargaFixa.potencia, 
        prioridade = cargaFixa.prioridade
        )
    Atualizar(CargaFixa, cargaFixa, cargaFixaAtualizada)


        

    