"""
PSO (Particle Swarm Optimization) para controle otimizado de microrredes
Objetivo: Minimizar o custo operacional usando metaheurística PSO
"""

import numpy as np
import pandas as pd
import json
from typing import Dict, Tuple, List
from models.Microrrede import Microrrede, Bateria, Diesel, Biogas, Solar, Carga
from Tools.GerarCurvaCarga import CurvaCarga


class PSOMicrorredes:
    """
    Classe para otimização de microrredes usando PSO (Particle Swarm Optimization)
    
    Variáveis de decisão:
    - Potência de cada fonte (Solar, Diesel, Biogas, Bateria, Concessionária) em cada período
    - Carga/Descarga da bateria
    - Venda de excedente para a rede
    """
    
    def __init__(self, microrrede: Microrrede, periodos: int = 1440):
        """
        Inicializa o modelo PSO
        
        Args:
            microrrede: Objeto da microrrede
            periodos: Número de períodos de tempo (minutos no dia = 1440)
        """
        self.microrrede = microrrede
        self.periodos = periodos
        self.solucao = None
        self.custo_otimo = None
        self.historico_convergencia = []
        
        # Dados da microrrede
        self.carga = microrrede.carga
        self.bateria = microrrede.bateria
        self.diesel = microrrede.diesel
        self.biogas = microrrede.biogas
        self.solar = microrrede.solar
        self.concessionaria = microrrede.concessionaria
        
        # Curva de carga
        self.curva_carga = np.array(CurvaCarga(self.carga), dtype=float)
        
        # Curva solar
        self.curva_solar = np.zeros(periodos)
        if self.solar is not None:
            try:
                geracao = json.loads(self.solar.curva_geracao)
                self.curva_solar = np.array([float(g) for g in geracao], dtype=float)
            except:
                self.curva_solar = np.zeros(periodos)
    
    def _codificar_solucao(self, despacho_dict: Dict) -> np.ndarray:
        """
        Codifica a solução em vetor para PSO
        
        Ordem: [P_solar, P_diesel, P_biogas, P_bateria_dis, P_carga_bat]
        """
        vetor = np.zeros(5 * self.periodos)
        idx = 0
        
        for fonte in ['P_solar', 'P_diesel', 'P_biogas', 'P_bateria_dis', 'P_carga_bat']:
            vetor[idx*self.periodos:(idx+1)*self.periodos] = despacho_dict.get(fonte, np.zeros(self.periodos))
            idx += 1
        
        return vetor
    
    def _decodificar_solucao(self, vetor: np.ndarray) -> Dict:
        """
        Decodifica vetor PSO em solução estruturada
        """
        p_solar = vetor[:self.periodos]
        p_diesel = vetor[self.periodos:2*self.periodos]
        p_biogas = vetor[2*self.periodos:3*self.periodos]
        p_bateria_dis = vetor[3*self.periodos:4*self.periodos]
        p_carga_bat = vetor[4*self.periodos:]
        
        return {
            'P_solar': p_solar,
            'P_diesel': p_diesel,
            'P_biogas': p_biogas,
            'P_bateria_dis': p_bateria_dis,
            'P_carga_bat': p_carga_bat
        }
    
    def _aplicar_limites(self, vetor: np.ndarray) -> np.ndarray:
        """
        Aplica limites de potência em cada variável
        """
        vetor = vetor.copy()
        
        # Limites solares
        p_max_solar = self.solar.potencia if self.solar else 0
        vetor[:self.periodos] = np.clip(vetor[:self.periodos], 0, p_max_solar)
        
        # Limites diesel
        p_max_diesel = self.diesel.potencia if self.diesel else 0
        vetor[self.periodos:2*self.periodos] = np.clip(vetor[self.periodos:2*self.periodos], 0, p_max_diesel)
        
        # Limites biogas
        p_max_biogas = self.biogas.potencia if self.biogas else 0
        vetor[2*self.periodos:3*self.periodos] = np.clip(vetor[2*self.periodos:3*self.periodos], 0, p_max_biogas)
        
        # Limites bateria descarga
        p_max_bateria = self.bateria.potencia if self.bateria else 0
        vetor[3*self.periodos:4*self.periodos] = np.clip(vetor[3*self.periodos:4*self.periodos], 0, p_max_bateria)
        
        # Limites bateria carga
        vetor[4*self.periodos:] = np.clip(vetor[4*self.periodos:], 0, p_max_bateria)
        
        return vetor
    
    def _avaliar_solucao(self, vetor: np.ndarray) -> float:
        """
        Avalia o custo de uma solução candidata
        
        Retorna o custo total operacional (menores valores são melhores)
        """
        # Aplicar limites
        vetor = self._aplicar_limites(vetor)
        
        # Decodificar
        sol = self._decodificar_solucao(vetor)
        p_solar = sol['P_solar']
        p_diesel = sol['P_diesel']
        p_biogas = sol['P_biogas']
        p_bateria_dis = sol['P_bateria_dis']
        p_carga_bat = sol['P_carga_bat']
        
        # Limitar solar pela disponibilidade
        p_solar = np.minimum(p_solar, self.curva_solar)
        
        custo_total = 0.0
        penalidade = 0.0
        
        # Dinâmica da bateria
        nivel_bateria = self.bateria.capacidade * (self.bateria.nivel / 100) if self.bateria else 0
        
        for t in range(self.periodos):
            # Balanço de energia
            demanda = self.curva_carga[t]
            geracao_local = p_solar[t] + p_diesel[t] + p_biogas[t] + p_bateria_dis[t]
            
            # Descarga da bateria
            if self.bateria:
                consumo_bateria = p_bateria_dis[t] / (self.bateria.eficiencia / 100) if self.bateria.eficiencia > 0 else 0
                nivel_bateria -= consumo_bateria / 60  # Converter para kWh (período em minutos)
                
                # Carga da bateria
                nivel_bateria += (p_carga_bat[t] * (self.bateria.eficiencia / 100)) / 60
                
                # Penalidade por violação de limite de bateria
                if nivel_bateria < self.bateria.capacidade * (self.bateria.capacidade_min / 100):
                    penalidade += 1000 * (self.bateria.capacidade * (self.bateria.capacidade_min / 100) - nivel_bateria)
                if nivel_bateria > self.bateria.capacidade * (self.bateria.capacidade_max / 100):
                    penalidade += 1000 * (nivel_bateria - self.bateria.capacidade * (self.bateria.capacidade_max / 100))
                
                nivel_bateria = np.clip(nivel_bateria, 
                                        self.bateria.capacidade * (self.bateria.capacidade_min / 100),
                                        self.bateria.capacidade * (self.bateria.capacidade_max / 100))
            
            # Compra/Venda da rede
            balanco = demanda - geracao_local
            
            if balanco > 0:  # Precisa comprar da rede
                custo_compra = balanco * (self.concessionaria.tarifa / 1000) / 60  # R$/kWh para R$/min
                custo_total += custo_compra
            else:  # Pode vender para a rede (geralmente proibido ou com tarifa menor)
                # Assumir que não há receita de venda por simplicidade
                pass
            
            # Custo de geração
            if p_diesel[t] > 0 and self.diesel:
                custo_total += p_diesel[t] * (self.diesel.custo_por_kWh / 1000) / 60
            
            if p_biogas[t] > 0 and self.biogas:
                custo_total += p_biogas[t] * (self.biogas.custo_por_kWh / 1000) / 60
            
            # Custo solar (operacional mínimo)
            if p_solar[t] > 0 and self.solar:
                custo_total += p_solar[t] * (self.solar.custo_kwh / 1000) / 60
            
            # Custo de degradação da bateria
            if self.bateria and (p_carga_bat[t] > 0 or p_bateria_dis[t] > 0):
                custo_total += (p_carga_bat[t] + p_bateria_dis[t]) * (self.bateria.custo_kwh / 1000) / 60
        
        return custo_total + penalidade
    
    def otimizar(self, iteracoes: int = 100, tamanho_enxame: int = 30, w: float = 0.7, c1: float = 1.5, c2: float = 1.5, verbose: bool = True) -> Tuple[np.ndarray, float]:
        """
        Executa otimização PSO
        
        Args:
            iteracoes: Número de iterações do PSO
            tamanho_enxame: Tamanho do enxame de partículas
            w: Peso de inércia
            c1, c2: Coeficientes cognitivo e social
            verbose: Se True, mostra progresso
        
        Returns:
            (melhor_solução, melhor_custo)
        """
        dim = 5 * self.periodos
        
        # Inicializar partículas
        X = np.random.rand(tamanho_enxame, dim) * 10  # Escalado para potências típicas
        V = np.zeros_like(X)
        
        # Avaliar população inicial
        fitness = np.array([self._avaliar_solucao(x) for x in X])
        
        # Melhor histórico pessoal
        pbest = X.copy()
        pbest_fitness = fitness.copy()
        
        # Melhor global
        gbest_idx = np.argmin(pbest_fitness)
        gbest = pbest[gbest_idx].copy()
        gbest_fitness = pbest_fitness[gbest_idx]
        
        # Loop PSO
        for iteracao in range(iteracoes):
            # Atualizar velocidade e posição
            r1 = np.random.rand(tamanho_enxame, dim)
            r2 = np.random.rand(tamanho_enxame, dim)
            
            V = (w * V + 
                 c1 * r1 * (pbest - X) + 
                 c2 * r2 * (gbest - X))
            
            X = X + V
            
            # Aplicar limites
            X = np.array([self._aplicar_limites(x) for x in X])
            
            # Avaliar nova população
            fitness = np.array([self._avaliar_solucao(x) for x in X])
            
            # Atualizar melhor pessoal
            melhorado = fitness < pbest_fitness
            pbest[melhorado] = X[melhorado]
            pbest_fitness[melhorado] = fitness[melhorado]
            
            # Atualizar melhor global
            gbest_idx = np.argmin(pbest_fitness)
            gbest = pbest[gbest_idx].copy()
            gbest_fitness = pbest_fitness[gbest_idx]
            
            self.historico_convergencia.append(gbest_fitness)
            
            if verbose and ((iteracao + 1) % 10 == 0 or iteracao == 0):
                print(f"Iteração {iteracao + 1}/{iteracoes} - Melhor custo: R$ {gbest_fitness:,.2f}")
        
        self.solucao = gbest
        self.custo_otimo = gbest_fitness
        
        return gbest, gbest_fitness
    
    def extrair_solucao(self) -> Dict:
        """
        Extrai a solução em formato estruturado
        """
        if self.solucao is None:
            return None
        
        sol = self._decodificar_solucao(self.solucao)
        
        # Limitar solar pela disponibilidade
        sol['P_solar'] = np.minimum(sol['P_solar'], self.curva_solar)
        
        return {
            'Solar': sol['P_solar'],
            'Diesel': sol['P_diesel'],
            'Biogas': sol['P_biogas'],
            'Bateria_Descarga': sol['P_bateria_dis'],
            'Bateria_Carga': sol['P_carga_bat'],
            'Custo': self.custo_otimo
        }
    
    def gerar_dataframe_resultado(self) -> pd.DataFrame:
        """
        Gera DataFrame com os resultados da otimização
        """
        if self.solucao is None:
            return None
        
        sol = self.extrair_solucao()
        
        # Calcular níveis de tanque e bateria
        nivel_bateria = np.zeros(self.periodos + 1)
        nivel_diesel = np.zeros(self.periodos + 1)
        nivel_biogas = np.zeros(self.periodos + 1)
        
        # Valores iniciais
        if self.bateria:
            nivel_bateria[0] = self.bateria.capacidade * (self.bateria.nivel / 100)
        if self.diesel:
            nivel_diesel[0] = self.diesel.tanque * (self.diesel.nivel / 100)
        if self.biogas:
            nivel_biogas[0] = self.biogas.tanque * (self.biogas.nivel / 100)
        
        # Simular dinâmica
        for t in range(self.periodos):
            # Bateria
            if self.bateria:
                consumo = sol['Bateria_Descarga'][t] / (self.bateria.eficiencia / 100)
                carga = sol['Bateria_Carga'][t] * (self.bateria.eficiencia / 100)
                nivel_bateria[t+1] = nivel_bateria[t] - (consumo - carga) / 60
                nivel_bateria[t+1] = np.clip(nivel_bateria[t+1], 0, self.bateria.capacidade)
            
            # Diesel
            if self.diesel and sol['Diesel'][t] > 0:
                consumo_diesel = sol['Diesel'][t] * 0.25 / 60  # Aproximação de consumo
                nivel_diesel[t+1] = nivel_diesel[t] - consumo_diesel
                nivel_diesel[t+1] = np.clip(nivel_diesel[t+1], 0, self.diesel.tanque)
            else:
                nivel_diesel[t+1] = nivel_diesel[t]
            
            # Biogas
            if self.biogas and sol['Biogas'][t] > 0:
                consumo_biogas = sol['Biogas'][t] * 0.3 / 60  # Aproximação de consumo
                nivel_biogas[t+1] = nivel_biogas[t] - consumo_biogas
                nivel_biogas[t+1] = np.clip(nivel_biogas[t+1], 0, self.biogas.tanque)
            else:
                nivel_biogas[t+1] = nivel_biogas[t]
        
        # Calcular compra/venda da rede
        p_concessionaria = np.zeros(self.periodos)
        p_venda = np.zeros(self.periodos)
        
        for t in range(self.periodos):
            geracao = sol['Solar'][t] + sol['Diesel'][t] + sol['Biogas'][t] + sol['Bateria_Descarga'][t]
            balanco = self.curva_carga[t] - geracao
            
            if balanco > 0:
                p_concessionaria[t] = balanco
            else:
                p_venda[t] = -balanco
        
        # Criar DataFrame
        df = pd.DataFrame({
            'Tempo (min)': np.arange(self.periodos),
            'Carga': self.curva_carga,
            'Solar': sol['Solar'],
            'Diesel': sol['Diesel'],
            'Biogas': sol['Biogas'],
            'Bateria': sol['Bateria_Descarga'],
            'Concessionaria': p_concessionaria,
            'Venda': p_venda,
            'Nivel_Bateria': nivel_bateria[:-1],
            'Nivel_Diesel': nivel_diesel[:-1],
            'Nivel_Biogas': nivel_biogas[:-1]
        })
        
        return df


