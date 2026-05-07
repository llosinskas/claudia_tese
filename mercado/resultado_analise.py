"""
Interface padronizada para os resultados de qualquer método de análise.
"""

from dataclasses import dataclass
import numpy as np
import pandas as pd
from typing import Dict, Any

from models.Microrrede import Microrrede


@dataclass
class ResultadoAnalise:
    """
    Resultado padronizado de qualquer método de análise para uma microrrede.
    Normaliza as saídas das análises 2, 3, MILP e PSO para que o Balcão de Energia
    possa processá-las de maneira agnóstica.
    """
    microrrede: Microrrede
    metodo: str                       # "heuristico", "milp", "pso"
    periodos: int                     # geralmente 1440
    
    # Uso de energia por fonte (kW em cada período)
    uso_solar: np.ndarray
    uso_bateria: np.ndarray
    uso_diesel: np.ndarray
    uso_biogas: np.ndarray
    uso_concessionaria: np.ndarray
    
    # Custos por fonte (R$ em cada período)
    custo_solar: np.ndarray
    custo_bateria: np.ndarray
    custo_diesel: np.ndarray
    custo_biogas: np.ndarray
    custo_concessionaria: np.ndarray
    
    # Balanço energético
    curva_carga: np.ndarray           # Demanda total (kW)
    excesso: np.ndarray               # Excesso disponível para venda no balcão (kW)
    deficit: np.ndarray               # Déficit que precisa ser comprado no balcão (kW)
    
    # Estado de armazenamento
    nivel_bateria: np.ndarray
    
    @staticmethod
    def from_analise2_ou_3(microrrede: Microrrede, resultado: tuple, metodo: str = "heuristico") -> 'ResultadoAnalise':
        """
        Converte a saída da Analise2.executar() ou Analise3.analise_3()['otimizado'] 
        para o formato padronizado.
        
        Args:
            microrrede: O objeto da microrrede
            resultado: A tupla de 13 elementos retornada pelas análises heurísticas
            metodo: Nome do método ("heuristico" ou "heuristico_deslize")
        """
        # A tupla retorna:
        # 0: custo_kwh_ordenado, 1: total_uso_diesel, 2: total_uso_bateria, 
        # 3: total_uso_concessionaria, 4: total_uso_biogas, 5: total_uso_solar,
        # 6: total_sobra, 7: total_carga, 8: total (df), 9: uso_energia (df), 
        # 10: niveis_tanques (df), 11: custo_total, 12: custo_total_instantaneo
        
        # Como o uso_energia tem as séries de tempo...
        uso_energia = resultado[9]
        niveis_tanques = resultado[10]
        
        periodos = len(uso_energia)
        
        # A heurística atual já calcula a compra da concessionária. 
        # Para o balcão, o déficit é o que foi suprido pela concessionária.
        # O excesso é o que sobrou (não utilizado das fontes).
        
        uso_solar = uso_energia.get('Solar', np.zeros(periodos)).values
        uso_bateria = uso_energia.get('Bateria', np.zeros(periodos)).values
        uso_diesel = uso_energia.get('Diesel', np.zeros(periodos)).values
        uso_biogas = uso_energia.get('Biogas', np.zeros(periodos)).values
        uso_concessionaria = uso_energia.get('Concessionaria', np.zeros(periodos)).values
        
        # Custos
        custo_solar = uso_solar * (microrrede.solar.custo_kwh if microrrede.solar else 0) / 60
        custo_bateria = uso_bateria * (microrrede.bateria.custo_kwh if microrrede.bateria else 0) / 60
        custo_diesel = uso_diesel * (microrrede.diesel.custo_por_kWh if microrrede.diesel else 0) / 60
        custo_biogas = uso_biogas * (microrrede.biogas.custo_por_kWh if microrrede.biogas else 0) / 60
        custo_concessionaria = uso_concessionaria * (microrrede.concessionaria.tarifa if microrrede.concessionaria else 0) / 60
        
        # Excesso: Se a potência de uma fonte não foi totalmente usada e ela é "grátis" ou obrigatória (solar)
        # Vamos assumir que o excesso principal vem da sobra não contabilizada no DataFrame.
        # Como não temos uma série temporal 'sobra' perfeitamente definida, vamos recalcular.
        curva_carga = np.abs(uso_energia.get('Carga', np.zeros(periodos)).values)
        
        # Para simplificar na versão inicial, vamos usar a capacidade máxima das renováveis - uso atual
        excesso = np.zeros(periodos)
        if microrrede.solar:
            import json
            curva_solar_raw = json.loads(microrrede.solar.curva_geracao)
            curva_solar = np.array([min(float(v), microrrede.solar.potencia) for v in curva_solar_raw])
            excesso += np.maximum(0, curva_solar - uso_solar)
            # Desconta o que foi usado para carregar a bateria
            recarga = np.abs(uso_energia.get('Recarga Bateria', np.zeros(periodos)).values)
            excesso = np.maximum(0, excesso - recarga)
            
        # O déficit é exatamente o que a concessionária está suprindo
        deficit = uso_concessionaria
        
        return ResultadoAnalise(
            microrrede=microrrede,
            metodo=metodo,
            periodos=periodos,
            uso_solar=uso_solar,
            uso_bateria=uso_bateria,
            uso_diesel=uso_diesel,
            uso_biogas=uso_biogas,
            uso_concessionaria=uso_concessionaria,
            custo_solar=custo_solar,
            custo_bateria=custo_bateria,
            custo_diesel=custo_diesel,
            custo_biogas=custo_biogas,
            custo_concessionaria=custo_concessionaria,
            curva_carga=curva_carga,
            excesso=excesso,
            deficit=deficit,
            nivel_bateria=niveis_tanques.get('Bateria', np.zeros(periodos)).values
        )

    @staticmethod
    def from_milp(microrrede: Microrrede, df_resultado: pd.DataFrame) -> 'ResultadoAnalise':
        """
        Converte a saída do MILP para o formato padronizado.
        """
        periodos = len(df_resultado)
        
        uso_solar = df_resultado.get('Solar', np.zeros(periodos)).values
        uso_bateria = df_resultado.get('Bateria', np.zeros(periodos)).values
        uso_diesel = df_resultado.get('Diesel', np.zeros(periodos)).values
        uso_biogas = df_resultado.get('Biogas', np.zeros(periodos)).values
        uso_concessionaria = df_resultado.get('Concessionaria', np.zeros(periodos)).values
        
        custo_solar = uso_solar * (microrrede.solar.custo_kwh if microrrede.solar else 0) / 60
        custo_bateria = uso_bateria * (microrrede.bateria.custo_kwh if microrrede.bateria else 0) / 60
        custo_diesel = uso_diesel * (microrrede.diesel.custo_por_kWh if microrrede.diesel else 0) / 60
        custo_biogas = uso_biogas * (microrrede.biogas.custo_por_kWh if microrrede.biogas else 0) / 60
        custo_concessionaria = uso_concessionaria * (microrrede.concessionaria.tarifa if microrrede.concessionaria else 0) / 60
        
        curva_carga = df_resultado.get('Carga', np.zeros(periodos)).values
        
        # No MILP, o excesso vendido já pode estar calculado como 'Venda'
        excesso = df_resultado.get('Venda', np.zeros(periodos)).values
        deficit = uso_concessionaria
        
        return ResultadoAnalise(
            microrrede=microrrede,
            metodo="milp",
            periodos=periodos,
            uso_solar=uso_solar,
            uso_bateria=uso_bateria,
            uso_diesel=uso_diesel,
            uso_biogas=uso_biogas,
            uso_concessionaria=uso_concessionaria,
            custo_solar=custo_solar,
            custo_bateria=custo_bateria,
            custo_diesel=custo_diesel,
            custo_biogas=custo_biogas,
            custo_concessionaria=custo_concessionaria,
            curva_carga=curva_carga,
            excesso=excesso,
            deficit=deficit,
            nivel_bateria=np.zeros(periodos) # TODO: extrair do milp se necessário
        )
