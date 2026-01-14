"""
# Explicação dos Otimizadores

1. **Otimizador Linear (MPILP)**:
   - Resolve problemas de otimização linear inteira mista.
   - Utiliza o método simplex ou variantes para encontrar a solução ótima.
   - Exemplo de uso: Minimizar custos de operação com restrições de capacidade e demanda.

2. **Algoritmos Genéticos (GA)**:
   - Baseado em evolução genética, simula seleção natural.
   - Utiliza conceitos de seleção, crossover e mutação para explorar o espaço de soluções.
   - Exemplo de uso: Encontrar configurações ótimas em problemas não lineares.

3. **Particle Swarm Optimization (PSO)**:
   - Baseado no comportamento de enxames (como pássaros ou peixes).
   - Cada partícula representa uma solução e ajusta sua posição com base em sua melhor solução e a do grupo.
   - Exemplo de uso: Otimização contínua em espaços de alta dimensão.

4. **Ant Colony Optimization (ACO)**:
   - Inspirado no comportamento de formigas na busca por alimentos.
   - Utiliza trilhas de feromônio para guiar a busca por soluções.
   - Exemplo de uso: Problemas de roteamento e caminhos mínimos.

5. **Simulated Annealing (SA)**:
   - Baseado no processo de resfriamento de metais.
   - Explora soluções vizinhas e aceita soluções piores com uma probabilidade que diminui ao longo do tempo.
   - Exemplo de uso: Encontrar mínimos globais em funções complexas.

"""

from scipy.optimize import linprog
import numpy as np
import random

# Otimização 1 '''
'''
Otimizador simples de tomada de decisão simples com base nos custos (microrede)
Compara os custos de energia e seleciona o mais barato e usa caso não de usa energia do mais proxímo 
'''
def Otimizador1(microrredes):
    
    for microrrede in enumerate(microrredes):
        analise = []
        
        biogas = microrrede.biogas
        bateria = microrrede.bateria
        rede = microrrede.concessionaria
        diesel = microrrede.diesel
        solar = microrrede.solar
        
        custo_biogas = biogas.custo_m3
        custo_bateria = bateria.custo_kwh
        custo_rede = rede.tarifa
        custo_diesel = diesel.custo
        custo_solar = solar.custo_kwh

        valores = {'custo_biogas':custo_biogas, 'custo_bateria': custo_bateria, 'custo_rede':custo_rede, 'custo_diesel':custo_diesel, 'custo_solar':custo_solar}
        barata = min(valores, key=valores.get)

        
        
        

# Programação matemática clássica
# Otimização 2
'''
Otimizador (MPILP) -> Microrredes 
'''
# Meta-heurísticas
# Otimização 3
'''
Algoritmos Genéticos (GA)
'''

# Otimização 4
'''
Particle Swarm Optimization (PSO):
'''
 
# Otimização 5
'''
Ant Colony Optimization (ACO)
'''

#Otimização 6 
'''
Simulated Annealing (SA)
'''

class OtimizadorLinear:
    """
    Resolve problemas de otimização linear.
    Exemplo: Minimizar custo com restrições de demanda e capacidade.
    """
    def __init__(self, custos, restricoes, limites):
        self.custos = custos
        self.restricoes = restricoes
        self.limites = limites

    def otimizar(self):
        resultado = linprog(self.custos, A_eq=self.restricoes["A_eq"], b_eq=self.restricoes["b_eq"], bounds=self.limites, method="highs")
        return resultado


