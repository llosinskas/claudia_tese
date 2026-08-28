"""
MILP (Mixed Integer Linear Programming) para controle otimizado de microrredes
Objetivo: Minimizar o custo operacional respeitando restrições de energia,
capacidade das fontes e prioridades de carga.
"""

import numpy as np
import pandas as pd
from pulp import *
import json
from typing import Dict
from models.Microrrede import Microrrede
from Tools.GerarCurvaCarga import CurvaCarga
from Tools.distancia import distancia_haversine


class MILPMicrorredes:
    """
    Classe para otimização de microrredes usando MILP
    """
    
    def __init__(self, microrrede: Microrrede, periodos: int = 1440):
        """
        Inicializa o modelo MILP
        
        Args:
            microrrede: Objeto da microrrede
            periodos: Número de períodos de tempo (minutos no dia = 1440)
        """
        self.microrrede = microrrede
        self.periodos = periodos
        self.modelo = None
        self.solucao = None
        
        # Dados da microrrede
        
        self.carga = microrrede.carga 
        self.bateria = microrrede.bateria if microrrede.bateria is not None else None 
        self.diesel = microrrede.diesel if microrrede.diesel is not None else None
        #self.biogas = microrrede.biogas if microrrede.biogas is not None else None
        self.solar = microrrede.solar if microrrede.solar is not None else None
        self.concessionaria = microrrede.concessionaria if microrrede.concessionaria is not None else None
        
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
    
    def criar_modelo(self, verbose: bool = True) -> None:
        """
        Cria o modelo MILP
        
        Args:
            verbose: Se True, exibe informações do modelo
        """
        self.modelo = LpProblem("Controle_Microrrede", LpMinimize)
        
        # ===== VARIÁVEIS DE DECISÃO =====
        # Energia fornecida por cada fonte em cada período (kW)
        self.uso_solar = [LpVariable(f"P_solar_{t}", lowBound=0) for t in range(self.periodos)] 
        self.uso_bateria = [LpVariable(f"P_bateria_{t}", lowBound=0) for t in range(self.periodos)]
        self.uso_diesel = [LpVariable(f"P_diesel_{t}", lowBound=0) for t in range(self.periodos)]
        #self.uso_biogas = [LpVariable(f"P_biogas_{t}", lowBound=0) for t in range(self.periodos)]
        self.uso_concessionaria = [LpVariable(f"P_conc_{t}", lowBound=0) for t in range(self.periodos)]
        
        # Estado de funcionamento (binário: 1 = ligado, 0 = desligado)
        self.diesel_ligado = [LpVariable(f"U_diesel_{t}", cat='Binary') for t in range(self.periodos)]
        #self.biogas_ligado = [LpVariable(f"U_biogas_{t}", cat='Binary') for t in range(self.periodos)]
        
        # Nível de armazenamento (kWh)
        self.nivel_bateria = [LpVariable(f"E_bateria_{t}", lowBound=0) for t in range(self.periodos + 1)]
        self.nivel_diesel = [LpVariable(f"E_diesel_{t}", lowBound=0) for t in range(self.periodos + 1)]
        #self.nivel_biogas = [LpVariable(f"E_biogas_{t}", lowBound=0) for t in range(self.periodos + 1)]
        
        # Energia de carga da bateria
        self.carga_bateria = [LpVariable(f"P_carga_bat_{t}", lowBound=0) for t in range(self.periodos)]
        
        # Venda para a rede (excesso)
        self.venda_rede = [LpVariable(f"P_venda_{t}", lowBound=0) for t in range(self.periodos)]
        
        # Corte de solar (energia solar desperdiçada quando bateria cheia)
        self.curtail_solar = [LpVariable(f"P_curtail_{t}", lowBound=0) for t in range(self.periodos)]
        
        # Variáveis para penalizar mudanças rápidas na bateria (suavização)
        # Delta de descarga e carga para cada transição de tempo
        self.delta_desc = [LpVariable(f"Delta_desc_{t}", lowBound=0) for t in range(self.periodos)]
        self.delta_carga = [LpVariable(f"Delta_carga_{t}", lowBound=0) for t in range(self.periodos)]
        
        # Binária para controlar modo da bateria: 1=descargando, 0=carregando/inativo
        self.bat_descarga = [LpVariable(f"U_bat_desc_{t}", cat='Binary') for t in range(self.periodos)]
        
        if verbose:
            print("Variáveis de decisão criadas")
    
    def adicionar_restricoes(self, verbose: bool = True) -> None:
        """
        Adiciona restrições ao modelo MILP
        
        Args:
            verbose: Se True, exibe informações das restrições
        """
        if self.modelo is None:
            raise ValueError("Modelo não foi criado. Execute criar_modelo() primeiro.")
        
        # ===== RESTRIÇÕES =====
        
        # 1. BALANÇO DE ENERGIA: Oferta = Demanda + Venda (para cada período)
        for t in range(self.periodos):
            self.modelo += (self.uso_solar[t] + self.uso_bateria[t] + 
        #                   self.uso_diesel[t] + self.uso_biogas[t] + 
                            self.uso_diesel[t] +
                           self.uso_concessionaria[t] == 
                           self.curva_carga[t] + self.carga_bateria[t] + self.venda_rede[t]), f"Balanço_energia_{t}"
        
        # 2. LIMITES DE POTÊNCIA
        # Solar: toda geração deve ser usada ou cortada (incentiva recarga)
        if self.solar is not None:
            for t in range(self.periodos):
                self.modelo += self.uso_solar[t] + self.curtail_solar[t] == self.curva_solar[t], f"Solar_total_{t}"
        
        if self.diesel is not None:
            for t in range(self.periodos):
                self.modelo += self.uso_diesel[t] <= self.diesel.potencia * self.diesel_ligado[t], f"Limite_diesel_{t}"
                # Custo mínimo (se ligado, deve ter potência mínima)
                self.modelo += self.uso_diesel[t] >= 0.2 * self.diesel.potencia * self.diesel_ligado[t], f"Min_diesel_{t}"
        
        # if self.biogas is not None:
        #     for t in range(self.periodos):
        #         self.modelo += self.uso_biogas[t] <= self.biogas.potencia * self.biogas_ligado[t], f"Limite_biogas_{t}"
        #         self.modelo += self.uso_biogas[t] >= 0.2 * self.biogas.potencia * self.biogas_ligado[t], f"Min_biogas_{t}"
        
        if self.bateria is not None:
            for t in range(self.periodos):
                # Limites de potência de descarga e recarga
                self.modelo += self.uso_bateria[t] <= self.bateria.potencia, f"Limite_descarga_bat_{t}"
                self.modelo += self.carga_bateria[t] <= self.bateria.potencia, f"Limite_carga_bat_{t}"
                
                # Exclusão mútua: não pode descarregar e carregar simultaneamente
                self.modelo += self.uso_bateria[t] <= self.bateria.potencia * self.bat_descarga[t], f"Excl_desc_{t}"
                self.modelo += self.carga_bateria[t] <= self.bateria.potencia * (1 - self.bat_descarga[t]), f"Excl_carga_{t}"
        
        # 3. DINÂMICA DE ARMAZENAMENTO
        # 3.1 Bateria
        if self.bateria is not None:
            # Estado inicial
            self.modelo += self.nivel_bateria[0] == self.bateria.capacidade, "Bateria_inicial"
            
            for t in range(self.periodos):
                # Dinâmica: E(t+1) = E(t) - P_descarga + η * P_carga
                eficiencia = self.bateria.eficiencia / 100
                self.modelo += (self.nivel_bateria[t + 1] == 
                               self.nivel_bateria[t] - self.uso_bateria[t] / 60 + 
                               eficiencia * self.carga_bateria[t] / 60), f"Bateria_dinamica_{t}"
                
                # Limites de capacidade
                self.modelo += self.nivel_bateria[t] >= self.bateria.capacidade_min, f"Bat_min_{t}"
                self.modelo += self.nivel_bateria[t] <= self.bateria.capacidade, f"Bat_max_{t}"
                
                # Penalidade para mudanças rápidas (suavização)
                if t > 0:
                    # Capturar magnitude da mudança na descarga
                    self.modelo += self.delta_desc[t] >= self.uso_bateria[t] - self.uso_bateria[t - 1], f"Delta_desc_up_{t}"
                    self.modelo += self.delta_desc[t] >= self.uso_bateria[t - 1] - self.uso_bateria[t], f"Delta_desc_down_{t}"
                    
                    # Capturar magnitude da mudança na carga
                    self.modelo += self.delta_carga[t] >= self.carga_bateria[t] - self.carga_bateria[t - 1], f"Delta_carga_up_{t}"
                    self.modelo += self.delta_carga[t] >= self.carga_bateria[t - 1] - self.carga_bateria[t], f"Delta_carga_down_{t}"
        
        # 3.2 Diesel
        if self.diesel is not None:
            self.modelo += self.nivel_diesel[0] == self.diesel.tanque, "Diesel_inicial"
            
            # Consumo de combustível (litros/kWh)
            consumo_especifico = 0.2  # litros/kWh teórico (ajustar conforme seus dados)
            
            for t in range(self.periodos):
                self.modelo += (self.nivel_diesel[t + 1] == 
                               self.nivel_diesel[t] - consumo_especifico * self.uso_diesel[t] / 60), f"Diesel_dinamica_{t}"
                
                self.modelo += self.nivel_diesel[t] >= 0, f"Diesel_min_{t}"
                self.modelo += self.nivel_diesel[t] <= self.diesel.tanque, f"Diesel_max_{t}"
        
        # 3.3 Biogas
        # if self.biogas is not None:
        #     self.modelo += self.nivel_biogas[0] == self.biogas.tanque, "Biogas_inicial"
            
        #     # Produção de biogas (considere a geração)
        #     producao_biogas = 0.1  # m³/h (ajustar conforme seus dados)
        #            consumo_especifico = 0.15  # m³/kWh
            
        #    for t in range(self.periodos):
        #        self.modelo += (self.nivel_biogas[t + 1] == 
        #                       self.nivel_biogas[t] + producao_biogas / 60 - 
        #                       consumo_especifico * self.uso_biogas[t] / 60), f"Biogas_dinamica_{t}"
        #        
        #        self.modelo += self.nivel_biogas[t] >= 0, f"Biogas_min_{t}"
        #        self.modelo += self.nivel_biogas[t] <= self.biogas.tanque, f"Biogas_max_{t}"
        
        if verbose:
            print("Restrições adicionadas")
    
    def adicionar_funcao_objetivo(self, verbose: bool = True) -> None:
        """
        Adiciona a função objetivo (minimizar custo)
        
        Args:
            verbose: Se True, exibe informações da função objetivo
        """
        if self.modelo is None:
            raise ValueError("Modelo não foi criado. Execute criar_modelo() primeiro.")
        
        custo_total = 0
        
        # Custo de combustível diesel
        if self.diesel is not None:
            for t in range(self.periodos):
                custo_total += self.diesel.custo_por_kWh * self.uso_diesel[t] / 60
                # Custo de inicialização (se liga)
                if t > 0:
                    custo_total += 5 * (self.diesel_ligado[t] - self.diesel_ligado[t - 1])
        
        # Custo de biogas
        # if self.biogas is not None:
        #     for t in range(self.periodos):
        #         custo_total += self.biogas.custo_por_kWh * self.uso_biogas[t] / 60
        
        # Custo de bateria
        if self.bateria is not None:
            for t in range(self.periodos):
                custo_total += self.bateria.custo_kwh * self.uso_bateria[t] / 60
        
        # Custo de concessionária
        if self.concessionaria is not None:
            for t in range(self.periodos):
                custo_total += self.concessionaria.tarifa * self.uso_concessionaria[t] / 60
        
        # Receita de venda para a rede (desconto)
        if self.concessionaria is not None:
            for t in range(self.periodos):
                custo_total -= self.concessionaria.tarifa * self.venda_rede[t] / 60 * 0.8  # 80% do valor
        
        # Custo de solar (negligenciável, mas pode adicionar manutenção)
        if self.solar is not None:
            custo_total += 0.01 * lpSum(self.uso_solar)
        
        # Penalidade por mudanças rápidas na bateria (suaviza o comportamento)
        if self.bateria is not None:
            # Penalizar transições rápidas (0.01 R$/kW - leve, não impede uso)
            custo_total += 0.01 * lpSum(self.delta_desc[t] / 60 for t in range(1, self.periodos))
            custo_total += 0.01 * lpSum(self.delta_carga[t] / 60 for t in range(1, self.periodos))
        
        # Penalidade por desperdiçar solar (força recarga da bateria)
        if self.solar is not None:
            custo_total += 10 * lpSum(self.curtail_solar[t] / 60 for t in range(self.periodos))
        
        self.modelo += custo_total, "Custo_Total"
        
        if verbose:
            print("Função objetivo adicionada")
    
    def resolver(self, verbose: bool = True) -> bool:
        """
        Resolve o modelo MILP
        
        Args:
            verbose: Se True, exibe informações da resolução
        
        Returns:
            True se resolveu com sucesso, False caso contrário
        """
        if self.modelo is None:
            self.criar_modelo(verbose=False)
            self.adicionar_restricoes(verbose=False)
            self.adicionar_funcao_objetivo(verbose=False)
        
        # Resolver o modelo
        try:
            # Usar solver padrão (CBC) com limite de tempo e tolerância
            self.modelo.solve(PULP_CBC_CMD(msg=0, timeLimit=180, gapRel=0.005))
            
            if self.modelo.status == 1:  # Optimal
                if verbose:
                    print(f"Modelo resolvido com sucesso!")
                    print(f"  Status: Ótimo")
                    print(f"  Custo total: R$ {value(self.modelo.objective):,.2f}")
                return True
            elif self.modelo.status == 0 and value(self.modelo.objective) is not None:
                # Solução viável encontrada (timeLimit atingido mas tem solução)
                if verbose:
                    print(f"Solução viável encontrada (limite de tempo atingido)")
                    print(f"  Custo total: R$ {value(self.modelo.objective):,.2f}")
                self.modelo.status = 1  # Aceitar como válida
                return True
            else:
                if verbose:
                    print(f"✗ Modelo não encontrou solução ótima. Status: {self.modelo.status}")
                return False
        except Exception as e:
            if verbose:
                print(f"✗ Erro ao resolver o modelo: {str(e)}")
            return False
    
    def extrair_solucao(self) -> Dict:
        """
        Extrai a solução do modelo
        
        Returns:
            Dicionário com os resultados
        """
        if self.modelo is None or self.modelo.status != 1:
            raise ValueError("Modelo não foi resolvido ou não encontrou solução ótima")
        
        solucao = {
            'Solar': np.array([value(self.uso_solar[t]) or 0 for t in range(self.periodos)]),
            'Bateria': np.array([value(self.uso_bateria[t]) or 0 for t in range(self.periodos)]),
            'Diesel': np.array([value(self.uso_diesel[t]) or 0 for t in range(self.periodos)]),
       #     'Biogas': np.array([value(self.uso_biogas[t]) or 0 for t in range(self.periodos)]),
            'Concessionaria': np.array([value(self.uso_concessionaria[t]) or 0 for t in range(self.periodos)]),
            'Venda': np.array([value(self.venda_rede[t]) or 0 for t in range(self.periodos)]),
            'Nivel_Bateria': np.array([value(self.nivel_bateria[t]) or 0 for t in range(self.periodos + 1)]),
            'Nivel_Diesel': np.array([value(self.nivel_diesel[t]) or 0 for t in range(self.periodos + 1)]),
          #  'Nivel_Biogas': np.array([value(self.nivel_biogas[t]) or 0 for t in range(self.periodos + 1)]),
            'Carga_Bateria': np.array([value(self.carga_bateria[t]) or 0 for t in range(self.periodos)]),
            'Custo_Total': value(self.modelo.objective),
            'Status': LpStatus[self.modelo.status]
        }
        
        self.solucao = solucao
        return solucao
    
    def gerar_dataframe_resultado(self) -> pd.DataFrame:
        """
        Gera um DataFrame com os resultados da otimização
        
        Returns:
            DataFrame com uso de energia por fonte
        """
        if self.solucao is None:
            self.resolver(verbose=False)
            self.extrair_solucao()
        
        df = pd.DataFrame({
            'Carga': self.curva_carga,
            'Solar': self.solucao['Solar'],
            'Bateria': self.solucao['Bateria'],
            'Diesel': self.solucao['Diesel'],
           # 'Biogas': self.solucao['Biogas'],
            'Concessionaria': self.solucao['Concessionaria'],
            'Venda': self.solucao['Venda'],
            'Carga_Bateria': self.solucao['Carga_Bateria']
        })
        
        return df
    
    def calcular_custos_totais(self) -> Dict:
        """
        Calcula os custos totais por fonte
        
        Returns:
            Dicionário com custos totalizados
        """
        if self.solucao is None:
            self.resolver(verbose=False)
            self.extrair_solucao()
        
        custos = {}
        
        if self.solar is not None:
            custos['Solar'] = (self.solucao['Solar'].sum() / 60) * 0.01  # Manutenção
        
        if self.bateria is not None:
            custos['Bateria'] = (self.solucao['Bateria'].sum() / 60) * self.bateria.custo_kwh
        
        if self.diesel is not None:
            custos['Diesel'] = (self.solucao['Diesel'].sum() / 60) * self.diesel.custo_por_kWh
        
       # if self.biogas is not None:
        #    custos['Biogas'] = (self.solucao['Biogas'].sum() / 60) * self.biogas.custo_por_kWh
        
        if self.concessionaria is not None:
            custos['Concessionaria'] = (self.solucao['Concessionaria'].sum() / 60) * self.concessionaria.tarifa
            custos['Receita_Venda'] = -(self.solucao['Venda'].sum() / 60) * self.concessionaria.tarifa * 0.8
        
        custos['Total'] = sum(custos.values())
        
        return custos


