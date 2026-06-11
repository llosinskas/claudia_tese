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
    def _copiar_microrrede(microrrede: Microrrede):
        """Cria uma cópia profunda da microrrede usando Pydantic para evitar corrupção de sessão."""
        from models.schemas import MicrorredeSchema
        # O model_validate vai acessar todas as propriedades lazy do SQLAlchemy
        # e transformar em um objeto puro do Python com a mesma estrutura de dados.
        return MicrorredeSchema.model_validate(microrrede)
    
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
        
        # Força o deslizamento ativado pois esta é a essência da Analise3
        config.deslizamento_habilitado = True
        
        # 1. Avalia o cenário original (sem deslizamento) usando a lógica da Análise 2
        resultado_original = Analise2.executar(microrrede, config)
        custo_kwh_ordenado = resultado_original[0]
        custo_instantaneo_original = resultado_original[12]
        
        # 2. Identifica cargas flexíveis e copia a microrrede
        microrrede_otimizada = Analise3._copiar_microrrede(microrrede)
        
        if config.deslizamento_habilitado and microrrede_otimizada.carga:
            # Seleciona cargas flexíveis (prioridade 2 e 4) a partir da cargaFixa
            cargas_flexiveis = [c for c in microrrede_otimizada.carga.cargaFixa if c.prioridade in [2, 4]]
            
            for carga in cargas_flexiveis:
                duracao = carga.tempo_desliga - carga.tempo_liga
                if duracao <= 0:
                    continue
                
                melhor_inicio = carga.tempo_liga
                
                # Avalia o custo atual antes de mover
                resultado_atual = Analise2.executar(microrrede_otimizada, config)
                menor_custo_total = resultado_atual[11] # Custo Total
                
                # Testa cada possível início (de 30 em 30 minutos)
                for inicio in range(0, 1440 - duracao + 1, 30):
                    carga.tempo_liga = inicio
                    carga.tempo_desliga = inicio + duracao
                    
                    resultado_teste = Analise2.executar(microrrede_otimizada, config)
                    custo_teste = resultado_teste[11]
                    
                    # Se encontrou um horário mais barato, atualiza o melhor
                    if custo_teste < menor_custo_total:
                        menor_custo_total = custo_teste
                        melhor_inicio = inicio
                
                # Aplica definitivamente o melhor horário encontrado para esta carga
                carga.tempo_liga = melhor_inicio
                carga.tempo_desliga = melhor_inicio + duracao
        
        # 3. Roda a análise com a microrrede modificada (deslizada)
        resultado_otimizado = Analise2.executar(microrrede_otimizada, config)
        
        return {
            "original": resultado_original,
            "otimizado": resultado_otimizado,
            "microrrede_otimizada": microrrede_otimizada
        }
