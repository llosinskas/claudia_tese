"""
Análise 3 — Heurística com deslizamento de carga.

Similar à Análise 2, porém tenta mover as cargas com prioridade 2 e 4
para os horários onde a energia é mais barata.
"""

import numpy as np
import pandas as pd
import json
import copy

from models.Microrrede import Microrrede, CargaFixa
from Tools.GerarCurvaCarga import CurvaCarga
from analises.analise2 import Analise2
from analises.config import ConfigAnalise


class Analise3:
    """
    Análise 3: Otimização por ordem de custo COM deslizamento de carga.
    
    Características:
    - Desliza cargas flexíveis (prioridade 2 e 4) para horários de menor custo.
    - Otimiza as MGs usando o mesmo princípio em cascata da Análise 2.
    """
    
    @staticmethod
    def _copiar_microrrede(microrrede: Microrrede) -> Microrrede:
        """Cria uma cópia profunda da microrrede para não alterar os dados originais."""
        mr_copy = copy.copy(microrrede)
        if mr_copy.carga:
            carga_copy = copy.copy(mr_copy.carga)
            # Acessa e copia explicitamente cargaFixa a partir do objeto original atrelado à sessão
            carga_copy.cargaFixa = [copy.copy(cf) for cf in microrrede.carga.cargaFixa]
            mr_copy.carga = carga_copy
        return mr_copy
    
    @staticmethod
    def analise_3(microrrede: Microrrede, config: ConfigAnalise = None):
        """
        Executa a Análise 3 (Deslizamento de Cargas).
        
        Args:
            microrrede: Objeto Microrrede
            config: ConfigAnalise com flags liga/desliga
            
        Returns:
            Dict com os resultados 'original' e 'otimizado' (mesmo formato da Análise 2)
        """
        if config is None:
            config = ConfigAnalise()
            # Força o deslizamento ativado se a Analise3 for chamada diretamente sem config
            config.deslizamento_habilitado = True
        
        # O deslizamento real só ocorre se a flag estiver habilitada
        # (se chamada via Analise3 e flag=False, equivale à Analise2)
        
        # 1. Avalia o cenário original (sem deslizamento) usando a lógica da Análise 2
        resultado_original = Analise2.executar(microrrede, config)
        custo_kwh_ordenado = resultado_original[0]
        custo_instantaneo_original = resultado_original[12]
        
        # 2. Identifica cargas flexíveis e copia a microrrede
        microrrede_otimizada = Analise3._copiar_microrrede(microrrede)
        
        if config.deslizamento_habilitado and microrrede_otimizada.carga:
            # Seleciona cargas flexíveis (prioridade 2 e 4) a partir da cargaFixa
            cargas_flexiveis = [c for c in microrrede_otimizada.carga.cargaFixa if c.prioridade in [2, 4]]
            
            # Ordena horários do mais barato pro mais caro baseado no cenário original
            # (Essa é a 'heurística' de deslizamento: move para as janelas mais baratas)
            df_custos = pd.DataFrame({
                'Tempo': range(1440),
                'Custo': custo_instantaneo_original
            }).sort_values(by='Custo')
            
            for carga in cargas_flexiveis:
                duracao = carga.tempo_desliga - carga.tempo_liga
                if duracao <= 0:
                    continue
                
                melhor_inicio = None
                menor_custo_janela = float('inf')
                
                # Procura a melhor janela contínua (saltando de 15 em 15 min por performance)
                for inicio in range(0, 1440 - duracao + 1, 15):
                    fim = inicio + duracao
                    custo_janela = custo_instantaneo_original[inicio:fim].sum()
                    
                    if custo_janela < menor_custo_janela:
                        menor_custo_janela = custo_janela
                        melhor_inicio = inicio
                
                # Se encontrou um horário melhor, atualiza a carga na cópia
                if melhor_inicio is not None:
                    carga.tempo_liga = melhor_inicio
                    carga.tempo_desliga = melhor_inicio + duracao
        
        # 3. Roda a análise com a microrrede modificada (deslizada)
        resultado_otimizado = Analise2.executar(microrrede_otimizada, config)
        
        return {
            "original": resultado_original,
            "otimizado": resultado_otimizado,
            "microrrede_otimizada": microrrede_otimizada
        }