class MILPMicrorredes_SemVenda(MILPMicrorredes):
    """
    Classe MILP para otimização SEM venda de energia para a rede.
    Herda de MILPMicrorredes e sobrescreve métodos para remover venda.
    """
    
    def criar_modelo(self, verbose: bool = True) -> None:
        """
        Cria o modelo MILP sem variável de venda
        """
        super().criar_modelo(verbose=False)
        
        # Remover variável de venda (deixar vazia)
        self.venda_rede = [LpVariable(f"P_venda_{t}", lowBound=0, upBound=0) for t in range(self.periodos)]
        
        if verbose:
            print("Variáveis de decisão criadas (SEM VENDA)")
    
    def adicionar_restricoes(self, verbose: bool = True) -> None:
        """
        Adiciona restrições ao modelo sem permitir venda
        """
        if self.modelo is None:
            raise ValueError("Modelo não foi criado. Execute criar_modelo() primeiro.")
        
        # 1. BALANÇO DE ENERGIA: Oferta = Demanda (SEM VENDA)
        for t in range(self.periodos):
            self.modelo += (self.uso_solar[t] + self.uso_bateria[t] + 
            #               self.uso_diesel[t] + self.uso_biogas[t] + 
                            self.uso_diesel[t]+
                           self.uso_concessionaria[t] == 
                           self.curva_carga[t] + self.carga_bateria[t]), f"Balanço_energia_{t}"
        
        # 2. LIMITES DE POTÊNCIA (idêntico ao original)
        # Solar: toda geração deve ser usada ou cortada (incentiva recarga)
        if self.solar is not None:
            for t in range(self.periodos):
                self.modelo += self.uso_solar[t] + self.curtail_solar[t] == self.curva_solar[t], f"Solar_total_{t}"
        
        if self.diesel is not None:
            for t in range(self.periodos):
                self.modelo += self.uso_diesel[t] <= self.diesel.potencia * self.diesel_ligado[t], f"Limite_diesel_{t}"
                self.modelo += self.uso_diesel[t] >= 0.2 * self.diesel.potencia * self.diesel_ligado[t], f"Min_diesel_{t}"
        
     #   if self.biogas is not None:
      #      for t in range(self.periodos):
       #         self.modelo += self.uso_biogas[t] <= self.biogas.potencia * self.biogas_ligado[t], f"Limite_biogas_{t}"
       #         self.modelo += self.uso_biogas[t] >= 0.2 * self.biogas.potencia * self.biogas_ligado[t], f"Min_biogas_{t}"
        
        if self.bateria is not None:
            for t in range(self.periodos):
                # Limites de potência de descarga e recarga
                self.modelo += self.uso_bateria[t] <= self.bateria.potencia, f"Limite_descarga_bat_{t}"
                self.modelo += self.carga_bateria[t] <= self.bateria.potencia, f"Limite_carga_bat_{t}"
                
                # Exclusão mútua: não pode descarregar e carregar simultaneamente
                self.modelo += self.uso_bateria[t] <= self.bateria.potencia * self.bat_descarga[t], f"Excl_desc_{t}"
                self.modelo += self.carga_bateria[t] <= self.bateria.potencia * (1 - self.bat_descarga[t]), f"Excl_carga_{t}"
        
        # 3. DINÂMICA DE ARMAZENAMENTO (idêntico ao original)
        # 3.1 Bateria
        if self.bateria is not None:
            self.modelo += self.nivel_bateria[0] == self.bateria.capacidade, "Bateria_inicial"
            
            for t in range(self.periodos):
                eficiencia = self.bateria.eficiencia / 100
                self.modelo += (self.nivel_bateria[t + 1] == 
                               self.nivel_bateria[t] - self.uso_bateria[t] / 60 + 
                               eficiencia * self.carga_bateria[t] / 60), f"Bateria_dinamica_{t}"
                
                self.modelo += self.nivel_bateria[t] >= self.bateria.capacidade_min, f"Bat_min_{t}"
                self.modelo += self.nivel_bateria[t] <= self.bateria.capacidade, f"Bat_max_{t}"
                
                # Penalidade para mudanças rápidas (suavização)
                if t > 0:
                    # Capturar magnitude da mudança na descarga
                    self.modelo += self.delta_desc[t] >= self.uso_bateria[t] - self.uso_bateria[t - 1], f"Delta_desc_up_{t}"
                    self.modelo += self.delta_desc[t] >= self.uso_bateria[t - 1] - self.uso_bateria[t], f"Delta_desc_down_{t}"
                    
                    # Capturar magnitude da mudança na carga
                    self.modelo += self.delta_carga[t] >= self.carga_bateria[t] - self.carga_bateria[t - 1], f"Delta_carga_up_{t}"
                    self.modelo += self.delta_carga[t] >= self.carga_bateria[t - 1] - self.carga_bateria[t], f"Delta_carga_down_{t}"
        
        # 3.2 Diesel
        if self.diesel is not None:
            self.modelo += self.nivel_diesel[0] == self.diesel.tanque, "Diesel_inicial"
            
            consumo_especifico = 0.2
            
            for t in range(self.periodos):
                self.modelo += (self.nivel_diesel[t + 1] == 
                               self.nivel_diesel[t] - consumo_especifico * self.uso_diesel[t] / 60), f"Diesel_dinamica_{t}"
                
                self.modelo += self.nivel_diesel[t] >= 0, f"Diesel_min_{t}"
                self.modelo += self.nivel_diesel[t] <= self.diesel.tanque, f"Diesel_max_{t}"
        
        # 3.3 Biogas
       # if self.biogas is not None:
        #    self.modelo += self.nivel_biogas[0] == self.biogas.tanque, "Biogas_inicial"
         #   
          #  producao_biogas = 0.1
          #  consumo_especifico = 0.15
            
          #  for t in range(self.periodos):
           #     self.modelo += (self.nivel_biogas[t + 1] == 
           #                    self.nivel_biogas[t] + producao_biogas / 60 - 
           #                    consumo_especifico * self.uso_biogas[t] / 60), f"Biogas_dinamica_{t}"
                
            #    self.modelo += self.nivel_biogas[t] >= 0, f"Biogas_min_{t}"
             #   self.modelo += self.nivel_biogas[t] <= self.biogas.tanque, f"Biogas_max_{t}"
        
        if verbose:
            print("Restrições adicionadas (SEM VENDA)")
    
    def adicionar_funcao_objetivo(self, verbose: bool = True) -> None:
        """
        Adiciona função objetivo SEM receita de venda
        """
        if self.modelo is None:
            raise ValueError("Modelo não foi criado. Execute criar_modelo() primeiro.")
        
        custo_total = 0
        
        # Custo de combustível diesel
        if self.diesel is not None:
            for t in range(self.periodos):
                custo_total += self.diesel.custo_por_kWh * self.uso_diesel[t] / 60
                if t > 0:
                    custo_total += 5 * (self.diesel_ligado[t] - self.diesel_ligado[t - 1])
        
        # Custo de biogas
    #    if self.biogas is not None:
     #       for t in range(self.periodos):
      #          custo_total += self.biogas.custo_por_kWh * self.uso_biogas[t] / 60
        
        # Custo de bateria
        if self.bateria is not None:
            for t in range(self.periodos):
                custo_total += self.bateria.custo_kwh * self.uso_bateria[t] / 60
        
        # Custo de concessionária
        if self.concessionaria is not None:
            for t in range(self.periodos):
                custo_total += self.concessionaria.tarifa * self.uso_concessionaria[t] / 60
        
        # Custo de solar (negligenciável)
        if self.solar is not None:
            custo_total += 0.01 * lpSum(self.uso_solar)
        
        # Penalidade por mudanças rápidas na bateria (suaviza o comportamento)
        if self.bateria is not None:
            # Penalizar transições rápidas (0.01 R$/kW - leve, não impede uso)
            custo_total += 0.01 * lpSum(self.delta_desc[t] / 60 for t in range(1, self.periodos))
            custo_total += 0.01 * lpSum(self.delta_carga[t] / 60 for t in range(1, self.periodos))
        
        # Penalidade por desperdiçar solar (força recarga da bateria)
        if self.solar is not None:
            custo_total += 10 * lpSum(self.curtail_solar[t] / 60 for t in range(self.periodos))
        
        # NÃO INCLUI RECEITA DE VENDA
        
        self.modelo += custo_total, "Custo_Total"
        
        if verbose:
            print("Função objetivo adicionada (SEM VENDA)")


