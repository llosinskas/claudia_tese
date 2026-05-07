"""
Análise 1 — Uso exclusivo de apenas uma fonte de energia durante o dia.

Testa cada fonte isoladamente para verificar se consegue suprir a demanda.
"""

import numpy as np
import pandas as pd
import json

from models.Microrrede import Microrrede
from Tools.GerarCurvaCarga import CurvaCarga
from Tools.Diesel.Ferramentas_diesel import Preco_tanque_diesel
from Tools.Biogas.Ferramentas_biogas import Preco_tanque_biogas
from analises.config import ConfigAnalise


class Analise1:
    """
    Análise 1: Uso exclusivo de apenas uma fonte de energia.
    Testa cada fonte isoladamente para verificar custo e viabilidade.
    """
    
    @staticmethod
    def executar(microrrede: Microrrede, config: ConfigAnalise = None):
        """
        Executa a Análise 1.
        
        Args:
            microrrede: Objeto Microrrede
            config: ConfigAnalise com flags liga/desliga (default: tudo ligado)
            
        Returns:
            Tupla com resultados de cada fonte
        """
        if config is None:
            config = ConfigAnalise()
        
        resultado_microrrede = pd.DataFrame(columns=['Carga', 'Bateria', 'Solar', 'Diesel', 'Biogas', 'Concessionaria'])
        carga = microrrede.carga
        curva_carga = CurvaCarga(carga)
        resultado_microrrede['Carga'] = curva_carga
        total_carga = resultado_microrrede['Carga'].sum()
        
        # === Concessionária ===
        total_concessionaria = 0.0
        valor_concessionaria = np.zeros(1440)
        if config.fonte_disponivel('Concessionaria', microrrede):
            concessionaria = microrrede.concessionaria
            for i, carga_instantanea in enumerate(curva_carga):
                valor = concessionaria.Preco_concessionaria(carga_instantanea)
                valor_concessionaria[i] = valor
            resultado_microrrede['Concessionaria'] = valor_concessionaria
            total_concessionaria = resultado_microrrede['Concessionaria'].sum()
        
        # === Bateria ===
        nivel_bateria = 0.0
        alerta_bateria = ""
        resultado_bateria = np.zeros(1440)
        total_bateria = 0.0
        
        if config.fonte_disponivel('Bateria', microrrede):
            bateria = microrrede.bateria
            nivel_bateria = bateria.capacidade
            for i, carga_instantanea in enumerate(curva_carga):
                if carga_instantanea < bateria.potencia:
                    if nivel_bateria > bateria.capacidade_min:
                        nivel_bateria -= (carga_instantanea * bateria.eficiencia) / 60
                        custo_bateria = bateria.custo_kwh * carga_instantanea / 60
                        resultado_bateria[i] = custo_bateria
                    else:
                        alerta_bateria = "Não consegue suprir a carga!"
                elif carga_instantanea > bateria.potencia:
                    if nivel_bateria > bateria.capacidade_min:
                        nivel_bateria -= (bateria.potencia * bateria.eficiencia) / 60
                        custo_bateria = bateria.custo_kwh * bateria.potencia / 60
                        resultado_bateria[i] = custo_bateria
                    else:
                        alerta_bateria = "Não consegue suprir a carga!"
            resultado_microrrede['Bateria'] = resultado_bateria
            total_bateria = resultado_microrrede['Bateria'].sum()
        else:
            alerta_bateria = "Bateria desligada ou não disponível"
        
        # === Solar ===
        alerta_solar = ""
        resultado_solar = np.zeros(1440)
        total_solar = 0.0
        
        if config.fonte_disponivel('Solar', microrrede):
            solar = microrrede.solar
            carga_instantanea = np.array(curva_carga, dtype=float)
            geracao_solar_raw = json.loads(solar.curva_geracao)
            
            if len(geracao_solar_raw) == len(carga_instantanea):
                for i, geracao in enumerate(geracao_solar_raw):
                    geracao_float = pd.to_numeric(geracao, errors='coerce')
                    geracao_limitada = min(geracao_float, solar.potencia)
                    
                    if geracao_limitada > carga_instantanea[i]:
                        custo_solar = solar.custo_kwh * carga_instantanea[i] / 60
                        resultado_solar[i] = custo_solar
                    elif geracao_limitada < carga_instantanea[i]:
                        custo_solar = solar.custo_kwh * geracao_limitada / 60
                        resultado_solar[i] = custo_solar
                        alerta_solar = "O gerador não supri toda a demanda da carga"
            else:
                alerta_solar = "Erro na leitura dos dados do gerador solar"
            
            resultado_microrrede['Solar'] = resultado_solar
            total_solar = resultado_microrrede['Solar'].sum()
        else:
            alerta_solar = "Solar desligado ou não disponível"
        
        # === Diesel ===
        alerta_diesel = ""
        nivel_diesel = 0.0
        resultado_diesel = np.zeros(1440)
        total_diesel = 0.0
        
        if config.fonte_disponivel('Diesel', microrrede):
            diesel = microrrede.diesel
            nivel_diesel = diesel.tanque
            
            for i, carga_instantanea in enumerate(curva_carga):
                if carga_instantanea < diesel.potencia:
                    alerta_diesel, nivel_diesel, valor = Preco_tanque_diesel(nivel_diesel, carga_instantanea, diesel)
                    resultado_diesel[i] = valor
                elif carga_instantanea > diesel.potencia:
                    alerta_diesel, nivel_diesel, valor = Preco_tanque_diesel(nivel_diesel, diesel.potencia, diesel)
                    resultado_diesel[i] = valor
                    
            resultado_microrrede['Diesel'] = resultado_diesel
            total_diesel = resultado_microrrede['Diesel'].sum()
        else:
            alerta_diesel = "Diesel desligado ou não disponível"
        
        # === Biogas ===
        alerta_biogas = ""
        resultado_biogas = np.zeros(1440)
        total_biogas = 0.0
        
        if config.fonte_disponivel('Biogas', microrrede):
            biogas = microrrede.biogas
            nivel = biogas.tanque
            
            for i, carga_instantanea in enumerate(curva_carga):
                if carga_instantanea < biogas.potencia:
                    alerta_biogas, nivel, valor = Preco_tanque_biogas(nivel, carga_instantanea, biogas)
                    resultado_biogas[i] = valor
                elif carga_instantanea > biogas.potencia:
                    alerta_biogas, nivel, valor = Preco_tanque_biogas(nivel, biogas.potencia, biogas)
                    resultado_biogas[i] = valor
                    
            resultado_microrrede["Biogas"] = resultado_biogas
            total_biogas = resultado_microrrede["Biogas"].sum()
        else:
            alerta_biogas = "Biogás desligado ou não disponível"
        
        return (total_carga, total_concessionaria, alerta_bateria, total_bateria,
                alerta_solar, total_solar, alerta_diesel, total_diesel,
                alerta_biogas, total_biogas, resultado_microrrede)
