# Principal controle é o microgerenciamento do sistema de energia
# Rodar primeiro dia normalmente sem controle das cargas, depois analisar o perfil de consumo e ajustar as cargas com prioridade 2, 4
''' Análise 1
    Uso apenas de uma fonte de energia:
    -> se não conseguir alarme "não supri energia necessária"
    
    Análise 2  
    Otimiza a carga da bateria 
    Não desliza as cargas quando possível 
    Vende e compra da rede sem a interação com outras microrredes 

    Análise 3 
    Otimiza o carga da bateria
    Desliza as cargas quando possível 
    Vende e compra das microrredes 

    Análsise 4 
    Otimiza o carga da bateria
    Desliza as cargas quando possível 
    Otimiza pelo custo global de energia
    Vende e compra das microrredes 

'''
import pandas as pd 
import numpy as np 
from Tools.Carga.Ferramentas_cargas import Otimizado, deslize_carga, Tempo_ligado
from models.Microrrede import Microrrede, Carga
from models.CRUD import Ler, Ler_Objeto
from Tools.GerarCurvaCarga import CurvaCarga
from Tools.Diesel.Ferramentas_diesel import Consumo_diesel, Preco_tanque_diesel
from Tools.Biogas.Ferramentas_biogas import Consumo_biogas, Geracao_biogas_instantanea, Preco_tanque_biogas
from Tools.Bateria.Ferramentas_bateria import Carregar_bateria, Descarrega_bateria, Tempo_Carga
import streamlit as st 
import json
from Tools.Graficos.Sankey_Chart import sankey_chart
from Tools.Graficos.LineChartMath import Grafico_linha
from otmizadores.milp_controle_microrrede import analise_milp as analise_milp_func, analise_milp_sem_venda, MILPMicrorredes, analise_milp_com_deslizamento
from otmizadores.pso import analise_pso as analise_pso_func, PSOMicrorredes
from threading import Thread
class Analise1(Thread):
    def __init__(self):
        super().__init__()
        self.return_value = None

    def analise_1(microrrede: Microrrede):
        with st.spinner("Carregando a análise"):
            resultado_microrrede = pd.DataFrame(columns=['Carga', 'Bateria', 'Solar', 'Diesel', 'Biogas', 'Concessionaria'])
            carga = microrrede.carga
            curva_carga = CurvaCarga(carga)
            resultado_microrrede['Carga'] = curva_carga
            total_carga = resultado_microrrede['Carga'].sum()
            concessionaria = microrrede.concessionaria
            valor_concessionaria = np.zeros(1440)
            for i,carga_instantanea in enumerate(curva_carga):
                valor = concessionaria.Preco_concessionaria(carga_instantanea)
                valor_concessionaria[i] = (valor)
            resultado_microrrede['Concessionaria'] = valor_concessionaria
            total_concessionaria = resultado_microrrede['Concessionaria'].sum()
        
            nivel_bateria       = 0.0
            alerta_bateria      = ""
            resultado_bateria   = np.zeros(1440)
            total_bateria       = 0.0
            
            alerta_solar        = ""
            resultado_solar     = np.zeros(1440)
            total_solar         = 0.0
            total_solar         = 0.0

            alerta_diesel       = ""
            nivel_diesel        = 0.0   
            resultado_diesel    = np.zeros(1440)
            total_diesel        = 0.0

            alerta_biogas       = ""
            resultado_biogas    = np.zeros(1440)
            total_biogas        = 0.0
            
            if microrrede.bateria != None:
                bateria = microrrede.bateria
                nivel_bateria = bateria.capacidade
                for i,carga_instantanea in enumerate(curva_carga):
                    # A bateria supre toda a demanda
                    if carga_instantanea<bateria.potencia: 
                        if nivel_bateria>bateria.capacidade_min:
                            nivel_bateria -= (carga_instantanea*bateria.eficiencia)/60 
                            custo_bateria = bateria.custo_kwh*carga_instantanea/60
                            resultado_bateria[i] = custo_bateria
                        else:
                            alerta_bateria = "Não consegue suprir a carga!"
                            
                    elif carga_instantanea>bateria.potencia:
                        if nivel_bateria>bateria.capacidade_min:
                            nivel_bateria -= (bateria.potencia*bateria.eficiencia)/60 
                            custo_bateria = bateria.custo_kwh*bateria.potencia/60
                            resultado_bateria[i] = custo_bateria
                        else:
                            alerta_bateria = "Não consegue suprir a carga!"
                            
                resultado_microrrede['Bateria'] = resultado_bateria
                total_bateria = resultado_microrrede['Bateria'].sum()
        
            if microrrede.solar != None:
                solar = microrrede.solar
                carga_instantanea = np.array(curva_carga, dtype=float)
                geracao_solar_raw = json.loads(solar.curva_geracao)
                
                if len(geracao_solar_raw) == len(carga_instantanea):
                    for i, geracao in enumerate(geracao_solar_raw):
                        geracao_float = pd.to_numeric(geracao, errors='coerce')
                        # Limita geração ao máximo da potência do painel solar
                        geracao_limitada = min(geracao_float, solar.potencia)
                        
                        if geracao_limitada > carga_instantanea[i]:
                            custo_solar = solar.custo_kwh*carga_instantanea[i]/60
                            resultado_solar[i] = custo_solar
                        elif geracao_limitada<carga_instantanea[i]:
                            custo_solar = solar.custo_kwh*geracao_limitada/60
                            resultado_solar[i]=custo_solar
                            alerta_solar="O gerador não supri toda a demanda da carga"
                else:
                    alerta_solar="Erro na leitura dos dados do gerador solar"
                
                resultado_microrrede['Solar'] = resultado_solar
                total_solar = resultado_microrrede['Solar'].sum()
            
            if microrrede.diesel!=None:
                    diesel = microrrede.diesel
                    nivel_diesel = diesel.tanque
                    
                    for i,carga_instantanea in enumerate(curva_carga):
                        if carga_instantanea<diesel.potencia:
                            alerta_diesel, nivel_diesel, valor = Preco_tanque_diesel(nivel_diesel, carga_instantanea,diesel)
                            resultado_diesel[i]=valor
                        elif carga_instantanea > diesel.potencia:
                            alerta_diesel,nivel_diesel, valor = Preco_tanque_diesel(nivel_diesel, diesel.potencia, diesel)
                            resultado_diesel[i]=valor
                        
                    resultado_microrrede['Diesel'] = resultado_diesel
                    total_diesel = resultado_microrrede['Diesel'].sum()
                    
            if microrrede.biogas != None:
                    biogas = microrrede.biogas
                    nivel = biogas.tanque
                    
                    for i,carga_instantanea in enumerate(curva_carga):
                        if carga_instantanea<biogas.potencia:
                            alerta_biogas, nivel, valor = Preco_tanque_biogas(nivel, carga_instantanea, biogas)
                            resultado_biogas[i] = valor
                        elif carga_instantanea>biogas.potencia:
                            alerta_biogas, nivel, valor = Preco_tanque_biogas(nivel, biogas.potencia, biogas)
                            resultado_biogas[i] = valor
                        
                    resultado_microrrede["Biogas"] = resultado_biogas
                    total_biogas = resultado_microrrede["Biogas"].sum()
            
            return total_carga, total_concessionaria,alerta_bateria, total_bateria,alerta_solar, total_solar, alerta_diesel, total_diesel, alerta_biogas, total_biogas,resultado_microrrede