class OtimizadorHeuristicoPSO:
    """
    Otimizador baseado em Particle Swarm Optimization (PSO).
    """
    def __init__(self, funcao_objetivo, limites, num_particulas=30, iteracoes=100):
        self.funcao_objetivo = funcao_objetivo
        self.limites = limites
        self.num_particulas = num_particulas
        self.iteracoes = iteracoes

    def otimizar(self):
        # Inicializa partículas
        dimensoes = len(self.limites)
        particulas = np.random.uniform([lim[0] for lim in self.limites], [lim[1] for lim in self.limites], (self.num_particulas, dimensoes))
        velocidades = np.random.uniform(-1, 1, (self.num_particulas, dimensoes))
        melhores_locais = particulas.copy()
        melhores_globais = particulas[np.argmin([self.funcao_objetivo(p) for p in particulas])]

        for _ in range(self.iteracoes):
            for i, particula in enumerate(particulas):
                fitness = self.funcao_objetivo(particula)
                if fitness < self.funcao_objetivo(melhores_locais[i]):
                    melhores_locais[i] = particula
                if fitness < self.funcao_objetivo(melhores_globais):
                    melhores_globais = particula

            # Atualiza velocidades e posições
            velocidades = 0.5 * velocidades + 0.5 * np.random.rand() * (melhores_locais - particulas) + 0.5 * np.random.rand() * (melhores_globais - particulas)
            particulas = np.clip(particulas + velocidades, [lim[0] for lim in self.limites], [lim[1] for lim in self.limites])

        return melhores_globais, self.funcao_objetivo(melhores_globais)


class OtimizadorMPILP:
    """
    Resolve problemas de otimização linear inteira mista.
    """
    def __init__(self, custos, restricoes, limites):
        self.custos = custos
        self.restricoes = restricoes
        self.limites = limites

    def otimizar(self):
        resultado = linprog(self.custos, A_eq=self.restricoes["A_eq"], b_eq=self.restricoes["b_eq"], bounds=self.limites, method="highs")
        return resultado


