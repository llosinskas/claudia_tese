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
        
        if verbose:
            print("✓ Variáveis de decisão criadas")
    
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
        if self.solar is not None:
            for t in range(self.periodos):
                self.modelo += self.uso_solar[t] <= self.curva_solar[t], f"Limite_solar_{t}"
        
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
                self.modelo += self.uso_bateria[t] <= self.bateria.potencia, f"Limite_descarga_bat_{t}"
                self.modelo += self.carga_bateria[t] <= self.bateria.potencia, f"Limite_carga_bat_{t}"
        
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
        
        # 4. CARREGAMENTO DA BATERIA APENAS COM EXCESSO SOLAR
        if self.solar is not None and self.bateria is not None:
            for t in range(self.periodos):
                # Carregamento só ocorre se há excesso solar
                self.modelo += self.carga_bateria[t] <= self.curva_solar[t], f"Carga_bat_solar_{t}"
        
        if verbose:
            print("✓ Restrições adicionadas")
    
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
                    custo_total += 50 * (self.diesel_ligado[t] - self.diesel_ligado[t - 1])
        
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
        
        self.modelo += custo_total, "Custo_Total"
        
        if verbose:
            print("✓ Função objetivo adicionada")
    
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
            # Usar solver padrão (CBC)
            self.modelo.solve(PULP_CBC_CMD(msg=0))
            
            if self.modelo.status == 1:  # Optimal
                if verbose:
                    print(f"✓ Modelo resolvido com sucesso!")
                    print(f"  Status: Ótimo")
                    print(f"  Custo total: R$ {value(self.modelo.objective):,.2f}")
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
            print("✓ Variáveis de decisão criadas (SEM VENDA)")
    
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
        if self.solar is not None:
            for t in range(self.periodos):
                self.modelo += self.uso_solar[t] <= self.curva_solar[t], f"Limite_solar_{t}"
        
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
                self.modelo += self.uso_bateria[t] <= self.bateria.potencia, f"Limite_descarga_bat_{t}"
                self.modelo += self.carga_bateria[t] <= self.bateria.potencia, f"Limite_carga_bat_{t}"
        
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
        
        # 4. CARREGAMENTO DA BATERIA APENAS COM EXCESSO SOLAR
        if self.solar is not None and self.bateria is not None:
            for t in range(self.periodos):
                self.modelo += self.carga_bateria[t] <= self.curva_solar[t], f"Carga_bat_solar_{t}"
        
        if verbose:
            print("✓ Restrições adicionadas (SEM VENDA)")
    
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
                    custo_total += 50 * (self.diesel_ligado[t] - self.diesel_ligado[t - 1])
        
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
        
        # NÃO INCLUI RECEITA DE VENDA
        
        self.modelo += custo_total, "Custo_Total"
        
        if verbose:
            print("✓ Função objetivo adicionada (SEM VENDA)")


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