class Analise2(Thread):
    def __init__(self):
        super().__init__()
        self.return_value = None
    def analise_2(microrrede: Microrrede):
        with st.spinner("Carregando..."):
            bateria = microrrede.bateria
            biogas = microrrede.biogas
            diesel = microrrede.diesel
            concessionaria = microrrede.concessionaria
            solar = microrrede.solar
            curva_solar = []    
            if solar != None:
                curva_solar_raw = json.loads(solar.curva_geracao)
                # Normaliza curva ao limite de potência do painel solar
                curva_solar = [min(v, solar.potencia) for v in curva_solar_raw]
            resultado_microrrede = pd.DataFrame(columns=['Carga', 'Bateria', 'Solar', 'Diesel', 'Biogas', 'Concessionaria'])
            carga = microrrede.carga
            curva_carga = CurvaCarga(carga)
            resultado_microrrede['Carga'] = curva_carga
            tempo_recarga_bateria = 0  
            custo_kwh = pd.DataFrame()
            geracao_biogas = 0
            nivel_instantaneo_biogas = 0
            if bateria != None:     
                custo_kwh_bateria = bateria.custo_kwh
                custo_kwh.loc[0, 'Bateria'] = custo_kwh_bateria
                tempo_recarga_bateria = Tempo_Carga(bateria)
                nivel_instantaneo_bateria = bateria.capacidade 
            elif bateria == None:
                custo_kwh.loc[0, 'Bateria'] = None
            if biogas != None:
                custo_kwh_biogas = biogas.custo_por_kWh
                custo_kwh.loc[0, 'Biogas'] = custo_kwh_biogas
                geracao_biogas = Geracao_biogas_instantanea(biogas)
                nivel_instantaneo_biogas = biogas.tanque

            elif biogas == None:
                custo_kwh.loc[0, 'Biogas'] = None
                    
            if diesel != None:
                custo_kwh_diesel = diesel.custo_por_kWh
                custo_kwh.loc[0, 'Diesel'] = custo_kwh_diesel
                nivel_instantaneo_diesel = diesel.tanque
            elif diesel == None:
                custo_kwh.loc[0, 'Diesel'] = None
            if solar != None:  
                custo_kwh_solar = solar.custo_kwh
                custo_kwh.loc[0, 'Solar'] = custo_kwh_solar
            elif solar == None:
                custo_kwh.loc[0, 'Solar'] = None
            custo_kwh_ordenado = custo_kwh.sort_values(by=0, axis=1)
            nivel_bateria = np.zeros(len(curva_carga))
            nivel_biogas = np.zeros(len(curva_carga))
            nivel_diesel = np.zeros(len(curva_carga))
            
            uso_solar = np.zeros(len(curva_carga))
            uso_diesel=np.zeros(len(curva_carga))
            uso_biogas=np.zeros(len(curva_carga))   
            uso_bateria = np.zeros(len(curva_carga))
            uso_concessionaria = np.zeros(len(curva_carga))
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
                if biogas != None:
                    if nivel_instantaneo_biogas < biogas.tanque:
                        nivel_instantaneo_biogas += geracao_biogas
                    nivel_biogas[i] = nivel_instantaneo_biogas
                if diesel != None:
                    nivel_diesel[i] = nivel_instantaneo_diesel

                for fonte in custo_kwh_ordenado.columns:
                    if carga_necessaria <= 0:
                        break
                    
                    match fonte:
                        case 'Solar':

                            if solar != None:
                                if curva_solar[i] >= carga_necessaria:
                                    uso_solar[i] = carga_necessaria
                                    custo_solar[i] = uso_solar[i]*solar.custo_kwh/60
                                    carga_necessaria = 0
                                    if bateria != None:
                                        nivel_instantaneo_bateria, alerta, energia_rejeitada = Carregar_bateria(nivel_instantaneo_bateria, bateria, (curva_solar[i]-carga_necessaria)/60)
                                        nivel_bateria[i] = nivel_instantaneo_bateria/60

                                elif curva_solar[i] < carga_necessaria:
                                    custo_solar[i] = curva_solar[i]*solar.custo_kwh/60
                                    uso_solar[i] = curva_solar[i]
                                    carga_necessaria -= uso_solar[i]

                        case 'Bateria':
                            if bateria != None:
                                if bateria.potencia >= carga_necessaria:
                                    if nivel_instantaneo_bateria > bateria.capacidade_min:
                                        
                                        # uso_bateria[i] = carga_necessaria/(bateria.eficiencia/100)/60
                                        uso_bateria[i] = carga_necessaria
                                        custo_bateria[i] = uso_bateria[i]*bateria.custo_kwh/60
                                        nivel_instantaneo_bateria = Descarrega_bateria(nivel_instantaneo_bateria, carga_necessaria/60, bateria)
                                        nivel_bateria[i] = nivel_instantaneo_bateria
                                        carga_necessaria = 0


                                elif bateria.potencia < carga_necessaria:
                                    if nivel_instantaneo_bateria > bateria.capacidade_min:
                                        uso_bateria[i] = bateria.potencia
                                        custo_bateria[i] = uso_bateria[i]*bateria.custo_kwh/60
                                        nivel_instantaneo_bateria = Descarrega_bateria(nivel_instantaneo_bateria, bateria.potencia/60, bateria)
                                        nivel_bateria[i] = nivel_instantaneo_bateria                               
                                        carga_necessaria -= bateria.potencia

                        case 'Biogas':
                            if biogas != None:
                                if biogas.potencia >= carga_necessaria:
                                    if nivel_instantaneo_biogas > 0:
                                        uso_biogas[i] = carga_necessaria
                                        custo_biogas[i] = uso_biogas[i]*biogas.custo_por_kWh/60
                                        alerta, nivel_instantaneo_biogas,consumo=Consumo_biogas(nivel_instantaneo_biogas, carga_necessaria, biogas)

                                        carga_necessaria = 0

                                elif biogas.potencia < carga_necessaria:
                                    if nivel_instantaneo_biogas > 0:
                                        uso_biogas[i] = biogas.potencia
                                        custo_biogas[i] = uso_biogas[i]*biogas.custo_por_kWh/60
                                        nivel_instantaneo_biogas -= uso_biogas[i]/60
                                    carga_necessaria -= biogas.potencia
                        case 'Diesel':
                            if fonte == 'Diesel' and diesel != None:
                                if diesel.potencia >= carga_necessaria:
                                    if nivel_instantaneo_diesel > 0:
                                        uso_diesel[i] = carga_necessaria    
                                        custo_diesel[i] = uso_diesel[i]*diesel.custo_por_kWh/60
                                        alerta, nivel_instantaneo_diesel, consumo = Consumo_diesel(nivel_instantaneo_diesel, carga_necessaria, diesel)
                                        carga_necessaria = 0
                                
                                elif diesel.potencia < carga_necessaria:
                                    if nivel_instantaneo_diesel > 0:
                                        uso_diesel[i] = diesel.potencia
                                        custo_diesel[i] = uso_diesel[i]*diesel.custo_por_kWh/60
                                        alerta, nivel_instantaneo_diesel, consumo = Consumo_diesel(nivel_instantaneo_diesel, uso_diesel[i], diesel)
                                        carga_necessaria -= diesel.potencia
                    
                # Sobra de energia (venda para a rede)
                sobra_instantanea = 0
                if diesel != None:
                    sobra_instantanea = diesel.potencia
                elif biogas != None:
                    sobra_instantanea += biogas.potencia
                elif bateria != None:
                    sobra_instantanea += bateria.potencia
                elif solar != None:
                    sobra_instantanea += curva_solar[i]

                if sobra_instantanea > carga_instantanea:
                    sobra.append(sobra_instantanea - carga_instantanea)
                
                custo_total_instantaneo[i] = custo_solar[i] + custo_bateria[i] + custo_biogas[i] + custo_diesel[i]+ custo_concessionaria[i]
                
                # Falta de energia (Compra da rede)            
                sum_fontes[i] = (uso_bateria[i]+uso_biogas[i]+uso_diesel[i]+uso_solar[i])
                
                falta = curva_carga[i] - (uso_bateria[i]+uso_biogas[i]+uso_diesel[i]+uso_solar[i])   
                if curva_carga[i] >= falta:
                    uso_concessionaria[i] = falta
                    custo_concessionaria[i] = uso_concessionaria[i]*concessionaria.tarifa/60
            
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
                "Carga": demanda_negativa
                })
            niveis_tanques = pd.DataFrame({
                "Bateria": nivel_bateria, 
                "Biogas": nivel_biogas,
                "Diesel": nivel_diesel,
                })

            custo_total = custo_total_instantaneo.sum()

            return custo_kwh_ordenado, total_uso_diesel, total_uso_bateria, total_uso_concessionaria, total_uso_biogas, total_uso_solar, total_sobra, total_carga, total, uso_energia, niveis_tanques, custo_total, custo_total_instantaneo

