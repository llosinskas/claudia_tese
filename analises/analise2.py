"""
Análise 2 — Uso otimizado das fontes de energia sem deslizamento de cargas.

Ordena fontes por custo crescente e usa em cascata (mais barata primeiro).
Carrega bateria com excesso de energia solar.
"""

import numpy as np
import pandas as pd
import json

from models.Microrrede import Microrrede
from Tools.GerarCurvaCarga import CurvaCarga
from Tools.Diesel.Ferramentas_diesel import Consumo_diesel
from Tools.Biogas.Ferramentas_biogas import Consumo_biogas, Geracao_biogas_instantanea
from Tools.Bateria.Ferramentas_bateria import Carregar_bateria, Descarrega_bateria, Tempo_Carga
from analises.config import ConfigAnalise


class Analise2:
    """
    Análise 2: Otimização por ordem de custo, sem deslizamento de carga.
    
    Características:
    - Ordena fontes por custo crescente (via ConfigAnalise)
    - Usa fontes em cascata (mais barata primeiro)
    - Carrega bateria com excesso solar
    - NÃO desliza cargas
    """
    
    @staticmethod
    def executar(microrrede: Microrrede, config: ConfigAnalise = None):
        """
        Executa a Análise 2.
        
        Args:
            microrrede: Objeto Microrrede
            config: ConfigAnalise com flags liga/desliga
            
        Returns:
            Tupla com resultados da análise
        """
        if config is None:
            config = ConfigAnalise()
        
        bateria = microrrede.bateria if config.fonte_disponivel('Bateria', microrrede) else None
        biogas = microrrede.biogas if config.fonte_disponivel('Biogas', microrrede) else None
        diesel = microrrede.diesel if config.fonte_disponivel('Diesel', microrrede) else None
        concessionaria = microrrede.concessionaria if config.fonte_disponivel('Concessionaria', microrrede) else None
        solar = microrrede.solar if config.fonte_disponivel('Solar', microrrede) else None
        
        curva_solar = []
        if solar is not None:
            curva_solar_raw = json.loads(solar.curva_geracao)
            curva_solar = [min(v, solar.potencia) for v in curva_solar_raw]
        
        resultado_microrrede = pd.DataFrame(columns=['Carga', 'Bateria', 'Solar', 'Diesel', 'Biogas', 'Concessionaria'])
        carga = microrrede.carga
        curva_carga = CurvaCarga(carga)
        resultado_microrrede['Carga'] = curva_carga
        
        tempo_recarga_bateria = 0
        custo_kwh = pd.DataFrame()
        geracao_biogas = 0
        nivel_instantaneo_biogas = 0
        
        if bateria is not None:
            custo_kwh.loc[0, 'Bateria'] = bateria.custo_kwh
            tempo_recarga_bateria = Tempo_Carga(bateria)
            nivel_instantaneo_bateria = bateria.capacidade
        else:
            custo_kwh.loc[0, 'Bateria'] = None
        
        if biogas is not None:
            custo_kwh.loc[0, 'Biogas'] = biogas.custo_por_kWh
            geracao_biogas = Geracao_biogas_instantanea(biogas)
            nivel_instantaneo_biogas = biogas.tanque
        else:
            custo_kwh.loc[0, 'Biogas'] = None
        
        if diesel is not None:
            custo_kwh.loc[0, 'Diesel'] = diesel.custo_por_kWh
            nivel_instantaneo_diesel = diesel.tanque
        else:
            custo_kwh.loc[0, 'Diesel'] = None
        
        if solar is not None:
            custo_kwh.loc[0, 'Solar'] = solar.custo_kwh
        else:
            custo_kwh.loc[0, 'Solar'] = None
        
        custo_kwh_ordenado = custo_kwh.sort_values(by=0, axis=1)
        
        nivel_bateria = np.zeros(len(curva_carga))
        nivel_biogas = np.zeros(len(curva_carga))
        nivel_diesel = np.zeros(len(curva_carga))
        
        uso_solar = np.zeros(len(curva_carga))
        uso_diesel = np.zeros(len(curva_carga))
        uso_biogas = np.zeros(len(curva_carga))
        uso_bateria = np.zeros(len(curva_carga))
        uso_concessionaria = np.zeros(len(curva_carga))
        recarga_bateria = np.zeros(len(curva_carga))
        total_carga = 0
        sobra = []
        total_sobra = 0
        sum_fontes = np.zeros(len(curva_carga))
        custo_solar = np.zeros(len(curva_carga))
        custo_diesel = np.zeros(len(curva_carga))
        custo_biogas = np.zeros(len(curva_carga))
        custo_bateria = np.zeros(len(curva_carga))
        custo_concessionaria = np.zeros(len(curva_carga))
        custo_total_instantaneo = np.zeros(len(curva_carga))
        custo_total = 0
        
        for i, carga_instantanea in enumerate(curva_carga):
            carga_necessaria = carga_instantanea
            total_carga += carga_instantanea
            if biogas is not None:
                if nivel_instantaneo_biogas < biogas.tanque:
                    nivel_instantaneo_biogas += geracao_biogas
                nivel_biogas[i] = nivel_instantaneo_biogas
            if diesel is not None:
                nivel_diesel[i] = nivel_instantaneo_diesel

            for fonte in custo_kwh_ordenado.columns:
                if carga_necessaria <= 0:
                    break
                
                match fonte:
                    case 'Solar':
                        if solar is not None:
                            if curva_solar[i] >= carga_necessaria:
                                uso_solar[i] = carga_necessaria
                                custo_solar[i] = uso_solar[i] * solar.custo_kwh / 60
                                carga_necessaria = 0
                                if bateria is not None:
                                    excesso_solar = curva_solar[i] - uso_solar[i]
                                    nivel_antes = nivel_instantaneo_bateria
                                    nivel_instantaneo_bateria, alerta, energia_rejeitada = Carregar_bateria(nivel_instantaneo_bateria, bateria, excesso_solar / 60)
                                    nivel_bateria[i] = nivel_instantaneo_bateria
                                    recarga_bateria[i] = excesso_solar - energia_rejeitada * 60 if excesso_solar > 0 else 0
                            elif curva_solar[i] < carga_necessaria:
                                custo_solar[i] = curva_solar[i] * solar.custo_kwh / 60
                                uso_solar[i] = curva_solar[i]
                                carga_necessaria -= uso_solar[i]

                    case 'Bateria':
                        if bateria is not None:
                            if bateria.potencia >= carga_necessaria:
                                if nivel_instantaneo_bateria > bateria.capacidade_min:
                                    uso_bateria[i] = carga_necessaria
                                    custo_bateria[i] = uso_bateria[i] * bateria.custo_kwh / 60
                                    nivel_instantaneo_bateria = Descarrega_bateria(nivel_instantaneo_bateria, carga_necessaria / 60, bateria)
                                    nivel_bateria[i] = nivel_instantaneo_bateria
                                    carga_necessaria = 0
                            elif bateria.potencia < carga_necessaria:
                                if nivel_instantaneo_bateria > bateria.capacidade_min:
                                    uso_bateria[i] = bateria.potencia
                                    custo_bateria[i] = uso_bateria[i] * bateria.custo_kwh / 60
                                    nivel_instantaneo_bateria = Descarrega_bateria(nivel_instantaneo_bateria, bateria.potencia / 60, bateria)
                                    nivel_bateria[i] = nivel_instantaneo_bateria
                                    carga_necessaria -= bateria.potencia

                    case 'Biogas':
                        if biogas is not None:
                            if biogas.potencia >= carga_necessaria:
                                if nivel_instantaneo_biogas > 0:
                                    uso_biogas[i] = carga_necessaria
                                    custo_biogas[i] = uso_biogas[i] * biogas.custo_por_kWh / 60
                                    alerta, nivel_instantaneo_biogas, consumo = Consumo_biogas(nivel_instantaneo_biogas, carga_necessaria, biogas)
                                    carga_necessaria = 0
                            elif biogas.potencia < carga_necessaria:
                                if nivel_instantaneo_biogas > 0:
                                    uso_biogas[i] = biogas.potencia
                                    custo_biogas[i] = uso_biogas[i] * biogas.custo_por_kWh / 60
                                    nivel_instantaneo_biogas -= uso_biogas[i] / 60
                                carga_necessaria -= biogas.potencia
                    
                    case 'Diesel':
                        if diesel is not None:
                            if diesel.potencia >= carga_necessaria:
                                if nivel_instantaneo_diesel > 0:
                                    uso_diesel[i] = carga_necessaria
                                    custo_diesel[i] = uso_diesel[i] * diesel.custo_por_kWh / 60
                                    alerta, nivel_instantaneo_diesel, consumo = Consumo_diesel(nivel_instantaneo_diesel, carga_necessaria, diesel)
                                    carga_necessaria = 0
                            elif diesel.potencia < carga_necessaria:
                                if nivel_instantaneo_diesel > 0:
                                    uso_diesel[i] = diesel.potencia
                                    custo_diesel[i] = uso_diesel[i] * diesel.custo_por_kWh / 60
                                    alerta, nivel_instantaneo_diesel, consumo = Consumo_diesel(nivel_instantaneo_diesel, uso_diesel[i], diesel)
                                    carga_necessaria -= diesel.potencia
            
            # Sobra de energia
            sobra_instantanea = 0
            if diesel is not None:
                sobra_instantanea = diesel.potencia
            elif biogas is not None:
                sobra_instantanea += biogas.potencia
            elif bateria is not None:
                sobra_instantanea += bateria.potencia
            elif solar is not None:
                sobra_instantanea += curva_solar[i]

            if sobra_instantanea > carga_instantanea:
                sobra.append(sobra_instantanea - carga_instantanea)
            
            custo_total_instantaneo[i] = custo_solar[i] + custo_bateria[i] + custo_biogas[i] + custo_diesel[i] + custo_concessionaria[i]
            
            # Falta de energia (Compra da rede)
            sum_fontes[i] = uso_bateria[i] + uso_biogas[i] + uso_diesel[i] + uso_solar[i]
            
            falta = curva_carga[i] - (uso_bateria[i] + uso_biogas[i] + uso_diesel[i] + uso_solar[i])
            if curva_carga[i] >= falta and concessionaria is not None:
                uso_concessionaria[i] = falta
                custo_concessionaria[i] = uso_concessionaria[i] * concessionaria.tarifa / 60
        
        total_uso_solar = uso_solar.sum()
        total_uso_bateria = uso_bateria.sum()
        total_uso_biogas = uso_biogas.sum()
        total_uso_diesel = uso_diesel.sum()
        total_uso_concessionaria = uso_concessionaria.sum()
        total_sobra = sum(sobra)
        
        total = pd.DataFrame({
            "Solar": total_uso_solar,
            "Bateria": total_uso_bateria,
            "Biogas": total_uso_biogas,
            "Diesel": total_uso_diesel,
            "Concessionaria": total_uso_concessionaria,
            "Sobra": total_sobra
        }, index=[0])
        
        demanda_negativa = -np.abs(curva_carga)
        uso_energia = pd.DataFrame({
            "Solar": uso_solar,
            "Bateria": uso_bateria,
            "Biogas": uso_biogas,
            "Diesel": uso_diesel,
            "Concessionaria": uso_concessionaria,
            "Recarga Bateria": -recarga_bateria,
            "Carga": demanda_negativa
        })
        niveis_tanques = pd.DataFrame({
            "Bateria": nivel_bateria,
            "Biogas": nivel_biogas,
            "Diesel": nivel_diesel,
        })

        custo_total = custo_total_instantaneo.sum()
        
        return (custo_kwh_ordenado, total_uso_diesel, total_uso_bateria,
                total_uso_concessionaria, total_uso_biogas, total_uso_solar,
                total_sobra, total_carga, total, uso_energia, niveis_tanques,
                custo_total, custo_total_instantaneo)
