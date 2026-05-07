"""
ConfigAnalise — Variáveis de controle liga/desliga de cada fonte de energia.

Centraliza as flags de controle que antes estavam espalhadas como
`if microrrede.bateria != None` em todas as análises.

Uso:
    config = ConfigAnalise(diesel_ligado=False)
    Analise2.executar(microrrede, config)
"""

from dataclasses import dataclass, field


@dataclass
class ConfigAnalise:
    """
    Variáveis de controle liga/desliga de cada fonte de energia.
    
    Todas as análises (1, 2, 3, MILP, PSO) e o Balcão de Energia
    recebem este objeto para decidir quais fontes usar.
    """
    
    # ===== FLAGS DE FONTES (liga/desliga) =====
    solar_ligado: bool = True
    bateria_ligada: bool = True
    diesel_ligado: bool = True
    biogas_ligado: bool = True
    concessionaria_ligada: bool = True
    
    # ===== FLAGS DE COMERCIALIZAÇÃO =====
    venda_rede_habilitada: bool = True       # Vender excesso para concessionária
    compra_balcao_habilitada: bool = True     # Comprar de outras MGs no balcão
    venda_balcao_habilitada: bool = True      # Vender para outras MGs no balcão
    
    # ===== FLAGS DE OTIMIZAÇÃO =====
    deslizamento_habilitado: bool = False     # Deslizar cargas prioridade 2 e 4
    
    # ===== PARÂMETROS DO BALCÃO =====
    margem_venda: float = 0.05               # 5% margem sobre custo médio
    coef_perda_km: float = 0.004             # 0.4%/km de perda por distância
    
    def fonte_disponivel(self, fonte: str, microrrede) -> bool:
        """
        Verifica se a fonte está ligada E existe na microrrede.
        
        Args:
            fonte: Nome da fonte ('Solar', 'Bateria', 'Diesel', 'Biogas', 'Concessionaria')
            microrrede: Objeto Microrrede
            
        Returns:
            True se a fonte está habilitada e existe
        """
        match fonte:
            case 'Solar':
                return self.solar_ligado and microrrede.solar is not None
            case 'Bateria':
                return self.bateria_ligada and microrrede.bateria is not None
            case 'Diesel':
                return self.diesel_ligado and microrrede.diesel is not None
            case 'Biogas':
                return self.biogas_ligado and microrrede.biogas is not None
            case 'Concessionaria':
                return self.concessionaria_ligada and microrrede.concessionaria is not None
        return False
    
    def fontes_disponiveis(self, microrrede) -> list:
        """Retorna lista de nomes de fontes disponíveis para a microrrede."""
        todas = ['Solar', 'Bateria', 'Diesel', 'Biogas', 'Concessionaria']
        return [f for f in todas if self.fonte_disponivel(f, microrrede)]
    
    def custo_kwh_fonte(self, fonte: str, microrrede) -> float:
        """Retorna o custo por kWh de uma fonte na microrrede."""
        if not self.fonte_disponivel(fonte, microrrede):
            return float('inf')
        
        match fonte:
            case 'Solar':
                return microrrede.solar.custo_kwh
            case 'Bateria':
                return microrrede.bateria.custo_kwh
            case 'Diesel':
                return microrrede.diesel.custo_por_kWh
            case 'Biogas':
                return microrrede.biogas.custo_por_kWh
            case 'Concessionaria':
                return microrrede.concessionaria.tarifa
        return float('inf')
    
    def fontes_ordenadas_por_custo(self, microrrede) -> list:
        """
        Retorna fontes disponíveis ordenadas por custo crescente.
        
        Returns:
            Lista de tuplas (nome_fonte, custo_kwh)
        """
        fontes = []
        for nome in self.fontes_disponiveis(microrrede):
            custo = self.custo_kwh_fonte(nome, microrrede)
            if custo < float('inf'):
                fontes.append((nome, custo))
        
        fontes.sort(key=lambda x: x[1])
        return fontes
