"""
Wrapper para as funções de otimização PSO, injetando o ConfigAnalise.
"""

from models.Microrrede import Microrrede
from otmizadores.pso import analise_pso
from analises.config import ConfigAnalise
import copy


class AnalisePSO:
    """Wrapper que adapta o otimizador PSO para usar ConfigAnalise."""
    
    @staticmethod
    def executar(microrrede: Microrrede, config: ConfigAnalise = None):
        """
        Executa a otimização PSO considerando as restrições do ConfigAnalise.
        
        A lógica é simular as fontes "desligadas" removendo-as de uma cópia
        temporária da microrrede antes de chamar o otimizador PSO subjacente.
        """
        if config is None:
            config = ConfigAnalise()
            
        mr_temp = copy.copy(microrrede)
        
        if not config.fonte_disponivel('Solar', mr_temp):
            mr_temp.solar = None
        if not config.fonte_disponivel('Bateria', mr_temp):
            mr_temp.bateria = None
        if not config.fonte_disponivel('Diesel', mr_temp):
            mr_temp.diesel = None
        if not config.fonte_disponivel('Biogas', mr_temp):
            mr_temp.biogas = None
        if not config.fonte_disponivel('Concessionaria', mr_temp):
            mr_temp.concessionaria = None
            
        return analise_pso(mr_temp)