# Deslizar as cargas para os horários de menor custo, priorizando o uso das fontes mais baratas, e otimizando o uso da bateria para suprir os picos de carga.  
class Analise3(Thread): 
    """
    Análise 3: Otimização Heurística com Deslizamento de Carga
    
    Características:
    - Ordena fontes por custo crescente
    - Usa-as em cascata (mais barata primeiro)
    - Carrega bateria com excesso de energia solar
    - Desliza cargas com prioridade 2 e 4 para horários de menor custo
    - Respeita limites de operação de todos os equipamentos
    """
    
    def __init__(self):
        super().__init__()
        self.return_value = None
    
    @staticmethod
    def _inicializar_variaveis(periodos: int) -> dict:
        """Inicializa arrays para armazenar resultados horários."""
        return {
            # Uso de energia por fonte (kW)
            'uso_solar': np.zeros(periodos),
            'uso_diesel': np.zeros(periodos),
            'uso_biogas': np.zeros(periodos),
            'uso_bateria': np.zeros(periodos),
            'uso_concessionaria': np.zeros(periodos),
            'recarga_bateria': np.zeros(periodos),
            
            # Custos instantâneos (R$)
            'custo_solar': np.zeros(periodos),
            'custo_diesel': np.zeros(periodos),
            'custo_biogas': np.zeros(periodos),
            'custo_bateria': np.zeros(periodos),
            'custo_concessionaria': np.zeros(periodos),
            'custo_total_instantaneo': np.zeros(periodos),
            
            # Níveis de armazenamento
            'nivel_bateria': np.zeros(periodos),
            'nivel_diesel': np.zeros(periodos),
            'nivel_biogas': np.zeros(periodos),
        }
    
    @staticmethod
    def _inicializar_custos_kwh(microrrede: Microrrede) -> pd.DataFrame:
        """Cria DataFrame com custos por kWh de cada fonte ordenados."""
        custo_kwh = pd.DataFrame()
        
        if microrrede.solar:
            custo_kwh.loc[0, 'Solar'] = microrrede.solar.custo_kwh
        
        if microrrede.bateria:
            custo_kwh.loc[0, 'Bateria'] = microrrede.bateria.custo_kwh
        
        if microrrede.biogas:
            custo_kwh.loc[0, 'Biogas'] = microrrede.biogas.custo_por_kWh
        
        if microrrede.diesel:
            custo_kwh.loc[0, 'Diesel'] = microrrede.diesel.custo_por_kWh
        
        return custo_kwh.sort_values(by=0, axis=1)
    
    @staticmethod
    def _inicializar_niveis_armazenamento(microrrede: Microrrede) -> dict:
        """Inicializa níveis instantâneos de armazenamento."""
        niveis = {}
        
        if microrrede.bateria:
            # Nível inicial = máximo operacional (SOC max %)
            nivel_max = microrrede.bateria.capacidade * microrrede.bateria.capacidade_max / 100
            niveis['nivel_bateria'] = nivel_max
        
        if microrrede.diesel:
            niveis['nivel_diesel'] = microrrede.diesel.tanque
        
        if microrrede.biogas:
            niveis['nivel_biogas'] = microrrede.biogas.tanque
            niveis['geracao_biogas'] = Geracao_biogas_instantanea(microrrede.biogas)
        
        return niveis
    
    @staticmethod
    def _gerenciar_bateria(i: int, carga_necessaria: float, excesso_solar: float,
                           resultado: dict, niveis: dict, microrrede: Microrrede) -> tuple:
        """
        Gerencia descarga e recarga da bateria respeitando:
        - Potência máxima: bateria.potencia (kW)
        - Nível mínimo operacional: capacidade * capacidade_min / 100
        - Nível máximo operacional: capacidade * capacidade_max / 100
        - Eficiência: bateria.eficiencia (%)
        
        Returns:
            (carga_necessaria_atualizada, excesso_nao_absorvido)
        """
        if not microrrede.bateria:
            return carga_necessaria, excesso_solar
        
        bateria = microrrede.bateria
        nivel = niveis['nivel_bateria']
        eff = bateria.eficiencia / 100  # percentual → fração
        nivel_min = bateria.capacidade * bateria.capacidade_min / 100
        nivel_max = bateria.capacidade * bateria.capacidade_max / 100
        
        # ===== DESCARGA: suprir demanda restante =====
        if carga_necessaria > 0 and nivel > nivel_min:
            energia_disponivel = nivel - nivel_min  # kWh acima do mínimo
            # Potência máxima que pode entregar em 1 minuto sem violar mínimo
            pot_max_energia = energia_disponivel * 60 * eff
            potencia_descarga = min(bateria.potencia, carga_necessaria, pot_max_energia)
            
            if potencia_descarga > 0:
                # Energia retirada do armazenamento (kWh) = potência entregue / eficiência / 60
                energia_retirada = potencia_descarga / (60 * eff)
                niveis['nivel_bateria'] -= energia_retirada
                niveis['nivel_bateria'] = max(niveis['nivel_bateria'], nivel_min)
                
                resultado['uso_bateria'][i] += potencia_descarga
                resultado['custo_bateria'][i] += potencia_descarga * bateria.custo_kwh / 60
                carga_necessaria -= potencia_descarga
        
        # ===== RECARGA: armazenar excesso de energia solar =====
        excesso_restante = excesso_solar
        if excesso_solar > 0 and niveis['nivel_bateria'] < nivel_max:
            espaco = nivel_max - niveis['nivel_bateria']  # kWh até o máximo
            # Potência máxima que pode absorver em 1 minuto sem exceder máximo
            pot_max_espaco = espaco * 60 / eff
            potencia_recarga = min(bateria.potencia, excesso_solar, pot_max_espaco)
            
            if potencia_recarga > 0:
                # Energia efetivamente armazenada (kWh) = potência injetada * eficiência / 60
                energia_armazenada = potencia_recarga * eff / 60
                niveis['nivel_bateria'] += energia_armazenada
                niveis['nivel_bateria'] = min(niveis['nivel_bateria'], nivel_max)
                
                resultado['recarga_bateria'][i] += potencia_recarga
                excesso_restante = excesso_solar - potencia_recarga
        
        resultado['nivel_bateria'][i] = niveis['nivel_bateria']
        return carga_necessaria, max(0, excesso_restante)
    
    @staticmethod
    def _processar_biogas(i: int, carga_necessaria: float, 
                         resultado: dict, niveis: dict, microrrede: Microrrede) -> float:
        """Processa despacho de energia do biogas."""
        if not microrrede.biogas or niveis['nivel_biogas'] <= 0:
            return carga_necessaria
        
        # Regenera biogas
        if niveis['nivel_biogas'] < microrrede.biogas.tanque:
            niveis['nivel_biogas'] += niveis.get('geracao_biogas', 0)
        
        biogas = microrrede.biogas
        disponivel = min(biogas.potencia, carga_necessaria)
        
        if niveis['nivel_biogas'] > 0:
            resultado['uso_biogas'][i] = disponivel
            resultado['custo_biogas'][i] = disponivel * biogas.custo_por_kWh / 60
            alerta, niveis['nivel_biogas'], _ = Consumo_biogas(niveis['nivel_biogas'], disponivel, biogas)
            resultado['nivel_biogas'][i] = niveis['nivel_biogas']
            return carga_necessaria - disponivel
        
        return carga_necessaria
    
    @staticmethod
    def _processar_diesel(i: int, carga_necessaria: float, 
                         resultado: dict, niveis: dict, microrrede: Microrrede) -> float:
        """Processa despacho de energia do diesel."""
        if not microrrede.diesel or niveis['nivel_diesel'] <= 0:
            return carga_necessaria
        
        diesel = microrrede.diesel
        disponivel = min(diesel.potencia, carga_necessaria)
        
        resultado['uso_diesel'][i] = disponivel
        resultado['custo_diesel'][i] = disponivel * diesel.custo_por_kWh / 60
        alerta, niveis['nivel_diesel'], _ = Consumo_diesel(niveis['nivel_diesel'], disponivel, diesel)
        resultado['nivel_diesel'][i] = niveis['nivel_diesel']
        
        return carga_necessaria - disponivel
    
    @staticmethod
    def _processar_concessionaria(i: int, carga_necessaria: float, 
                                  resultado: dict, microrrede: Microrrede) -> float:
        """Processa compra da rede concessionária para déficit energético."""
        if carga_necessaria > 0:
            resultado['uso_concessionaria'][i] = carga_necessaria
            resultado['custo_concessionaria'][i] = carga_necessaria * microrrede.concessionaria.tarifa / 60
        
        return 0
    
    @staticmethod
    def _executar_simulacao_otimizacao(microrrede: Microrrede, 
                                       curva_carga: list) -> tuple:
        """
        Executa uma simulação completa de otimização com a curva de carga fornecida.
        
        Args:
            microrrede: Objeto da microrrede
            curva_carga: Curva de carga horária (lista ou array)
            
        Returns:
            Tupla com todos os resultados da simulação
        """
        periodos = len(curva_carga)
        resultado = Analise3._inicializar_variaveis(periodos)
        custo_kwh_ordenado = Analise3._inicializar_custos_kwh(microrrede)
        niveis = Analise3._inicializar_niveis_armazenamento(microrrede)
        
        # Carrega e normaliza curva solar
        curva_solar = []
        if microrrede.solar:
            curva_solar_raw = json.loads(microrrede.solar.curva_geracao)
            # Normaliza a curva ao limite de potência máxima do painel
            curva_solar = [min(v, microrrede.solar.potencia) for v in curva_solar_raw]
        
        total_carga = 0
        sobra = []
        
        # Loop principal de simulação
        for i, carga_instantanea in enumerate(curva_carga):
            carga_necessaria = carga_instantanea
            total_carga += carga_instantanea
            excesso_solar = 0.0
            
            # Despacha fontes em ordem de custo crescente
            for fonte in custo_kwh_ordenado.columns:
                if carga_necessaria <= 0 and excesso_solar <= 0:
                    break
                
                match fonte:
                    case 'Solar':
                        if microrrede.solar and i < len(curva_solar) and curva_solar[i] > 0:
                            geracao = curva_solar[i]
                            uso = min(geracao, carga_necessaria)
                            resultado['uso_solar'][i] = uso
                            resultado['custo_solar'][i] = uso * microrrede.solar.custo_kwh / 60
                            carga_necessaria -= uso
                            excesso_solar = geracao - uso
                    case 'Bateria':
                        carga_necessaria, excesso_restante = Analise3._gerenciar_bateria(
                            i, carga_necessaria, excesso_solar, resultado, niveis, microrrede
                        )
                        excesso_solar = 0
                    case 'Biogas':
                        carga_necessaria = Analise3._processar_biogas(
                            i, carga_necessaria, resultado, niveis, microrrede
                        )
                    case 'Diesel':
                        carga_necessaria = Analise3._processar_diesel(
                            i, carga_necessaria, resultado, niveis, microrrede
                        )
            
            # Se Solar veio depois de Bateria na ordenação, processar excesso pendente
            if excesso_solar > 0:
                _, excesso_final = Analise3._gerenciar_bateria(
                    i, 0, excesso_solar, resultado, niveis, microrrede
                )
            
            # Supri déficit com concessionária
            Analise3._processar_concessionaria(i, carga_necessaria, resultado, microrrede)
            
            # Calcula custo total instantâneo
            resultado['custo_total_instantaneo'][i] = (
                resultado['custo_solar'][i] + 
                resultado['custo_bateria'][i] + 
                resultado['custo_biogas'][i] + 
                resultado['custo_diesel'][i] + 
                resultado['custo_concessionaria'][i]
            )
        
        # Calcula totais
        total_uso_solar = resultado['uso_solar'].sum()
        total_uso_bateria = resultado['uso_bateria'].sum()
        total_uso_biogas = resultado['uso_biogas'].sum()
        total_uso_diesel = resultado['uso_diesel'].sum()
        total_uso_concessionaria = resultado['uso_concessionaria'].sum()
        total_sobra = sum(sobra) if sobra else 0
        
        # ===== VALIDAÇÃO FINAL: Garante que recarga NUNCA excede bateria.potencia =====
        if microrrede.bateria:
            resultado['recarga_bateria'] = np.minimum(resultado['recarga_bateria'], microrrede.bateria.potencia)
        
        return (
            custo_kwh_ordenado,
            total_uso_diesel,
            total_uso_bateria,
            total_uso_concessionaria,
            total_uso_biogas,
            total_uso_solar,
            total_sobra,
            total_carga,
            resultado['uso_solar'],
            resultado['uso_bateria'],
            resultado['uso_biogas'],
            resultado['uso_diesel'],
            resultado['uso_concessionaria'],
            curva_carga,
            resultado['nivel_bateria'],
            resultado['nivel_biogas'],
            resultado['nivel_diesel'],
            resultado['custo_total_instantaneo'],
            resultado['recarga_bateria'],
        )
    
    @staticmethod
    def _deslizar_cargas_otimizado(microrrede: Microrrede, 
                                   curva_carga_original: list,
                                   curva_custo: np.ndarray) -> list:
        """
        Desliza cargas com prioridade 2 e 4 para horários de menor custo.
        
        Args:
            microrrede: Objeto da microrrede
            curva_carga_original: Curva de carga original
            curva_custo: Curva de custo instantâneo (R$/período)
            
        Returns:
            Nova curva de carga com cargas deslizadas
        """
        if not microrrede.carga:
            return curva_carga_original
        
        # Usa função existente de deslizamento
        curva_deslizada = deslize_carga(microrrede.carga, curva_custo)
        return curva_deslizada.tolist() if isinstance(curva_deslizada, np.ndarray) else curva_deslizada
    
    def analise_3(microrrede: Microrrede):
        """
        Executa a Análise 3 com otimização heurística e deslizamento de cargas.
        
        Processo em duas etapas:
        1. Executa simulação com cargas nos horários originais
        2. Identifica horários de menor custo e desliza cargas com prioridade 2 e 4
        3. Executa nova simulação com cargas otimizadas
        
        Args:
            microrrede: Objeto da microrrede a analisar
            
        Returns:
            Dict com 'original' e 'otimizado', cada um contendo tupla de resultados
        """
        # ===== ETAPA 1: Executa com curva original =====
        curva_carga_original = CurvaCarga(microrrede.carga)
        resultado_original = Analise3._executar_simulacao_otimizacao(microrrede, curva_carga_original)
        
        # Extrai curva de custo instantâneo para deslizamento
        custo_instantaneo = resultado_original[17]  # custo_total_instantaneo
        
        # ===== ETAPA 2: Desliza cargas baseado em custos =====
        curva_carga_otimizada = Analise3._deslizar_cargas_otimizado(
            microrrede, curva_carga_original, custo_instantaneo
        )
        
        # ===== ETAPA 3: Executa com curva otimizada =====
        resultado_otimizado = Analise3._executar_simulacao_otimizacao(microrrede, curva_carga_otimizada)
        
        # ===== Retorna ambos os resultados =====
        return {
            'original': resultado_original,
            'otimizado': resultado_otimizado,
            'curva_carga_original': curva_carga_original,
            'curva_carga_otimizada': curva_carga_otimizada
        }        
            
