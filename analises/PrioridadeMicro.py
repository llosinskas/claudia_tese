"""
Arquivo mantido para compatibilidade com códigos antigos.
As análises foram refatoradas e extraídas para módulos individuais.
Recomenda-se importar diretamente de `analises` ou do módulo específico.
"""

from analises.analise1 import Analise1
from analises.analise2 import Analise2
from analises.analise3 import Analise3

# Re-exporta funções do MILP e PSO que eram expostas por aqui
from otmizadores.milp_controle_microrrede import (
    analise_milp as analise_5_milp,
    analise_milp_sem_venda,
    analise_milp_com_deslizamento
)

# Funções que possivelmente não existem mais mas mantidas as assinaturas para evitar crash imediato de import
def analise_5_milp_multi(*args, **kwargs):
    pass

def analise_6_pso(*args, **kwargs):
    from otmizadores.pso import analise_pso
    return analise_pso(*args, **kwargs)

def analise_6_pso_multi(*args, **kwargs):
    pass

class Analise4:
    @staticmethod
    def analise_4(*args, **kwargs):
        pass

__all__ = [
    'Analise1',
    'Analise2',
    'Analise3',
    'Analise4',
    'analise_5_milp',
    'analise_5_milp_multi',
    'analise_6_pso',
    'analise_6_pso_multi',
    'analise_milp_sem_venda',
    'analise_milp_com_deslizamento'
]