def analise_milp(microrrede: Microrrede):
    """
    Função para análise MILP da microrrede
    
    Args:
        microrrede: Objeto da microrrede a otimizar
    
    Returns:
        Tuple com os resultados (dataframe, custos, solução)
    """
    # Criar e resolver modelo MILP
    otimizador = MILPMicrorredes(microrrede)
    
    print("\n" + "="*60)
    print("OTIMIZAÇÃO MILP - CONTROLE DE MICRORREDE")
    print("="*60)
    
    # Criar modelo
    otimizador.criar_modelo()
    
    # Adicionar restrições
    otimizador.adicionar_restricoes()
    
    # Adicionar função objetivo
    otimizador.adicionar_funcao_objetivo()
    
    # Resolver
    sucesso = otimizador.resolver()
    
    if not sucesso:
        print("✗ Não foi possível resolver o modelo MILP")
        return None, None, None
    
    # Extrair solução
    solucao = otimizador.extrair_solucao()
    
    # Gerar resultados
    df_resultado = otimizador.gerar_dataframe_resultado()
    custos = otimizador.calcular_custos_totais()
    
    # Exibir resumo
    print("\n" + "-"*60)
    print("RESUMO DOS CUSTOS")
    print("-"*60)
    for fonte, custo in custos.items():
        if fonte != 'Total':
            print(f"{fonte:20s}: R$ {custo:>10,.2f}")
    print("-"*60)
    print(f"{'CUSTO TOTAL':20s}: R$ {custos['Total']:>10,.2f}")
    print("="*60 + "\n")
    
    return df_resultado, custos, solucao