class Analise4(Thread):
    def __init__(self):
        super().__init__()
        self.return_value = None
    def analise4( microrredes:Microrrede):
        for microrrede in microrredes:
            st.subheader(f"{microrrede}")
            curva_custo, curva_custo_otimizado,curva_carga, curva_carga_otimizada = Otimizado(microrrede)   
            curva_custo_total = curva_custo.sum()
            st.write(f"Curva de custo da microrrede sem otimização: R$ {curva_custo_total:,.2f}")
            curva_custo_otimizado_total = curva_custo_otimizado.sum()
            st.write(f"Curva de custo da microrrede com otimização: R$ {curva_custo_otimizado_total:,.2f}")
            df = pd.DataFrame({
                "Curva Carga sem otimização":curva_carga, 
                "Curva Carga Otimizada": curva_carga_otimizada
            })

            st.line_chart(df)
            df  = pd.DataFrame({
                "Curva de custo sem otimização": curva_custo,
                "Curva de custo com otimização": curva_custo_otimizado
            })
            st.line_chart(df, x_label="Tempo (min)", y_label="Custo (R$)")


def analise_5_milp(microrrede: Microrrede, index: int = 0):
    """
    Análise 5 - MILP COM DESLIZAMENTO INTEGRADO DE CARGAS
    
    Usa variáveis binárias para determinar o melhor horário de cada carga 
    com prioridade 2 e 4, otimizando dentro do modelo MILP (uma única resolução).
    
    Args:
        microrrede: Objeto Microrrede a otimizar
        index: Índice único para diferenciar chaves em loops (default: 0)
    """
    st.subheader("Análise 5: MILP com Deslizamento Integrado (Prioridades 2 e 4)")
    
    with st.spinner("Otimizando microrrede com MILP (variáveis binárias para deslizamento)..."):
        # ===== RESOLUÇÃO ÚNICA COM DESLIZAMENTO INTEGRADO =====
        df_resultado, custos, solucao = analise_milp_com_deslizamento(microrrede)
        
        if df_resultado is None:
            st.error("❌ Não foi possível resolver o modelo MILP")
            return
        
        # ===== INFORMAÇÃO DE CARGAS DESLOCADAS =====
        horarios = solucao.get('Horarios_Cargas', {})
        if horarios:
            st.info(f"📋 {len(horarios)} carga(s) deslocada(s) com variáveis binárias")
            for nome, info in horarios.items():
                h_orig = f"{info['original_inicio']//60:02d}:{info['original_inicio']%60:02d}"
                h_otim = f"{info['otimizado_inicio']//60:02d}:{info['otimizado_inicio']%60:02d}"
                st.write(f"  - **{nome}** (P{info['prioridade']}): {h_orig} → {h_otim} ({info['potencia']:.1f} kW)")
        
        # ===== MÉTRICAS RESUMIDAS =====
        st.markdown("### 📊 Resumo de Operação")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        custo_total = custos.get('Total', 0)
        carga_total = df_resultado['Carga'].sum()
        
        with col1:
            st.metric("💰 Custo Total", f"R$ {custo_total:,.2f}")
        with col2:
            cobertura_local = ((carga_total - df_resultado['Concessionaria'].sum()) / carga_total * 100) if carga_total > 0 else 0
            st.metric("🏠 Cobertura Local", f"{cobertura_local:.1f}%")
        with col3:
            aproveitamento_solar = (df_resultado['Solar'].sum() / carga_total * 100) if carga_total > 0 else 0
            st.metric("☀️ Aproveit. Solar", f"{aproveitamento_solar:.1f}%")
        with col4:
            st.metric("📦 Demanda Total", f"{carga_total:,.2f} kWh")
        with col5:
            autossuficiencia = ((carga_total - df_resultado['Concessionaria'].sum()) / carga_total * 100) if carga_total > 0 else 0
            st.metric("⚡ Autossuficiência", f"{autossuficiencia:.1f}%")
        
        # ===== ABAS ORGANIZADAS =====
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Fluxo de Energia", "🔋 Armazenamento", "💵 Custos", "🎯 Resumo de Fontes", "📋 Detalhes"])
        
        # TAB 1: FLUXO DE ENERGIA
        with tab1:
            st.markdown("#### Despacho de Energia ao Longo do Dia (COM DESLIZAMENTO)")
            df_uso = pd.DataFrame({
                "Solar": df_resultado['Solar'],
                "Diesel": df_resultado['Diesel'],
                "Bateria": df_resultado['Bateria'],
                "Concessionária": df_resultado['Concessionaria'],
                "Carga (Demanda)": -np.abs(np.array(df_resultado['Carga']))
            })
            fig1 = Grafico_linha(df_uso, xlabel="Tempo (min)", ylabel="Potência (kW)", title="Positivo = Fornecimento | Negativo = Consumo")
            st.plotly_chart(fig1, use_container_width=True, key=f"analise5_milp_fluxo_{index}")
            
            st.markdown("**Legenda:**")
            st.write("- 📈 **Acima do zero**: Fontes gerando/fornecendo energia")
            st.write("- 📉 **Abaixo do zero**: Demanda de carga")
            st.write("- 💡 **Cargas com prioridade 2 foram deslocadas para minimizar custos**")
        
        # TAB 2: ARMAZENAMENTO
        with tab2:
            st.markdown("#### Evolução dos Níveis de Armazenamento")
            df_niveis = pd.DataFrame({
                "Bateria (kWh)": solucao['Nivel_Bateria'][:-1] if 'Nivel_Bateria' in solucao else np.zeros(len(df_resultado)),
                "Diesel (L)": solucao['Nivel_Diesel'][:-1] if 'Nivel_Diesel' in solucao else np.zeros(len(df_resultado))
            })
            fig2 = Grafico_linha(df_niveis, xlabel="Tempo (min)", ylabel="Energia/Volume", title="Dinâmica dos Sistemas de Armazenamento")
            st.plotly_chart(fig2, use_container_width=True, key=f"analise5_milp_armazenamento_{index}")
            
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                bateria_final = solucao['Nivel_Bateria'][-2] if 'Nivel_Bateria' in solucao and len(solucao['Nivel_Bateria']) > 1 else 0
                st.metric("🔋 Bateria Final", f"{bateria_final:.2f} kWh", f"{(bateria_final/microrrede.bateria.capacidade*100 if microrrede.bateria else 0):.1f}%")
            with col2:
                diesel_final = solucao['Nivel_Diesel'][-2] if 'Nivel_Diesel' in solucao and len(solucao['Nivel_Diesel']) > 1 else 0
                st.metric("⛽ Diesel Final", f"{diesel_final:.2f} L")
        
        # TAB 3: CUSTOS
        with tab3:
            st.markdown("#### Análise de Custos")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Custo Instantâneo**")
                df_custo_inst = pd.DataFrame({"Custo (R$)": solucao.get('Custo_Total_Instante', np.zeros(len(df_resultado)))})
                fig_inst = Grafico_linha(df_custo_inst, xlabel="Tempo (min)", ylabel="Custo (R$)", title="")
                st.plotly_chart(fig_inst, use_container_width=True, key=f"analise5_milp_custo_inst_{index}")
            
            with col2:
                st.markdown("**Custo Acumulado**")
                custo_acumulado = np.cumsum(solucao.get('Custo_Total_Instante', np.zeros(len(df_resultado))))
                df_custo_acu = pd.DataFrame({"Custo Acumulado (R$)": custo_acumulado})
                fig_acu = Grafico_linha(df_custo_acu, xlabel="Tempo (min)", ylabel="Custo Acumulado (R$)", title="")
                st.plotly_chart(fig_acu, use_container_width=True, key=f"analise5_milp_custo_acu_{index}")
            
            st.divider()
            st.markdown("**Custo por Fonte:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                custo_solar = custos.get('Solar', 0)
                st.metric("☀️ Solar", f"R$ {custo_solar:,.2f}")
                custo_diesel = custos.get('Diesel', 0)
                st.metric("🔥 Diesel", f"R$ {custo_diesel:,.2f}")
            with col2:
                custo_bateria = custos.get('Bateria', 0)
                st.metric("🔋 Bateria", f"R$ {custo_bateria:,.2f}")
            with col3:
                custo_rede = custos.get('Concessionaria', 0)
                st.metric("🏢 Concessionária", f"R$ {custo_rede:,.2f}")
        
        # TAB 4: RESUMO DE FONTES
        with tab4:
            st.markdown("#### Uso Total por Fonte")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Resumo Energético:**")
                total_df = pd.DataFrame({
                    "Fonte": ["☀️ Solar", "🔋 Bateria", "🔥 Diesel", "🏢 Concessionária"],
                    "Energia (kWh)": [
                        f"{df_resultado['Solar'].sum():,.2f}",
                        f"{df_resultado['Bateria'].sum():,.2f}",
                        f"{df_resultado['Diesel'].sum():,.2f}",
                        f"{df_resultado['Concessionaria'].sum():,.2f}"
                    ]
                })
                st.dataframe(total_df, use_container_width=True, hide_index=True)
            
            with col2:
                st.write("**Resumo de Custos:**")
                custo_df = pd.DataFrame({
                    "Fonte": ["☀️ Solar", "🔋 Bateria", "🔥 Diesel", "🏢 Concessionária"],
                    "Custo (R$)": [
                        f"R$ {custos.get('Solar', 0):,.2f}",
                        f"R$ {custos.get('Bateria', 0):,.2f}",
                        f"R$ {custos.get('Diesel', 0):,.2f}",
                        f"R$ {custos.get('Concessionaria', 0):,.2f}"
                    ]
                })
                st.dataframe(custo_df, use_container_width=True, hide_index=True)
        
        # TAB 5: DETALHES
        with tab5:
            st.markdown("#### Dados Horários Detalhados")
            
            df_completo = pd.DataFrame({
                "Tempo (min)": range(len(df_resultado)),
                "Demanda (kW)": df_resultado['Carga'],
                "Solar (kW)": df_resultado['Solar'],
                "Diesel (kW)": df_resultado['Diesel'],
                "Bateria (kW)": df_resultado['Bateria'],
                "Concessionária (kW)": df_resultado['Concessionaria'],
                "Nível Bateria (kWh)": solucao['Nivel_Bateria'][:-1] if 'Nivel_Bateria' in solucao else np.zeros(len(df_resultado)),
                "Nível Diesel (L)": solucao['Nivel_Diesel'][:-1] if 'Nivel_Diesel' in solucao else np.zeros(len(df_resultado)),
                "Custo Instantâneo (R$)": solucao.get('Custo_Total_Instante', np.zeros(len(df_resultado)))
            })
            
            st.dataframe(df_completo.style.format("{:.4f}"), use_container_width=True)
            
            st.download_button(
                label="📥 Baixar dados em CSV",
                data=df_completo.to_csv(index=False),
                file_name=f"analise5_{microrrede}.csv",
                mime="text/csv"
            )



def analise_5_milp_multi(microrredes: list):
    """
    Análise 5 MILP para múltiplas microrredes
    
    Args:
        microrredes: Lista de objetos Microrrede
    """
    st.subheader("Análise 5: Otimização MILP - Múltiplas Microrredes")
    
    # Processar cada microrrede
    resultados_globais = {}
    
    for microrrede in microrredes:
        st.write(f"### 🔧 Processando: {microrrede}")
        
        with st.spinner(f"Otimizando {microrrede}..."):
            df_resultado, custos, solucao = analise_milp_func(microrrede)
        
        if df_resultado is not None:
            resultados_globais[str(microrrede)] = {
                'dataframe': df_resultado,
                'custos': custos,
                'solucao': solucao
            }
            
            st.success(f"✓ {microrrede} otimizada com custo total: R$ {custos.get('Total', 0):,.2f}")
        else:
            st.error(f"✗ Erro ao otimizar {microrrede}")
    
    # Resumo comparativo
    if resultados_globais:
        st.subheader("📊 Resumo Comparativo")
        
        dados_comparacao = []
        for nome_rede, resultado in resultados_globais.items():
            custos = resultado['custos']
            df = resultado['dataframe']
            dados_comparacao.append({
                'Microrrede': nome_rede,
                'Custo Total (R$)': custos.get('Total', 0),
                'Carga Total (kWh)': df['Carga'].sum(),
                'Autossuficiência': ((df['Carga'].sum() - df['Concessionaria'].sum()) / df['Carga'].sum() * 100),
            })
        
        df_comparacao = pd.DataFrame(dados_comparacao)
        st.dataframe(df_comparacao.style.format({
            'Custo Total (R$)': '{:,.2f}',
            'Carga Total (kWh)': '{:,.2f}',
            'Autossuficiência': '{:.1f}%'
        }), use_container_width=True)


def analise_6_pso(microrrede: Microrrede):
    """
    Análise 6 - PSO (Particle Swarm Optimization)
    Otimiza o controle da microrrede usando algoritmo de enxame de partículas
    
    Características:
    - Minimiza custo total operacional
    - Metaheurística baseada em comportamento social
    - Menor tempo computacional que MILP
    - Múltiplas iterações para convergência
    """
    st.subheader("Análise 6: Otimização PSO (Particle Swarm Optimization)")
    st.write("""
    Esta análise utiliza **PSO (Particle Swarm Optimization)** para otimizar 
    o controle da microrrede. Este algoritmo metaheurístico:
    - Simula o comportamento de um enxame de partículas
    - Busca a solução ótima através de exploração e exploração
    - Mais rápido que MILP mantendo boa qualidade de solução
    - Ideal para problemas com estrutura não-linear
    """)
    
    # Parâmetros do PSO com keys únicas baseadas no ID da microrrede
    col1, col2, col3 = st.columns(3)
    with col1:
        iteracoes = st.slider("Iterações PSO", 20, 200, 50, step=10, key=f"pso_iter_{microrrede.id}")
    with col2:
        tamanho_enxame = st.slider("Tamanho do Enxame", 10, 100, 30, step=5, key=f"pso_enxame_{microrrede.id}")
    with col3:
        velocidade = st.slider("Coeficiente de Inércia (w)", 0.1, 1.0, 0.7, step=0.1, key=f"pso_vel_{microrrede.id}")
    
    with st.spinner("Otimizando microrrede com PSO..."):
        try:
            # Executar otimização PSO
            df_resultado, custos, solucao = analise_pso_func(
                microrrede, 
                iteracoes=iteracoes,
                tamanho_enxame=tamanho_enxame
            )
            
            if df_resultado is None:
                st.error("❌ Não foi possível resolver o modelo PSO")
                return
            
            # ===== RESUMO DE CUSTOS =====
            st.subheader("💰 Resumo de Custos")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Solar", f"R$ {custos.get('Solar', 0):,.2f}")
            with col2:
                st.metric("Bateria", f"R$ {custos.get('Bateria', 0):,.2f}")
            with col3:
                st.metric("Diesel", f"R$ {custos.get('Diesel', 0):,.2f}")
            with col4:
                st.metric("Biogas", f"R$ {custos.get('Biogas', 0):,.2f}")
            
            col5, col6 = st.columns(2)
            
            with col5:
                st.metric("Concessionária", f"R$ {custos.get('Concessionaria', 0):,.2f}")
            with col6:
                st.metric("**CUSTO TOTAL PSO**", f"R$ {custos.get('Total', 0):,.2f}", 
                         delta=None, delta_color="inverse")
            
            # ===== CONVERGÊNCIA DO PSO =====
            if 'Convergencia' in solucao and solucao['Convergencia']:
                st.subheader("📉 Convergência do Algoritmo")
                df_convergencia = pd.DataFrame({
                    'Iteração': range(len(solucao['Convergencia'])),
                    'Melhor Custo (R$)': solucao['Convergencia']
                })
                st.line_chart(df_convergencia.set_index('Iteração'), height=300)
                st.caption("Evolução do melhor custo encontrado a cada iteração")
            
            # ===== USO DE ENERGIA POR FONTE =====
            st.subheader("⚡ Despacho de Energia")
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de barras com uso por fonte
                totais_uso = {
                    'Solar': df_resultado['Solar'].sum(),
                    'Bateria': df_resultado['Bateria'].sum(),
                    'Diesel': df_resultado['Diesel'].sum(),
                    'Biogas': df_resultado['Biogas'].sum(),
                    'Concessionária': df_resultado['Concessionaria'].sum(),
                }
                df_totais = pd.DataFrame({
                    'Fonte': list(totais_uso.keys()),
                    'Energia (kWh)': list(totais_uso.values())
                })
                st.bar_chart(df_totais.set_index('Fonte'), width=400, height=300)
            
            with col2:
                # Tabela de resumo
                st.write("**Resumo de Uso por Fonte:**")
                df_resumo = pd.DataFrame({
                    'Fonte': ['Solar', 'Bateria', 'Diesel', 'Biogas', 'Concessionária', 'Venda'],
                    'Energia (kWh)': [
                        f"{df_resultado['Solar'].sum():.2f}",
                        f"{df_resultado['Bateria'].sum():.2f}",
                        f"{df_resultado['Diesel'].sum():.2f}",
                        f"{df_resultado['Biogas'].sum():.2f}",
                        f"{df_resultado['Concessionaria'].sum():.2f}",
                        f"{df_resultado['Venda'].sum():.2f}",
                    ]
                })
                st.dataframe(df_resumo, hide_index=True)
            
            # ===== SÉRIES TEMPORAIS =====
            st.subheader("📈 Evolução Temporal")
            
            tab1, tab2, tab3 = st.tabs(["Despacho em Tempo Real", "Níveis de Armazenamento", "Comparação de Fontes"])
            
            with tab1:
                df_uso = pd.DataFrame({
                    'Solar': df_resultado['Solar'],
                    'Bateria': df_resultado['Bateria'],
                    'Diesel': df_resultado['Diesel'],
                    'Biogas': df_resultado['Biogas'],
                    'Concessionária': df_resultado['Concessionaria'],
                    'Carga': df_resultado['Carga']
                })
                st.line_chart(df_uso, width=None, height=400)
                st.caption("Despacho de energia de cada fonte ao longo do dia")
            
            with tab2:
                df_niveis = pd.DataFrame({
                    'Bateria (kWh)': solucao['Nivel_Bateria'][:-1] if 'Nivel_Bateria' in solucao else [],
                    'Diesel (L)': solucao['Nivel_Diesel'][:-1] if 'Nivel_Diesel' in solucao else [],
                    'Biogas (m³)': solucao['Nivel_Biogas'][:-1] if 'Nivel_Biogas' in solucao else []
                })
                if not df_niveis.empty:
                    st.line_chart(df_niveis, width=None, height=400)
                    st.caption("Evolução dos níveis de armazenamento")
            
            with tab3:
                # Comparação de fontes de energia
                df_comparacao_fontes = pd.DataFrame({
                    'Tempo (min)': range(len(df_resultado)),
                    'Demanda': df_resultado['Carga'],
                    'Geração Local': df_resultado['Solar'] + df_resultado['Bateria'] + df_resultado['Diesel'] + df_resultado['Biogas']
                })
                st.line_chart(df_comparacao_fontes.set_index('Tempo (min)'), height=400)
                st.caption("Comparação entre demanda e capacidade de geração local")
            
            # ===== ESTATÍSTICAS =====
            st.subheader("📋 Estatísticas e Indicadores")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                carga_total = df_resultado['Carga'].sum()
                st.metric("Demanda Total", f"{carga_total:.2f} kWh")
            
            with col2:
                # Taxa de cobertura local (não da rede)
                cobertura_local = ((carga_total - df_resultado['Concessionaria'].sum()) / carga_total * 100) if carga_total > 0 else 0
                st.metric("Cobertura Local", f"{cobertura_local:.1f}%")
            
            with col3:
                # Aproveitamento solar
                total_solar = df_resultado['Solar'].sum() + df_resultado['Venda'].sum()
                aproveitamento = (df_resultado['Solar'].sum() / total_solar * 100) if total_solar > 0 else 0
                st.metric("Aproveit. Solar", f"{aproveitamento:.1f}%")
            
            with col4:
                # Taxa de autossuficiência energética
                energia_propria = carga_total - df_resultado['Concessionaria'].sum()
                autossuficiencia = (energia_propria / carga_total * 100) if carga_total > 0 else 0
                st.metric("Autossuficiência", f"{autossuficiencia:.1f}%")
            
            # ===== DADOS DETALHADOS =====
            st.subheader("📑 Dados Detalhados")
            st.dataframe(df_resultado.style.format("{:.4f}"), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erro durante otimização PSO: {str(e)}")
            import traceback
            st.error(traceback.format_exc())


def analise_6_pso_multi(microrredes: list):
    """
    Análise 6 PSO para múltiplas microrredes
    
    Args:
        microrredes: Lista de objetos Microrrede
    """
    st.subheader("Análise 6: Otimização PSO - Múltiplas Microrredes")
    
    # Parâmetros globais
    col1, col2 = st.columns(2)
    with col1:
        iteracoes = st.slider("Iterações PSO", 20, 100, 50, step=10, key="pso_multi_iter")
    with col2:
        tamanho_enxame = st.slider("Tamanho do Enxame", 10, 50, 20, step=5, key="pso_multi_enxame")
    
    # Processar cada microrrede
    resultados_globais = {}
    
    for microrrede in microrredes:
        st.write(f"### 🔧 Processando: {microrrede}")
        
        with st.spinner(f"Otimizando {microrrede} com PSO..."):
            try:
                df_resultado, custos, solucao = analise_pso_func(
                    microrrede, 
                    iteracoes=iteracoes,
                    tamanho_enxame=tamanho_enxame
                )
                
                if df_resultado is not None:
                    resultados_globais[str(microrrede)] = {
                        'dataframe': df_resultado,
                        'custos': custos,
                        'solucao': solucao
                    }
                    
                    st.success(f"✓ {microrrede} otimizada com custo: R$ {custos.get('Total', 0):,.2f}")
                else:
                    st.error(f"✗ Erro ao otimizar {microrrede}")
            except Exception as e:
                st.error(f"✗ Erro ao otimizar {microrrede}: {str(e)}")
    
    # Resumo comparativo
    if resultados_globais:
        st.subheader("📊 Resumo Comparativo PSO")
        
        dados_comparacao = []
        for nome_rede, resultado in resultados_globais.items():
            custos = resultado['custos']
            df = resultado['dataframe']
            carga = df['Carga'].sum()
            dados_comparacao.append({
                'Microrrede': nome_rede,
                'Custo Total (R$)': custos.get('Total', 0),
                'Carga Total (kWh)': carga,
                'Custo/kWh': (custos.get('Total', 0) / carga) if carga > 0 else 0,
                'Autossuficiência': ((carga - df['Concessionaria'].sum()) / carga * 100) if carga > 0 else 0,
            })
        
        df_comparacao = pd.DataFrame(dados_comparacao)
        st.dataframe(df_comparacao.style.format({
            'Custo Total (R$)': '{:,.2f}',
            'Carga Total (kWh)': '{:,.2f}',
            'Custo/kWh': '{:.2f}',
            'Autossuficiência': '{:.1f}%'
        }), use_container_width=True)
        
        # Gráfico comparativo
        st.write("**Comparação de Custos**")
        st.bar_chart(df_comparacao.set_index('Microrrede')['Custo Total (R$)'], 
                     color='#1f77b4')