def analise_pso(microrrede: Microrrede, iteracoes: int = 50, tamanho_enxame: int = 20) -> Tuple[pd.DataFrame, Dict, Dict]:
    """
    Função wrapper para otimização PSO
    
    Args:
        microrrede: Objeto da microrrede
        iteracoes: Número de iterações PSO
        tamanho_enxame: Tamanho do enxame
    
    Returns:
        (DataFrame resultado, Dicionário custos, Dicionário solução)
    """
    otimizador = PSOMicrorredes(microrrede)
    
    # Executar otimização
    solucao_otima, custo_otimo = otimizador.otimizar(
        iteracoes=iteracoes, 
        tamanho_enxame=tamanho_enxame,
        verbose=False
    )
    
    # Extrair resultados
    df_resultado = otimizador.gerar_dataframe_resultado()
    
    # Calcular custos por fonte
    custos = {
        'Solar': df_resultado['Solar'].sum() * (microrrede.solar.custo_kwh if microrrede.solar else 0) / 1000,
        'Diesel': df_resultado['Diesel'].sum() * (microrrede.diesel.custo_por_kWh if microrrede.diesel else 0) / 1000,
        'Biogas': df_resultado['Biogas'].sum() * (microrrede.biogas.custo_por_kWh if microrrede.biogas else 0) / 1000,
        'Bateria': (df_resultado['Bateria'].sum() * (microrrede.bateria.custo_kwh if microrrede.bateria else 0) / 1000),
        'Concessionaria': df_resultado['Concessionaria'].sum() * (microrrede.concessionaria.tarifa / 1000),
        'Total': custo_otimo
    }
    
    solucao_dict = {
        'Nivel_Bateria': df_resultado['Nivel_Bateria'].values,
        'Nivel_Diesel': df_resultado['Nivel_Diesel'].values,
        'Nivel_Biogas': df_resultado['Nivel_Biogas'].values,
        'Convergencia': otimizador.historico_convergencia
    }
    
    return df_resultado, custos, solucao_dict