def analise_milp_sem_venda(microrrede: Microrrede):
    """
    Função para análise MILP SEM VENDA DA REDE - Método 5.1
    
    Args:
        microrrede: Objeto da microrrede a otimizar
    
    Returns:
        Tuple com os resultados (dataframe, custos, solução)
    """
    # Criar e resolver modelo MILP SEM VENDA
    otimizador = MILPMicrorredes_SemVenda(microrrede)
    
    print("\n" + "="*60)
    print("OTIMIZAÇÃO MILP - SEM VENDA (Método 5.1)")
    print("="*60)
    
    # Criar modelo
    otimizador.criar_modelo()
    
    # Adicionar restrições
    otimizador.adicionar_restricoes()
    
    # Adicionar função objetivo
    otimizador.adicionar_funcao_objetivo()
    
    # Resolver
    sucesso = otimizador.resolver()
    
    if not sucesso:
        print("✗ Não foi possível resolver o modelo MILP SEM VENDA")
        return None, None, None
    
    # Extrair solução
    solucao = otimizador.extrair_solucao()
    
    # Gerar resultados
    df_resultado = otimizador.gerar_dataframe_resultado()
    custos = otimizador.calcular_custos_totais()
    
    # Exibir resumo
    print("\n" + "-"*60)
    print("RESUMO DOS CUSTOS (SEM VENDA)")
    print("-"*60)
    for fonte, custo in custos.items():
        if fonte != 'Total':
            print(f"{fonte:20s}: R$ {custo:>10,.2f}")
    print("-"*60)
    print(f"{'CUSTO TOTAL':20s}: R$ {custos['Total']:>10,.2f}")
    print("="*60 + "\n")
    
    return df_resultado, custos, solucao