class OtimizadorGA:
    """
    Otimizador baseado em Algoritmos Genéticos.
    """
    def __init__(self, funcao_objetivo, limites, populacao=50, geracoes=100, taxa_mutacao=0.1):
        self.funcao_objetivo = funcao_objetivo
        self.limites = limites
        self.populacao = populacao
        self.geracoes = geracoes
        self.taxa_mutacao = taxa_mutacao

    def otimizar(self):
        # Inicializa população
        dimensoes = len(self.limites)
        individuos = np.random.uniform([lim[0] for lim in self.limites], [lim[1] for lim in self.limites], (self.populacao, dimensoes))

        for _ in range(self.geracoes):
            # Avalia fitness
            fitness = np.array([self.funcao_objetivo(ind) for ind in individuos])
            pais = individuos[np.argsort(fitness)[:self.populacao // 2]]  # Seleciona os melhores

            # Crossover
            filhos = []
            for _ in range(self.populacao // 2):
                pai1, pai2 = random.choices(pais, k=2)
                ponto_corte = random.randint(1, dimensoes - 1)
                filho = np.concatenate((pai1[:ponto_corte], pai2[ponto_corte:]))
                filhos.append(filho)

            # Mutação
            filhos = np.array(filhos)
            mutacao = np.random.rand(*filhos.shape) < self.taxa_mutacao
            filhos = np.clip(filhos + mutacao * np.random.uniform(-1, 1, filhos.shape), [lim[0] for lim in self.limites], [lim[1] for lim in self.limites])

            # Atualiza população
            individuos = np.vstack((pais, filhos))

        melhor_indice = np.argmin([self.funcao_objetivo(ind) for ind in individuos])
        return individuos[melhor_indice], self.funcao_objetivo(individuos[melhor_indice])


class OtimizadorACO:
    """
    Otimizador baseado em Colônia de Formigas.
    """
    def __init__(self, funcao_objetivo, limites, num_formigas=20, iteracoes=50):
        self.funcao_objetivo = funcao_objetivo
        self.limites = limites
        self.num_formigas = num_formigas
        self.iteracoes = iteracoes

    def otimizar(self):
        # Inicializa trilhas de feromônio
        dimensoes = len(self.limites)
        feromonio = np.ones((self.num_formigas, dimensoes))
        melhor_solucao = None
        melhor_custo = float("inf")

        for _ in range(self.iteracoes):
            solucoes = []
            for _ in range(self.num_formigas):
                solucao = np.random.uniform([lim[0] for lim in self.limites], [lim[1] for lim in self.limites])
                custo = self.funcao_objetivo(solucao)
                solucoes.append((solucao, custo))

                # Atualiza melhor solução
                if custo < melhor_custo:
                    melhor_solucao = solucao
                    melhor_custo = custo

            # Atualiza feromônio
            for solucao, custo in solucoes:
                feromonio += 1 / (1 + custo)

        return melhor_solucao, melhor_custo


class OtimizadorSA:
    """
    Otimizador baseado em Simulated Annealing.
    """
    def __init__(self, funcao_objetivo, limites, temperatura_inicial=100, resfriamento=0.95, iteracoes=100):
        self.funcao_objetivo = funcao_objetivo
        self.limites = limites
        self.temperatura = temperatura_inicial
        self.resfriamento = resfriamento
        self.iteracoes = iteracoes

    def otimizar(self):
        # Inicializa solução
        dimensoes = len(self.limites)
        solucao_atual = np.random.uniform([lim[0] for lim in self.limites], [lim[1] for lim in self.limites])
        custo_atual = self.funcao_objetivo(solucao_atual)
        melhor_solucao = solucao_atual
        melhor_custo = custo_atual

        for _ in range(self.iteracoes):
            # Gera nova solução
            nova_solucao = solucao_atual + np.random.uniform(-1, 1, dimensoes)
            nova_solucao = np.clip(nova_solucao, [lim[0] for lim in self.limites], [lim[1] for lim in self.limites])
            novo_custo = self.funcao_objetivo(nova_solucao)

            # Aceita ou rejeita nova solução
            if novo_custo < custo_atual or np.random.rand() < np.exp((custo_atual - novo_custo) / self.temperatura):
                solucao_atual = nova_solucao
                custo_atual = novo_custo

                if novo_custo < melhor_custo:
                    melhor_solucao = nova_solucao
                    melhor_custo = novo_custo

            # Resfria temperatura
            self.temperatura *= self.resfriamento

        return melhor_solucao, melhor_custo


class OtimizadorBaseadoRegras:
    """
    Otimizador que utiliza regras fixas para priorizar ações.
    """
    def __init__(self, regras):
        self.regras = regras

    def otimizar(self, contexto):
        for regra in self.regras:
            if regra["condicao"](contexto):
                return regra["acao"](contexto)


# Adaptação do Otimizador Linear para minimizar custo de energia
class OtimizadorCustoEnergia:
    """
    Otimizador para minimizar o custo de energia considerando múltiplas fontes.
    """
    def __init__(self, custos, capacidades, demanda):
        """
        :param custos: Lista com os custos por unidade de energia para cada fonte.
        :param capacidades: Lista com as capacidades máximas de cada fonte.
        :param demanda: Demanda total de energia a ser atendida.
        """
        self.custos = custos
        self.capacidades = capacidades
        self.demanda = demanda

    def otimizar(self):
        """
        Resolve o problema de otimização para minimizar o custo de energia.
        """
        num_fontes = len(self.custos)

        # Função objetivo: minimizar custo total
        c = self.custos

        # Restrições de igualdade: atender à demanda total
        A_eq = [[1] * num_fontes]  # Soma das energias fornecidas por todas as fontes
        b_eq = [self.demanda]

        # Restrições de capacidade: cada fonte não pode exceder sua capacidade máxima
        bounds = [(0, cap) for cap in self.capacidades]

        # Resolve o problema de otimização
        resultado = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
        return resultado

# Exemplo de uso
if __name__ == "__main__":
    # Otimizador Linear
    custos = [1, 2, 3]  # Coeficientes da função objetivo
    restricoes = {
        "A_eq": [[1, 1, 1]],  # Soma das variáveis deve ser igual a 7
        "b_eq": [7]
    }
    limites = [(0, None), (0, None), (0, None)]  # Limites das variáveis
    otimizador_linear = OtimizadorLinear(custos, restricoes, limites)
    resultado_linear = otimizador_linear.otimizar()
    print("Resultado Otimizador Linear:", resultado_linear)

    # Otimizador Heurístico (PSO)
    def funcao_objetivo(x):
        return sum(x**2)  # Exemplo: minimizar soma dos quadrados

    limites_pso = [(-10, 10), (-10, 10)]
    otimizador_pso = OtimizadorHeuristicoPSO(funcao_objetivo, limites_pso)
    resultado_pso = otimizador_pso.otimizar()
    print("Resultado Otimizador PSO:", resultado_pso)

    # Otimizador MPILP
    custos_mpilp = [1, 2, 3]  # Coeficientes da função objetivo
    restricoes_mpilp = {
        "A_eq": [[1, 1, 1]],  # Soma das variáveis deve ser igual a 7
        "b_eq": [7]
    }
    limites_mpilp = [(0, None), (0, None), (0, None)]  # Limites das variáveis
    otimizador_mpilp = OtimizadorMPILP(custos_mpilp, restricoes_mpilp, limites_mpilp)
    resultado_mpilp = otimizador_mpilp.otimizar()
    print("Resultado Otimizador MPILP:", resultado_mpilp)

    # Otimizador GA
    def funcao_objetivo_ga(x):
        return sum(x**2)  # Exemplo: minimizar soma dos quadrados

    limites_ga = [(-10, 10), (-10, 10)]
    otimizador_ga = OtimizadorGA(funcao_objetivo_ga, limites_ga)
    resultado_ga = otimizador_ga.otimizar()
    print("Resultado Otimizador GA:", resultado_ga)

    # Otimizador ACO
    def funcao_objetivo_aco(x):
        return sum(x**2)  # Exemplo: minimizar soma dos quadrados

    limites_aco = [(-10, 10), (-10, 10)]
    otimizador_aco = OtimizadorACO(funcao_objetivo_aco, limites_aco)
    resultado_aco = otimizador_aco.otimizar()
    print("Resultado Otimizador ACO:", resultado_aco)

    # Otimizador SA
    def funcao_objetivo_sa(x):
        return sum(x**2)  # Exemplo: minimizar soma dos quadrados

    limites_sa = [(-10, 10), (-10, 10)]
    otimizador_sa = OtimizadorSA(funcao_objetivo_sa, limites_sa)
    resultado_sa = otimizador_sa.otimizar()
    print("Resultado Otimizador SA:", resultado_sa)

    # Otimizador Baseado em Regras
    regras = [
        {"condicao": lambda ctx: ctx["demanda"] > 10, "acao": lambda ctx: "Usar Diesel"},
        {"condicao": lambda ctx: ctx["demanda"] <= 10, "acao": lambda ctx: "Usar Solar"}
    ]
    otimizador_regras = OtimizadorBaseadoRegras(regras)
    contexto = {"demanda": 8}
    resultado_regras = otimizador_regras.otimizar(contexto)
    print("Resultado Otimizador Baseado em Regras:", resultado_regras)

    # Otimizador Custo Energia
    custos = [0.5, 0.3, 0.8, 0.6]  # Exemplo: [Solar, Biogás, Diesel, Bateria]
    capacidades = [100, 50, 80, 60]
    demanda = 120
    otimizador_custo_energia = OtimizadorCustoEnergia(custos, capacidades, demanda)
    resultado_custo_energia = otimizador_custo_energia.otimizar()

    # Exibe os resultados do Otimizador Custo Energia
    if resultado_custo_energia.success:
        print("Solução encontrada para Otimizador Custo Energia:")
        for i, energia in enumerate(resultado_custo_energia.x):
            print(f"Fonte {i + 1}: {energia:.2f} kWh")
        print(f"Custo total: R${resultado_custo_energia.fun:.2f}")
    else:
        print("Não foi possível encontrar uma solução para Otimizador Custo Energia.")