"""
Wrapper para as funções de otimização MILP, injetando o ConfigAnalise.
"""

from models.Microrrede import Microrrede
from otmizadores.milp_controle_microrrede import (
    analise_milp,
    analise_milp_sem_venda,
    analise_milp_com_deslizamento
)
from analises.config import ConfigAnalise
import copy


class AnaliseMILP:
    """Wrapper que adapta os otimizadores MILP para usar ConfigAnalise."""
    
    @staticmethod
    def executar(microrrede: Microrrede, config: ConfigAnalise = None):
        """
        Executa a otimização MILP considerando as restrições do ConfigAnalise.
        
        A lógica é simular as fontes "desligadas" removendo-as de uma cópia
        temporária da microrrede antes de chamar o otimizador MILP subjacente,
        já que o código do MILP atual usa os checks de `is not None`.
        """
        if config is None:
            config = ConfigAnalise()
            
        # Para não quebrar a lógica original do MILP, usamos uma cópia
        # da microrrede e removemos as fontes que estão "desligadas" no config.
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
            
        # Determina qual função MILP usar com base nas flags de comercialização e deslizamento
        if config.deslizamento_habilitado:
            return analise_milp_com_deslizamento(mr_temp)
        elif config.venda_rede_habilitada:
            return analise_milp(mr_temp)
        else:
            return analise_milp_sem_venda(mr_temp)