class MILPDeslizamentoCarga:
    """
    MILP centralizado para otimização do deslizamento de cargas flexíveis.

    Essa classe é AUTOSSUFICIENTE — não herda das classes MILPMicrorredes*
    para evitar bugs de herança e comportamentos inesperados.

    Objetivo: encontrar o horário de início ótimo para cada carga flexível
    (prioridade 2 e 3) minimizando o custo real de operação da microrrede.

    Formulação matemática:
    ─────────────────────
    Para cada carga flexível k com duração d_k e potência p_k:
        δ[k][s] ∈ {0,1}  →  1 se carga k inicia no minuto s
        Σ_s δ[k][s] = 1   →  exatamente um início por carga

    Demanda total no instante t:
        D(t) = D_fixo(t) + Σ_k p_k · Σ_{s: s≤t<s+d_k} δ[k][s]

    Balanço de energia (para cada t):
        P_solar(t) + P_bat_desc(t) + P_diesel(t) + P_biogas(t) + P_conc(t)
        = D(t) + P_bat_carga(t)

    Função objetivo (minimizar custo real):
        min Σ_t [ c_diesel·P_diesel(t) + c_biogas·P_biogas(t)
                + c_bat·P_bat_desc(t) + c_conc·P_conc(t) ] / 60
    """

    def __init__(
        self,
        microrrede,
        periodos: int = 1440,
        passo_deslizamento: int = 30,
        aplicar_penalidades: bool = False,
        curva_preco_mercado: list = None,
        soc_inicial: float = None,
        diesel_inicial: float = None,
        biogas_inicial: float = None,
    ):
        """
        Args:
            microrrede: objeto Microrrede ou MicrorredeSchema
            periodos: número de períodos (minutos no dia)
            passo_deslizamento: granularidade (min) para testar inícios das cargas
                                Valores menores = mais preciso, mais lento.
                                Recomendado: 30 min (bom balanço qualidade/velocidade)
            aplicar_penalidades: se True, adiciona penalidades auxiliares mínimas
                                 (só serve para desempate, não distorce o custo)
            curva_preco_mercado: lista com preço efetivo de energia por minuto
            soc_inicial: SoC inicial da bateria em kWh (se None, usa capacidade máxima)
            diesel_inicial: nível inicial de diesel em L (se None, usa tanque cheio)
            biogas_inicial: nível inicial de biogás em m³ (se None, usa tanque cheio)
        """
        self.microrrede = microrrede
        self.periodos = periodos
        self.passo = passo_deslizamento
        self.aplicar_penalidades = aplicar_penalidades
        self.curva_preco_mercado = curva_preco_mercado
        self.soc_inicial = soc_inicial
        self.diesel_inicial = diesel_inicial
        self.biogas_inicial = biogas_inicial

        # Fontes
        self.solar = microrrede.solar
        self.bateria = microrrede.bateria
        self.diesel = microrrede.diesel
        self.biogas = microrrede.biogas
        self.concessionaria = microrrede.concessionaria

        # Separar cargas: flexíveis (prioridade 2 e 3) vs fixas (prioridade 1)
        self.cargas_flexiveis = []
        self.cargas_fixas = []
        if microrrede.carga:
            for cf in microrrede.carga.cargaFixa:
                dur = int(cf.tempo_desliga) - int(cf.tempo_liga)
                if cf.prioridade in [2, 3] and cf.potencia > 0 and dur > 0:
                    self.cargas_flexiveis.append(cf)
                else:
                    self.cargas_fixas.append(cf)

        # Curva de demanda FIXA (cargas não deslocáveis)
        self.curva_fixa = np.zeros(periodos)
        for cf in self.cargas_fixas:
            t0 = max(0, int(cf.tempo_liga))
            t1 = min(periodos, int(cf.tempo_desliga))
            self.curva_fixa[t0:t1] += cf.potencia

        # Curva solar
        self.curva_solar = np.zeros(periodos)
        if self.solar is not None:
            try:
                raw = self.solar.curva_geracao
                vals = json.loads(raw) if isinstance(raw, str) else raw
                solar_arr = np.array([float(v) for v in vals], dtype=float)
                # Limitar pela potência instalada
                self.curva_solar = np.minimum(solar_arr, self.solar.potencia)
            except Exception:
                self.curva_solar = np.zeros(periodos)

        # Modelo PuLP (criado em criar_modelo)
        self.modelo = None
        self.solucao = None

    # ──────────────────────────────────────────────────────────────
    # Passo adaptativo por carga
    # ──────────────────────────────────────────────────────────────

    def _passo_para_carga(self, duracao: int) -> int:
        """Determina o passo (min) para uma carga com base em sua duração."""
        if duracao >= 480:
            return max(self.passo, 120)
        elif duracao >= 240:
            return max(self.passo, 60)
        elif duracao >= 120:
            return max(self.passo, 30)
        else:
            return max(self.passo, 15)

    # ──────────────────────────────────────────────────────────────
    # Criação do modelo
    # ──────────────────────────────────────────────────────────────

    def criar_modelo(self) -> None:
        """Cria todas as variáveis de decisão do modelo."""
        self.modelo = LpProblem("MILP_Deslizamento_Carga", LpMinimize)
        T = self.periodos

        # ── Variáveis contínuas de despacho (kW em cada minuto) ──────────
        self.P_solar  = [LpVariable(f"Psol_{t}", lowBound=0) for t in range(T)]
        self.P_bat_d  = [LpVariable(f"Pbat_d_{t}", lowBound=0) for t in range(T)]  # descarga
        self.P_bat_c  = [LpVariable(f"Pbat_c_{t}", lowBound=0) for t in range(T)]  # carga
        self.P_diesel = [LpVariable(f"Pdiesel_{t}", lowBound=0) for t in range(T)]
        self.P_biogas = [LpVariable(f"Pbiogas_{t}", lowBound=0) for t in range(T)]
        self.P_conc   = [LpVariable(f"Pconc_{t}", lowBound=0) for t in range(T)]
        self.P_curtail = [LpVariable(f"Pcurtail_{t}", lowBound=0) for t in range(T)]

        # ── Nível de armazenamento ────────────────────────────────────────
        if self.bateria is not None:
            self.E_bat = [LpVariable(f"Ebat_{t}", lowBound=0) for t in range(T + 1)]
        if self.diesel is not None:
            self.E_diesel = [LpVariable(f"Ediesel_{t}", lowBound=0) for t in range(T + 1)]
        if self.biogas is not None:
            self.E_biogas = [LpVariable(f"Ebiogas_{t}", lowBound=0) for t in range(T + 1)]

        # ── Binárias de modo ─────────────────────────────────────────────
        if self.bateria is not None:
            # 1 = descarregando, 0 = carregando/ocioso
            self.u_bat = [LpVariable(f"Ubat_{t}", cat='Binary') for t in range(T)]
        if self.diesel is not None:
            self.u_diesel = [LpVariable(f"Udiesel_{t}", cat='Binary') for t in range(T)]
        if self.biogas is not None:
            self.u_biogas = [LpVariable(f"Ubiogas_{t}", cat='Binary') for t in range(T)]

        # ── Binárias de deslizamento de carga ────────────────────────────
        # delta[k][s] = 1  ↔  carga k começa no minuto s
        self.delta = {}
        n_bins_total = 0
        for k, cf in enumerate(self.cargas_flexiveis):
            duracao = int(cf.tempo_desliga) - int(cf.tempo_liga)
            passo_k = self._passo_para_carga(duracao)
            max_s = T - duracao
            self.delta[k] = {
                s: LpVariable(f"delta_{k}_{s}", cat='Binary')
                for s in range(0, max_s + 1, passo_k)
            }
            n_bins_total += len(self.delta[k])

    # ──────────────────────────────────────────────────────────────
    # Restrições
    # ──────────────────────────────────────────────────────────────

    def adicionar_restricoes(self) -> None:
        """Adiciona todas as restrições físicas e operacionais."""
        T = self.periodos

        # ── 1. Cada carga flexível tem exatamente um início ───────────────
        for k in range(len(self.cargas_flexiveis)):
            self.modelo += (
                lpSum(self.delta[k][s] for s in self.delta[k]) == 1,
                f"UnicoInicio_{k}"
            )

        # ── 2. Balanço de energia em cada período ─────────────────────────
        for t in range(T):
            # Demanda flexível neste instante
            dem_flex = lpSum(
                self.cargas_flexiveis[k].potencia * self.delta[k][s]
                for k in range(len(self.cargas_flexiveis))
                for s in self.delta[k]
                if s <= t < s + int(self.cargas_flexiveis[k].tempo_desliga) - int(self.cargas_flexiveis[k].tempo_liga)
            )

            oferta = self.P_solar[t] + self.P_bat_d[t] + self.P_diesel[t] + \
                     self.P_biogas[t] + self.P_conc[t]
            demanda = self.curva_fixa[t] + dem_flex + self.P_bat_c[t]
            self.modelo += (oferta == demanda, f"Balanco_{t}")

        # ── 3. Solar ─────────────────────────────────────────────────────
        if self.solar is not None:
            for t in range(T):
                # Toda geração solar deve ser usada ou curtailada
                self.modelo += (
                    self.P_solar[t] + self.P_curtail[t] == self.curva_solar[t],
                    f"Solar_{t}"
                )
        else:
            # Sem solar: forçar zero
            for t in range(T):
                self.modelo += (self.P_solar[t] == 0, f"SemSolar_{t}")
                self.modelo += (self.P_curtail[t] == 0, f"SemCurtail_{t}")

        # ── 4. Bateria ────────────────────────────────────────────────────
        if self.bateria is not None:
            eta = self.bateria.eficiencia / 100.0
            cap_max = self.bateria.capacidade
            cap_min = self.bateria.capacidade_min
            pot_max = self.bateria.potencia

            # Estado inicial: SoC real ou capacidade máxima
            e_init = self.soc_inicial if self.soc_inicial is not None else cap_max
            e_init = max(cap_min, min(cap_max, e_init))
            self.modelo += (self.E_bat[0] == e_init, "Bat_inicial")

            for t in range(T):
                # Limites de potência
                self.modelo += (self.P_bat_d[t] <= pot_max * self.u_bat[t], f"BatD_max_{t}")
                self.modelo += (self.P_bat_c[t] <= pot_max * (1 - self.u_bat[t]), f"BatC_max_{t}")

                # Dinâmica de energia (kWh)
                self.modelo += (
                    self.E_bat[t + 1] ==
                    self.E_bat[t] - self.P_bat_d[t] / 60.0 + eta * self.P_bat_c[t] / 60.0,
                    f"Bat_din_{t}"
                )

                # Limites de capacidade
                self.modelo += (self.E_bat[t] >= cap_min, f"Bat_min_{t}")
                self.modelo += (self.E_bat[t] <= cap_max, f"Bat_max_{t}")

            # Estado final: pelo menos capacidade mínima ou 20% da capacidade
            self.modelo += (self.E_bat[T] >= max(cap_min, 0.2 * cap_max), "Bat_final_min")
        else:
            for t in range(T):
                self.modelo += (self.P_bat_d[t] == 0, f"SemBatD_{t}")
                self.modelo += (self.P_bat_c[t] == 0, f"SemBatC_{t}")

        # ── 5. Diesel ─────────────────────────────────────────────────────
        if self.diesel is not None:
            consumo_esp = getattr(self.diesel, 'consumo_especifico', 0.2)
            pot_diesel = self.diesel.potencia

            d_init = self.diesel_inicial if self.diesel_inicial is not None else self.diesel.tanque
            d_init = max(0.0, min(self.diesel.tanque, d_init))
            self.modelo += (self.E_diesel[0] == d_init, "Diesel_inicial")

            # Rampa máxima de 50% da potência por minuto
            ramp_max = 0.5 * pot_diesel

            for t in range(T):
                # Se ligado: deve gerar entre 20% e 100% da potência nominal
                self.modelo += (
                    self.P_diesel[t] <= pot_diesel * self.u_diesel[t],
                    f"Diesel_max_{t}"
                )
                self.modelo += (
                    self.P_diesel[t] >= 0.2 * pot_diesel * self.u_diesel[t],
                    f"Diesel_min_pot_{t}"
                )

                # Restrições de rampa (ramping)
                if t > 0:
                    self.modelo += (
                        self.P_diesel[t] - self.P_diesel[t - 1] <= ramp_max,
                        f"Diesel_ramp_up_{t}"
                    )
                    self.modelo += (
                        self.P_diesel[t - 1] - self.P_diesel[t] <= ramp_max,
                        f"Diesel_ramp_down_{t}"
                    )

                # Dinâmica do tanque
                self.modelo += (
                    self.E_diesel[t + 1] ==
                    self.E_diesel[t] - consumo_esp * self.P_diesel[t] / 60.0,
                    f"Diesel_din_{t}"
                )
                self.modelo += (self.E_diesel[t] >= 0, f"Diesel_empty_{t}")
                self.modelo += (self.E_diesel[t] <= self.diesel.tanque, f"Diesel_full_{t}")
        else:
            for t in range(T):
                self.modelo += (self.P_diesel[t] == 0, f"SemDiesel_{t}")

        # ── 6. Biogás ─────────────────────────────────────────────────────
        if self.biogas is not None:
            consumo_esp_bg = getattr(self.biogas, 'consumo_especifico', 0.15)
            geracao_bg = getattr(self.biogas, 'geracao_instantanea', 0.0)
            pot_biogas = self.biogas.potencia

            bg_init = self.biogas_inicial if self.biogas_inicial is not None else self.biogas.tanque
            bg_init = max(0.0, min(self.biogas.tanque, bg_init))
            self.modelo += (self.E_biogas[0] == bg_init, "Biogas_inicial")

            for t in range(T):
                self.modelo += (
                    self.P_biogas[t] <= pot_biogas * self.u_biogas[t],
                    f"Biogas_max_{t}"
                )
                self.modelo += (
                    self.P_biogas[t] >= 0.2 * pot_biogas * self.u_biogas[t],
                    f"Biogas_min_pot_{t}"
                )

                # Dinâmica do tanque (com regeneração)
                self.modelo += (
                    self.E_biogas[t + 1] ==
                    self.E_biogas[t] + geracao_bg / 60.0 -
                    consumo_esp_bg * self.P_biogas[t] / 60.0,
                    f"Biogas_din_{t}"
                )
                self.modelo += (self.E_biogas[t] >= 0, f"Biogas_empty_{t}")
                self.modelo += (self.E_biogas[t] <= self.biogas.tanque, f"Biogas_full_{t}")
        else:
            for t in range(T):
                self.modelo += (self.P_biogas[t] == 0, f"SemBiogas_{t}")

        # ── 7. Concessionária: sem limite superior (pode suprir tudo) ─────
        # (sem restrição adicional — já é limitada pela variável >= 0)

    # ──────────────────────────────────────────────────────────────
    # Função objetivo
    # ──────────────────────────────────────────────────────────────

    def adicionar_funcao_objetivo(self) -> None:
        """
        Minimiza o custo real de operação.

        Apenas custos reais das fontes entram na função objetivo.
        Penalidades auxiliares (se habilitadas) são calibradas para ser
        ordens de magnitude menores que qualquer custo real, servindo apenas
        para desempatar soluções de mesmo custo — sem jamais distorcer a decisão.
        """
        T = self.periodos
        custo = 0

        # Custo real de cada fonte por período
        if self.diesel is not None:
            c_d = self.diesel.custo_por_kWh
            custo += lpSum(c_d * self.P_diesel[t] / 60.0 for t in range(T))

        if self.biogas is not None:
            c_bg = self.biogas.custo_por_kWh
            custo += lpSum(c_bg * self.P_biogas[t] / 60.0 for t in range(T))

        if self.bateria is not None:
            c_b = self.bateria.custo_kwh
            custo += lpSum(c_b * self.P_bat_d[t] / 60.0 for t in range(T))

        if self.concessionaria is not None:
            # Se curva de preço existe, usa ela; caso contrário, tarifa fixa
            if self.curva_preco_mercado is not None:
                custo += lpSum(self.curva_preco_mercado[t] * self.P_conc[t] / 60.0 for t in range(T))
            else:
                custo += lpSum(self.concessionaria.tarifa * self.P_conc[t] / 60.0 for t in range(T))

        if self.solar is not None:
            # Custo de solar negligenciável; forçar uso máximo penalizando curtailment
            # epsilon = 0.1% da tarifa mais barata disponível
            tarifas = [self.concessionaria.tarifa if self.concessionaria else 1.0]
            if self.diesel: tarifas.append(self.diesel.custo_por_kWh)
            if self.biogas: tarifas.append(self.biogas.custo_por_kWh)
            eps = min(tarifas) * 0.001
            custo += eps * lpSum(self.P_curtail[t] for t in range(T))

        # Penalidades auxiliares de desempate (opcionais, muito pequenas)
        if self.aplicar_penalidades and self.diesel is not None:
            # Suaviza ligações/desligamentos do diesel (custo de partida simbólico)
            tarifa_ref = self.concessionaria.tarifa if self.concessionaria else 1.0
            eps_start = tarifa_ref * 0.001  # << muito menor que qualquer custo real
            for t in range(1, T):
                custo += eps_start * (self.u_diesel[t] - self.u_diesel[t - 1])

        self.modelo += custo, "Custo_Total_Real"

    # ──────────────────────────────────────────────────────────────
    # Resolução
    # ──────────────────────────────────────────────────────────────

    def resolver(self, verbose: bool = False) -> bool:
        """
        Resolve o modelo MILP.

        Parâmetros do solver CBC:
        - timeLimit=600s: tempo suficiente para encontrar boas soluções
        - gapRel=0.005: aceita solução ≤0.5% acima do ótimo
        - threads=0: usa todos os núcleos disponíveis

        Retorna True se encontrou solução viável, False caso contrário.
        """
        if self.modelo is None:
            raise RuntimeError("Modelo não criado. Chame criar_modelo() primeiro.")

        try:
            self.modelo.solve(
                PULP_CBC_CMD(msg=0, timeLimit=600, gapRel=0.005, threads=0)
            )

            obj_val = value(self.modelo.objective)

            if self.modelo.status == 1:
                if verbose:
                    print(f"  [MILP] Ótimo encontrado | Custo: R$ {obj_val:,.2f}")
                return True
            elif obj_val is not None:
                # Solução viável (timeLimit atingido antes do certificado de otimalidade)
                if verbose:
                    print(f"  [MILP] Solução viável (timeout) | Custo: R$ {obj_val:,.2f}")
                self.modelo.status = 1  # aceitar como válida
                return True
            else:
                if verbose:
                    print(f"  [MILP] Sem solução. Status={self.modelo.status}")
                return False
        except Exception as exc:
            if verbose:
                print(f"  [MILP] Erro: {exc}")
            return False

    # ──────────────────────────────────────────────────────────────
    # Extração da solução
    # ──────────────────────────────────────────────────────────────

    def extrair_solucao(self) -> Dict:
        """
        Extrai os resultados do modelo resolvido.

        Retorna dicionário com:
        - 'Horarios_Cargas': {nome_carga: {original_inicio, otimizado_inicio, ...}}
        - 'Custo_Total': valor da função objetivo (R$)
        - Arrays de despacho por fonte
        """
        if self.modelo is None or value(self.modelo.objective) is None:
            raise RuntimeError("Modelo não resolvido.")

        T = self.periodos

        def _val(v):
            x = value(v)
            return max(0.0, x) if x is not None else 0.0

        # Despacho por fonte
        sol_solar   = np.array([_val(self.P_solar[t])  for t in range(T)])
        sol_bat_d   = np.array([_val(self.P_bat_d[t])  for t in range(T)])
        sol_bat_c   = np.array([_val(self.P_bat_c[t])  for t in range(T)])
        sol_diesel  = np.array([_val(self.P_diesel[t]) for t in range(T)])
        sol_biogas  = np.array([_val(self.P_biogas[t]) for t in range(T)])
        sol_conc    = np.array([_val(self.P_conc[t])   for t in range(T)])
        sol_curtail = np.array([_val(self.P_curtail[t]) for t in range(T)])

        # Nível de bateria
        sol_E_bat = np.zeros(T + 1)
        if self.bateria is not None:
            sol_E_bat = np.array([_val(self.E_bat[t]) for t in range(T + 1)])

        # Horários ótimos das cargas flexíveis
        horarios_cargas = {}
        for k, cf in enumerate(self.cargas_flexiveis):
            duracao = int(cf.tempo_desliga) - int(cf.tempo_liga)
            for s, var in self.delta[k].items():
                if _val(var) > 0.5:  # binária ativa
                    horarios_cargas[cf.nome] = {
                        'original_inicio': int(cf.tempo_liga),
                        'original_fim':    int(cf.tempo_desliga),
                        'otimizado_inicio': s,
                        'otimizado_fim':    s + duracao,
                        'potencia':  cf.potencia,
                        'prioridade': cf.prioridade,
                    }
                    break

        # Curva de carga com os horários ótimos
        curva_otimizada = np.copy(self.curva_fixa)
        for nome, info in horarios_cargas.items():
            t0, t1 = info['otimizado_inicio'], info['otimizado_fim']
            curva_otimizada[t0:t1] += info['potencia']

        # Custo instantâneo real (R$ por minuto)
        custo_inst = np.zeros(T)
        if self.diesel is not None:
            custo_inst += sol_diesel * self.diesel.custo_por_kWh / 60.0
        if self.biogas is not None:
            custo_inst += sol_biogas * self.biogas.custo_por_kWh / 60.0
        if self.bateria is not None:
            custo_inst += sol_bat_d * self.bateria.custo_kwh / 60.0
        if self.concessionaria is not None:
            for t in range(T):
                tarifa_t = self.curva_preco_mercado[t] if self.curva_preco_mercado is not None else self.concessionaria.tarifa
                custo_inst[t] += sol_conc[t] * tarifa_t / 60.0

        self.solucao = {
            'Solar':           sol_solar,
            'Bateria':         sol_bat_d,
            'Carga_Bateria':   sol_bat_c,
            'Diesel':          sol_diesel,
            'Biogas':          sol_biogas,
            'Concessionaria':  sol_conc,
            'Curtail_Solar':   sol_curtail,
            'Venda':           np.zeros(T),  # sem venda nesta implementação
            'Nivel_Bateria':   sol_E_bat,
            'Custo_Total':     float(value(self.modelo.objective)),
            'Custo_Instante':  custo_inst,
            'Horarios_Cargas': horarios_cargas,
            'Curva_Carga_Otimizada': curva_otimizada,
        }
        return self.solucao

    def gerar_dataframe_resultado(self) -> pd.DataFrame:
        """Retorna DataFrame no formato esperado pelas páginas Streamlit."""
        if self.solucao is None:
            raise RuntimeError("Chame extrair_solucao() primeiro.")
        return pd.DataFrame({
            'Carga':          self.solucao['Curva_Carga_Otimizada'],
            'Solar':          self.solucao['Solar'],
            'Bateria':        self.solucao['Bateria'],
            'Carga_Bateria':  self.solucao['Carga_Bateria'],
            'Diesel':         self.solucao['Diesel'],
            'Biogas':         self.solucao['Biogas'],
            'Concessionaria': self.solucao['Concessionaria'],
            'Venda':          self.solucao['Venda'],
        })

    def calcular_custos_totais(self) -> Dict:
        """Retorna custos totais por fonte (kWh × custo unitário), compatível com a API anterior."""
        if self.solucao is None:
            raise RuntimeError("Chame extrair_solucao() primeiro.")
        sol = self.solucao
        custos = {}
        if self.solar is not None:
            custos['Solar'] = float(sol['Solar'].sum() / 60.0 * self.solar.custo_kwh)
        if self.bateria is not None:
            custos['Bateria'] = float(sol['Bateria'].sum() / 60.0 * self.bateria.custo_kwh)
        if self.diesel is not None:
            custos['Diesel'] = float(sol['Diesel'].sum() / 60.0 * self.diesel.custo_por_kWh)
        if self.biogas is not None:
            custos['Biogas'] = float(sol['Biogas'].sum() / 60.0 * self.biogas.custo_por_kWh)
        if self.concessionaria is not None:
            custos['Concessionaria'] = float(sol['Concessionaria'].sum() / 60.0 * self.concessionaria.tarifa)
        custos['Total'] = sum(custos.values())
        return custos


# Manter alias para compatibilidade retroativa com código que importe a classe antiga
MILPMicrorredes_ComDeslizamento = MILPDeslizamentoCarga


def analise_milp_com_deslizamento(microrrede, passo: int = 30, aplicar_penalidades: bool = False):
    """
    Interface de alto nível para MILP com deslizamento de cargas (prioridades 2 e 3).

    Args:
        microrrede: objeto Microrrede
        passo: granularidade em minutos para testar inícios (padrão: 30 min)
        aplicar_penalidades: se True, adiciona penalidades auxiliares mínimas de desempate

    Returns:
        (df_resultado, custos, solucao) ou (None, None, None) se falhar
    """
    print("\n" + "=" * 60)
    print("MILP — DESLIZAMENTO DE CARGAS (Prioridades 2 e 3)")
    print("=" * 60)

    otm = MILPDeslizamentoCarga(
        microrrede,
        passo_deslizamento=passo,
        aplicar_penalidades=aplicar_penalidades,
    )
    otm.criar_modelo()
    otm.adicionar_restricoes()
    otm.adicionar_funcao_objetivo()

    sucesso = otm.resolver(verbose=True)
    if not sucesso:
        print("✗ Não foi possível resolver o modelo MILP.")
        return None, None, None

    solucao  = otm.extrair_solucao()
    df       = otm.gerar_dataframe_resultado()
    custos   = otm.calcular_custos_totais()

    print("\n" + "-" * 60)
    print("RESUMO DOS CUSTOS")
    print("-" * 60)
    for fonte, custo in custos.items():
        if fonte != 'Total':
            print(f"  {fonte:20s}: R$ {custo:>10,.2f}")
    print("-" * 60)
    print(f"  {'CUSTO TOTAL':20s}: R$ {custos['Total']:>10,.2f}")

    if solucao.get('Horarios_Cargas'):
        print("\n📋 CARGAS DESLOCADAS:")
        for nome, info in solucao['Horarios_Cargas'].items():
            h_orig = f"{info['original_inicio'] // 60:02d}:{info['original_inicio'] % 60:02d}"
            h_otim = f"{info['otimizado_inicio'] // 60:02d}:{info['otimizado_inicio'] % 60:02d}"
            print(f"  {nome} (P{info['prioridade']}): {h_orig} → {h_otim} ({info['potencia']:.1f} kW)")
    print("=" * 60 + "\n")

    return df, custos, solucao



# ==============================================================================
# MILP CENTRALIZADO — OTIMIZAÇÃO CONJUNTA MULTI-MICRORREDE COM TRADES P2P
# ==============================================================================

class MILPCentralizado:
    """
    Modelo MILP Centralizado para Otimização Conjunta de Múltiplas Microrredes.
    
    Conforme a literatura recente (2023-2024), este modelo formula todas as
    microrredes e suas transações P2P em um ÚNICO problema de programação inteira
    mista, garantindo o ótimo global de cooperação energética e deslizamento de cargas.
    
    Principais características:
    - Deslizamento conjunto de cargas flexíveis (prioridades 2 e 3)
    - Variáveis de trade P2P explícitas entre pares de microrredes (i -> j)
    - Consideração das perdas elétricas por distância entre microrredes
    - Despacho ótimo e restrições de rampa para geradores
    - Dinâmica exata de baterias com restrições de estado inicial (SoC real)
    """

    def __init__(
        self,
        microrredes: list,
        periodos: int = 1440,
        passo_deslizamento: int = 30,
        coef_perda_km: float = 0.004,
        margem_venda: float = 0.05,
        estados_iniciais: dict = None,
    ):
        """
        Args:
            microrredes: Lista de objetos Microrrede ou MicrorredeSchema
            periodos: Minutos no dia (1440)
            passo_deslizamento: Granularidade (min) para testar inícios das cargas flexíveis
            coef_perda_km: Coeficiente de perda por km
            margem_venda: Margem sobre o custo de geração no mercado P2P
            estados_iniciais: Dicionário opcional com SoC e níveis de tanques iniciais por MG
        """
        self.microrredes = microrredes
        self.periodos = periodos
        self.passo = passo_deslizamento
        self.coef_perda_km = coef_perda_km
        self.margem_venda = margem_venda
        self.estados_iniciais = estados_iniciais or {}
        
        self.nomes_mg = [str(mg.nome) for mg in microrredes]
        self.num_mg = len(microrredes)
        
        # Mapeamento e separação de cargas por microrrede
        self.cargas_flexiveis = {}
        self.cargas_fixas = {}
        self.curva_fixa = {}
        self.curva_solar = {}
        
        for mg in microrredes:
            nome = str(mg.nome)
            self.cargas_flexiveis[nome] = []
            self.cargas_fixas[nome] = []
            if mg.carga:
                for cf in mg.carga.cargaFixa:
                    dur = int(cf.tempo_desliga) - int(cf.tempo_liga)
                    if cf.prioridade in [2, 3] and cf.potencia > 0 and dur > 0:
                        self.cargas_flexiveis[nome].append(cf)
                    else:
                        self.cargas_fixas[nome].append(cf)
                        
            # Curva fixa da MG
            cf_arr = np.zeros(periodos)
            for cf in self.cargas_fixas[nome]:
                t0 = max(0, int(cf.tempo_liga))
                t1 = min(periodos, int(cf.tempo_desliga))
                cf_arr[t0:t1] += cf.potencia
            self.curva_fixa[nome] = cf_arr
            
            # Curva solar da MG
            cs_arr = np.zeros(periodos)
            if mg.solar is not None:
                try:
                    raw = mg.solar.curva_geracao
                    vals = json.loads(raw) if isinstance(raw, str) else raw
                    solar_arr = np.array([float(v) for v in vals], dtype=float)
                    cs_arr = np.minimum(solar_arr, mg.solar.potencia)
                except Exception:
                    cs_arr = np.zeros(periodos)
            self.curva_solar[nome] = cs_arr
            
        # Matriz de perdas por distância
        self.perdas_p2p = {}
        for i, mg_i in enumerate(microrredes):
            nome_i = str(mg_i.nome)
            for j, mg_j in enumerate(microrredes):
                nome_j = str(mg_j.nome)
                if nome_i != nome_j:
                    lat1, lon1 = getattr(mg_i, 'latitude', 0.0), getattr(mg_i, 'longitude', 0.0)
                    lat2, lon2 = getattr(mg_j, 'latitude', 0.0), getattr(mg_j, 'longitude', 0.0)
                    dist = distancia_haversine(lat1, lon1, lat2, lon2)
                    self.perdas_p2p[(nome_i, nome_j)] = min(dist * self.coef_perda_km, 0.99)

        self.modelo = None
        self.solucao = None

    def _passo_para_carga(self, duracao: int) -> int:
        if duracao >= 480:
            return max(self.passo, 120)
        elif duracao >= 240:
            return max(self.passo, 60)
        elif duracao >= 120:
            return max(self.passo, 30)
        else:
            return max(self.passo, 15)

    def criar_modelo(self) -> None:
        self.modelo = LpProblem("MILP_Centralizado_MultiMicrorrede", LpMinimize)
        T = self.periodos
        
        self.P_solar = {}
        self.P_bat_d = {}
        self.P_bat_c = {}
        self.P_diesel = {}
        self.P_biogas = {}
        self.P_conc = {}
        self.P_curtail = {}
        self.E_bat = {}
        self.E_diesel = {}
        self.E_biogas = {}
        self.u_bat = {}
        self.u_diesel = {}
        self.u_biogas = {}
        self.delta = {}
        
        for mg in self.microrredes:
            nome = str(mg.nome)
            self.P_solar[nome] = [LpVariable(f"Psol_{nome}_{t}", lowBound=0) for t in range(T)]
            self.P_bat_d[nome] = [LpVariable(f"Pbat_d_{nome}_{t}", lowBound=0) for t in range(T)]
            self.P_bat_c[nome] = [LpVariable(f"Pbat_c_{nome}_{t}", lowBound=0) for t in range(T)]
            self.P_diesel[nome] = [LpVariable(f"Pdiesel_{nome}_{t}", lowBound=0) for t in range(T)]
            self.P_biogas[nome] = [LpVariable(f"Pbiogas_{nome}_{t}", lowBound=0) for t in range(T)]
            self.P_conc[nome] = [LpVariable(f"Pconc_{nome}_{t}", lowBound=0) for t in range(T)]
            self.P_curtail[nome] = [LpVariable(f"Pcurtail_{nome}_{t}", lowBound=0) for t in range(T)]
            
            if mg.bateria is not None:
                self.E_bat[nome] = [LpVariable(f"Ebat_{nome}_{t}", lowBound=0) for t in range(T + 1)]
                self.u_bat[nome] = [LpVariable(f"Ubat_{nome}_{t}", cat='Binary') for t in range(T)]
            if mg.diesel is not None:
                self.E_diesel[nome] = [LpVariable(f"Ediesel_{nome}_{t}", lowBound=0) for t in range(T + 1)]
                self.u_diesel[nome] = [LpVariable(f"Udiesel_{nome}_{t}", cat='Binary') for t in range(T)]
            if mg.biogas is not None:
                self.E_biogas[nome] = [LpVariable(f"Ebiogas_{nome}_{t}", lowBound=0) for t in range(T + 1)]
                self.u_biogas[nome] = [LpVariable(f"Ubiogas_{nome}_{t}", cat='Binary') for t in range(T)]
                
            # Binárias de início de cargas flexíveis
            self.delta[nome] = {}
            for k, cf in enumerate(self.cargas_flexiveis[nome]):
                duracao = int(cf.tempo_desliga) - int(cf.tempo_liga)
                passo_k = self._passo_para_carga(duracao)
                max_s = T - duracao
                self.delta[nome][k] = {
                    s: LpVariable(f"delta_{nome}_{k}_{s}", cat='Binary')
                    for s in range(0, max_s + 1, passo_k)
                }

        # Variáveis de Trade P2P entre microrredes (i -> j no minuto t)
        self.P_trade = {}
        for nome_i in self.nomes_mg:
            for nome_j in self.nomes_mg:
                if nome_i != nome_j:
                    self.P_trade[(nome_i, nome_j)] = [
                        LpVariable(f"Trade_{nome_i}_{nome_j}_{t}", lowBound=0) for t in range(T)
                    ]

    def adicionar_restricoes(self) -> None:
        T = self.periodos
        
        for mg in self.microrredes:
            nome = str(mg.nome)
            
            # 1. Início único de cada carga flexível
            for k in range(len(self.cargas_flexiveis[nome])):
                self.modelo += (
                    lpSum(self.delta[nome][k][s] for s in self.delta[nome][k]) == 1,
                    f"UnicoInicio_{nome}_{k}"
                )
                
            # 2. Balanço de Potência da Microrrede com Trades P2P
            for t in range(T):
                dem_flex = lpSum(
                    self.cargas_flexiveis[nome][k].potencia * self.delta[nome][k][s]
                    for k in range(len(self.cargas_flexiveis[nome]))
                    for s in self.delta[nome][k]
                    if s <= t < s + int(self.cargas_flexiveis[nome][k].tempo_desliga) - int(self.cargas_flexiveis[nome][k].tempo_liga)
                )
                
                # Energia recebida de outras MGs (com perda na transmissão)
                compra_p2p = lpSum(
                    self.P_trade[(nome_outro, nome)][t] * (1.0 - self.perdas_p2p[(nome_outro, nome)])
                    for nome_outro in self.nomes_mg if nome_outro != nome
                )
                
                # Energia enviada para outras MGs
                venda_p2p = lpSum(
                    self.P_trade[(nome, nome_outro)][t]
                    for nome_outro in self.nomes_mg if nome_outro != nome
                )
                
                geracao_local = (
                    self.P_solar[nome][t] + self.P_bat_d[nome][t] +
                    self.P_diesel[nome][t] + self.P_biogas[nome][t] +
                    self.P_conc[nome][t]
                )
                
                consumo_total = self.curva_fixa[nome][t] + dem_flex + self.P_bat_c[nome][t]
                
                # Balanço nodal exato: Geração Local + Importação P2P == Consumo Local + Exportação P2P
                self.modelo += (
                    geracao_local + compra_p2p == consumo_total + venda_p2p,
                    f"BalancoP2P_{nome}_{t}"
                )
                
            # 3. Restrições de Solar
            if mg.solar is not None:
                for t in range(T):
                    self.modelo += (
                        self.P_solar[nome][t] + self.P_curtail[nome][t] == self.curva_solar[nome][t],
                        f"Solar_{nome}_{t}"
                    )
            else:
                for t in range(T):
                    self.modelo += (self.P_solar[nome][t] == 0, f"SemSolar_{nome}_{t}")
                    self.modelo += (self.P_curtail[nome][t] == 0, f"SemCurtail_{nome}_{t}")

            # 4. Restrições de Bateria
            if mg.bateria is not None:
                eta = mg.bateria.eficiencia / 100.0
                cap_max = mg.bateria.capacidade
                cap_min = mg.bateria.capacidade_min
                pot_max = mg.bateria.potencia
                
                e_init = self.estados_iniciais.get(nome, {}).get('soc', cap_max)
                e_init = max(cap_min, min(cap_max, e_init))
                self.modelo += (self.E_bat[nome][0] == e_init, f"Bat_init_{nome}")
                
                for t in range(T):
                    self.modelo += (self.P_bat_d[nome][t] <= pot_max * self.u_bat[nome][t], f"BatD_max_{nome}_{t}")
                    self.modelo += (self.P_bat_c[nome][t] <= pot_max * (1 - self.u_bat[nome][t]), f"BatC_max_{nome}_{t}")
                    self.modelo += (
                        self.E_bat[nome][t + 1] ==
                        self.E_bat[nome][t] - self.P_bat_d[nome][t] / 60.0 + eta * self.P_bat_c[nome][t] / 60.0,
                        f"Bat_din_{nome}_{t}"
                    )
                    self.modelo += (self.E_bat[nome][t] >= cap_min, f"Bat_min_{nome}_{t}")
                    self.modelo += (self.E_bat[nome][t] <= cap_max, f"Bat_max_{nome}_{t}")
                self.modelo += (self.E_bat[nome][T] >= max(cap_min, 0.2 * cap_max), f"Bat_final_{nome}")
            else:
                for t in range(T):
                    self.modelo += (self.P_bat_d[nome][t] == 0, f"SemBatD_{nome}_{t}")
                    self.modelo += (self.P_bat_c[nome][t] == 0, f"SemBatC_{nome}_{t}")

            # 5. Restrições de Diesel com Ramping
            if mg.diesel is not None:
                consumo_esp = getattr(mg.diesel, 'consumo_especifico', 0.2)
                pot_diesel = mg.diesel.potencia
                ramp_max = 0.5 * pot_diesel
                
                d_init = self.estados_iniciais.get(nome, {}).get('diesel', mg.diesel.tanque)
                d_init = max(0.0, min(mg.diesel.tanque, d_init))
                self.modelo += (self.E_diesel[nome][0] == d_init, f"Diesel_init_{nome}")
                
                for t in range(T):
                    self.modelo += (self.P_diesel[nome][t] <= pot_diesel * self.u_diesel[nome][t], f"Diesel_max_{nome}_{t}")
                    self.modelo += (self.P_diesel[nome][t] >= 0.2 * pot_diesel * self.u_diesel[nome][t], f"Diesel_min_{nome}_{t}")
                    if t > 0:
                        self.modelo += (self.P_diesel[nome][t] - self.P_diesel[nome][t - 1] <= ramp_max, f"Diesel_rup_{nome}_{t}")
                        self.modelo += (self.P_diesel[nome][t - 1] - self.P_diesel[nome][t] <= ramp_max, f"Diesel_rdown_{nome}_{t}")
                    self.modelo += (
                        self.E_diesel[nome][t + 1] ==
                        self.E_diesel[nome][t] - consumo_esp * self.P_diesel[nome][t] / 60.0,
                        f"Diesel_din_{nome}_{t}"
                    )
                    self.modelo += (self.E_diesel[nome][t] >= 0, f"Diesel_empty_{nome}_{t}")
                    self.modelo += (self.E_diesel[nome][t] <= mg.diesel.tanque, f"Diesel_full_{nome}_{t}")
            else:
                for t in range(T):
                    self.modelo += (self.P_diesel[nome][t] == 0, f"SemDiesel_{nome}_{t}")

            # 6. Restrições de Biogás
            if mg.biogas is not None:
                consumo_esp_bg = getattr(mg.biogas, 'consumo_especifico', 0.15)
                geracao_bg = getattr(mg.biogas, 'geracao_instantanea', 0.0)
                pot_biogas = mg.biogas.potencia
                
                bg_init = self.estados_iniciais.get(nome, {}).get('biogas', mg.biogas.tanque)
                bg_init = max(0.0, min(mg.biogas.tanque, bg_init))
                self.modelo += (self.E_biogas[nome][0] == bg_init, f"Biogas_init_{nome}")
                
                for t in range(T):
                    self.modelo += (self.P_biogas[nome][t] <= pot_biogas * self.u_biogas[nome][t], f"Biogas_max_{nome}_{t}")
                    self.modelo += (self.P_biogas[nome][t] >= 0.2 * pot_biogas * self.u_biogas[nome][t], f"Biogas_min_{nome}_{t}")
                    self.modelo += (
                        self.E_biogas[nome][t + 1] ==
                        self.E_biogas[nome][t] + geracao_bg / 60.0 - consumo_esp_bg * self.P_biogas[nome][t] / 60.0,
                        f"Biogas_din_{nome}_{t}"
                    )
                    self.modelo += (self.E_biogas[nome][t] >= 0, f"Biogas_empty_{nome}_{t}")
                    self.modelo += (self.E_biogas[nome][t] <= mg.biogas.tanque, f"Biogas_full_{nome}_{t}")
            else:
                for t in range(T):
                    self.modelo += (self.P_biogas[nome][t] == 0, f"SemBiogas_{nome}_{t}")

    def adicionar_funcao_objetivo(self) -> None:
        T = self.periodos
        custo_global = 0
        
        for mg in self.microrredes:
            nome = str(mg.nome)
            if mg.diesel is not None:
                c_d = mg.diesel.custo_por_kWh
                custo_global += lpSum(c_d * self.P_diesel[nome][t] / 60.0 for t in range(T))
            if mg.biogas is not None:
                c_bg = mg.biogas.custo_por_kWh
                custo_global += lpSum(c_bg * self.P_biogas[nome][t] / 60.0 for t in range(T))
            if mg.bateria is not None:
                c_b = mg.bateria.custo_kwh
                custo_global += lpSum(c_b * self.P_bat_d[nome][t] / 60.0 for t in range(T))
            if mg.concessionaria is not None:
                c_c = mg.concessionaria.tarifa
                custo_global += lpSum(c_c * self.P_conc[nome][t] / 60.0 for t in range(T))
            if mg.solar is not None:
                eps = 0.0001
                custo_global += eps * lpSum(self.P_curtail[nome][t] for t in range(T))

        self.modelo += custo_global, "Custo_Total_Mercado_Centralizado"

    def resolver(self, verbose: bool = False) -> bool:
        if self.modelo is None:
            raise RuntimeError("Modelo não criado. Chame criar_modelo() primeiro.")
        try:
            self.modelo.solve(
                PULP_CBC_CMD(msg=0, timeLimit=600, gapRel=0.005, threads=0)
            )
            obj_val = value(self.modelo.objective)
            if self.modelo.status == 1 or obj_val is not None:
                return True
            return False
        except Exception as exc:
            if verbose:
                print(f"Erro no MILPCentralizado: {exc}")
            return False

    def extrair_solucao(self) -> dict:
        if self.modelo is None or value(self.modelo.objective) is None:
            raise RuntimeError("Modelo não resolvido.")
            
        def _val(v):
            x = value(v)
            return max(0.0, x) if x is not None else 0.0
            
        horarios_cargas = {}
        for mg in self.microrredes:
            nome = str(mg.nome)
            horarios_cargas[nome] = {}
            for k, cf in enumerate(self.cargas_flexiveis[nome]):
                duracao = int(cf.tempo_desliga) - int(cf.tempo_liga)
                for s, var in self.delta[nome][k].items():
                    if _val(var) > 0.5:
                        horarios_cargas[nome][cf.nome] = {
                            'original_inicio': int(cf.tempo_liga),
                            'original_fim': int(cf.tempo_desliga),
                            'otimizado_inicio': s,
                            'otimizado_fim': s + duracao,
                            'potencia': cf.potencia,
                            'prioridade': cf.prioridade,
                        }
                        break
                        
        self.solucao = {
            'Custo_Total': float(value(self.modelo.objective)),
            'Horarios_Cargas': horarios_cargas,
        }
        return self.solucao
