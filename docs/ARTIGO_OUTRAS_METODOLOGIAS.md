# Outras Metodologias de Otimização para Microrredes
## Além de MILP e Heurísticas: Comparação de Técnicas Avançadas

---

## 1. CATEGORIZAÇÃO DAS METODOLOGIAS

```
OTIMIZAÇÃO
├─ Métodos Exatos
│  ├─ MILP (Mixed Integer Linear Programming) ✓ Seu projeto
│  ├─ PNL (Programação Não-Linear)
│  └─ Programação Dinâmica
│
├─ Meta-Heurísticas
│  ├─ Algoritmos Evolutivos (Genético, PSO)
│  ├─ Simulated Annealing
│  ├─ Ant Colony Optimization
│  └─ Tabu Search
│
├─ Machine Learning / IA
│  ├─ Deep Reinforcement Learning
│  ├─ Neural Networks
│  ├─ Gradient Boosting
│  └─ Support Vector Machines
│
├─ Controle Avançado
│  ├─ Model Predictive Control (MPC)
│  ├─ Stochastic Programming
│  └─ Otimização Robusta
│
└─ Distribuído / Descentralizado
   ├─ Multi-Agent Systems
   ├─ Game Theory
   └─ Consenso Distribuído
```

---

## 2. PROGRAMAÇÃO DINÂMICA (Dynamic Programming)

### 2.1 O que é?

Decomposição do problema em **estágios** (períodos de tempo) e **estados** (nível de armazenamento).

Resolve "de trás para frente": partir do fim do dia, calcular a decisão ótima para cada estado.

### 2.2 Princípio da Otimalidade de Bellman

$$V_t(E) = \min_{u_t} \left[ C_t(u_t) + V_{t+1}(E + \Delta E) \right]$$

Onde:
- $V_t(E)$ = custo acumulado ótimo a partir do estado E no tempo t
- $u_t$ = ação (despacho) no tempo t
- $C_t(u_t)$ = custo instantâneo
- $\Delta E$ = mudança de armazenamento

### 2.3 Exemplo Prático

```python
import numpy as np

def programacao_dinamica_microrrede(demanda, solar, custos, T=1440):
    """
    Programação dinâmica para despacho ótimo
    
    Estados: E_bat = 0 a 100 kWh (em passos de 1 kWh)
    Períodos: t = 0 a 1439 minutos
    Ações: P_diesel, P_rede (P_solar é fixo, P_bateria = f(ação))
    """
    
    # Aproximação por discretização
    E_estados = np.arange(0, 101, 1)  # 0-100 kWh em 1kWh steps
    
    # Inicializar tabela V(t, E)
    V = np.full((T+1, len(E_estados)), float('inf'))
    V[T, :] = 0  # Condição final (sem custo futuro)
    
    # Regressão no tempo
    for t in range(T-1, -1, -1):
        for i_E, E in enumerate(E_estados):
            # Tentar todas as ações possíveis
            custo_minimo = float('inf')
            melhor_acao = None
            
            # Ação: quantidade de diesel a usar
            for P_diesel in range(0, 41, 5):  # 0-40 kW em steps 5
                # Calcular novo estado E_next
                P_solar_t = solar[t]
                P_demanda = demanda[t]
                P_bateria = min(50, P_demanda - P_solar_t - P_diesel)  # Máx 50 kW
                
                if P_bateria < 0:
                    P_bateria = 0
                    P_rede = P_demanda - P_solar_t - P_diesel - P_bateria
                else:
                    P_rede = 0
                
                # Novo nível de bateria
                E_next = E - P_bateria/60 + 0  # Sem carregamento agora
                E_next = max(20, min(100, E_next))  # Limites
                
                i_E_next = int(E_next)
                
                # Custo instantâneo + futuro
                custo_instantaneo = (P_diesel * custos['diesel'] + 
                                    P_rede * custos['rede']) / 60
                custo_total = custo_instantaneo + V[t+1, i_E_next]
                
                if custo_total < custo_minimo:
                    custo_minimo = custo_total
                    melhor_acao = P_diesel
            
            V[t, i_E] = custo_minimo
    
    # Reconstruir solução ótima (forward)
    E_atual = 100  # Nível inicial
    solucao = []
    
    for t in range(T):
        i_E = int(E_atual)
        # Encontrar ação que alcançou V[t, i_E]
        # (simplificado: re-otimizar)
        melhor_P_diesel = 0
        melhor_custo = float('inf')
        
        for P_diesel in range(0, 41, 5):
            P_solar_t = solar[t]
            P_demanda = demanda[t]
            P_bateria = min(50, P_demanda - P_solar_t - P_diesel)
            
            if P_bateria < 0:
                P_bateria = 0
                P_rede = P_demanda - P_solar_t - P_diesel - P_bateria
            else:
                P_rede = 0
            
            E_next = max(20, min(100, E_atual - P_bateria/60))
            i_E_next = int(E_next)
            
            custo = (P_diesel * custos['diesel'] + P_rede * custos['rede'])/60 + V[t+1, i_E_next]
            
            if custo < melhor_custo:
                melhor_custo = custo
                melhor_P_diesel = P_diesel
        
        solucao.append(melhor_P_diesel)
        # Atualizar estado
        P_solar_t = solar[t]
        P_demanda = demanda[t]
        P_bateria = min(50, P_demanda - P_solar_t - melhor_P_diesel)
        E_atual -= P_bateria / 60
        E_atual = max(20, min(100, E_atual))
    
    custo_total_DP = V[0, 100]
    return solucao, custo_total_DP

# Uso
custos_exemplo = {'diesel': 0.40, 'rede': 0.60}
solucao_DP, custo_DP = programacao_dinamica_microrrede(
    demanda[:100], solar[:100], custos_exemplo, T=100
)
print(f"Custo DP: R$ {custo_DP:.2f}")
```

### 2.4 Vantagens / Desvantagens

| Aspecto | DP |
|--------|-----|
| **Optimalidade** | ✅ Exato (como MILP) |
| **Tempo** | ⚠️ Exponencial no tamanho do espaço de estado |
| **Discretização** | ❌ Precisa discretizar (bateria 1 kWh steps) |
| **Escalabilidade** | ❌ Explode com múltiplas fontes/estados |
| **Implementação** | ✅ Simples (loops aninhados) |
| **Parallelização** | ❌ Difícil (dependência temporal) |

**Conclusão**: DP é viável para microrredes simples com poucas variáveis de estado, mas **MILP é superior** para sistemas complexos (múltiplas fontes, restrições não-estruturadas).

---

## 3. META-HEURÍSTICAS

### 3.1 Algoritmos Genéticos (Genetic Algorithms)

#### **Conceito**

Simula evolução biológica: população → mutação → seleção → convergência

#### **Implementação**

```python
from deap import base, creator, tools, algorithms
import random
import numpy as np

# Seu projeto JÁ tem algoritmo similar em: otmizadores/pso.py
# Aqui vamos fazer um GA

class MicrorredGA:
    """Otimização com Algoritmo Genético"""
    
    def __init__(self, demanda, solar, custos, pop_size=100, geracao_max=50):
        self.demanda = demanda
        self.solar = solar
        self.custos = custos
        self.pop_size = pop_size
        self.geracao_max = geracao_max
        
        # Indivíduo = vetor de decisões [P_diesel_0, P_diesel_1, ..., P_diesel_1439]
        # Cada gene: potência diesel 0-40 kW
        self.tam_individuo = len(demanda)
    
    def avaliacao_custo(self, individuo):
        """
        Avalia custo de um indivíduo (estratégia de despacho)
        
        Retorna: (custo_total,) em tupla (DEAP exige tupla)
        """
        custo_total = 0
        E_bat = 100  # Nível inicial bateria
        
        for t in range(len(self.demanda)):
            P_diesel = individuo[t]
            P_solar_t = self.solar[t]
            P_demanda = self.demanda[t]
            
            # Balanço de energia
            P_bat = min(50, P_demanda - P_solar_t - P_diesel)
            
            if P_bat < 0:
                P_bat = 0
                P_rede = P_demanda - P_solar_t - P_diesel
            else:
                P_rede = 0
            
            # Custo instantâneo
            custo_t = (P_diesel * self.custos['diesel'] + 
                      P_rede * self.custos['rede'] +
                      P_bat * self.custos['bateria']) / 60
            custo_total += custo_t
            
            # Atualizar estado bateria
            E_bat -= P_bat / 60
            E_bat = max(20, min(100, E_bat))
            
            # Penalidade se violar limite
            if E_bat < 20 or P_rede > 100:
                custo_total += 1000  # Grande penalidade
        
        return (custo_total,)  # DEAP exige tupla
    
    def otimizar(self):
        """
        Executa algoritmo genético
        """
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))  # Minimizar
        creator.create("Individual", list, fitness=creator.FitnessMin)
        
        toolbox = base.Toolbox()
        
        # Gerar genes (potência diesel 0-40)
        toolbox.register("gene", random.uniform, 0, 40)
        
        # Criar indivíduo
        toolbox.register("individual", 
                        tools.initRepeat, creator.Individual,
                        toolbox.gene, n=self.tam_individuo)
        
        # Criar população
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        
        # Registrar operações
        toolbox.register("evaluate", self.avaliacao_custo)
        toolbox.register("mate", tools.cxBlend, alpha=0.5)  # Cruzamento
        toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=5, indpb=0.1)  # Mutação
        toolbox.register("select", tools.selTournament, tournsize=3)
        
        # Limites de genes
        toolbox.decorate("mate", tools.DeltaPenality(
            [0, 40] * self.tam_individuo, (-1e10,)))
        toolbox.decorate("mutate", tools.DeltaPenality(
            [0, 40] * self.tam_individuo, (-1e10,)))
        
        # Executar EA
        pop = toolbox.population(n=self.pop_size)
        hof = tools.HallOfFame(1)
        
        pop, logbook = algorithms.eaSimple(pop, toolbox, 
                                          cxpb=0.7,  # Probabilidade cruzamento
                                          mutpb=0.3,  # Probabilidade mutação
                                          ngen=self.geracao_max,
                                          halloffame=hof,
                                          verbose=True)
        
        melhor_individuo = hof[0]
        melhor_custo = melhor_individuo.fitness.values[0]
        
        return melhor_individuo, melhor_custo, logbook

# Usar
custos = {'diesel': 0.40, 'rede': 0.60, 'bateria': 0.15}
ga = MicrorredGA(demanda[:200], solar[:200], custos, pop_size=50, geracao_max=30)
melhor, custo, log = ga.otimizar()

print(f"✓ Custo GA: R$ {custo:.2f}")
```

#### **Vantagens / Desvantagens**

| Aspecto | GA |
|--------|-----|
| **Optimalidade** | ❌ Heurística (frequentemente subótima) |
| **Tempo** | ⚠️ Variável (gerações × população) |
| **Implementação** | ✅ Simples com DEAP |
| **Parallelização** | ✅ Excelente (cada geração é parallelizável) |
| **Parâmetros** | ❌ Muitos (mutação, cruzamento, seleção) |
| **Convergência** | ⚠️ Não garantida |

---

### 3.2 Particle Swarm Optimization (PSO)

#### **Conceito**

Simula bando de pássaros: partículas exploram espaço, lembram melhor posição, seguem melhor global.

#### **Seu projeto JÁ tem PSO**!

Arquivo: [otmizadores/pso.py](otmizadores/pso.py)

```python
# Pseudocódigo da implementação padrão

class PSO:
    def __init__(self, num_particulas=30, dim=1440, max_iter=100):
        self.particulas = []  # Posições X
        self.velocidades = []  # Velocidades V
        self.melhor_pessoal = []  # Melhor de cada partícula
        self.melhor_global = None  # Melhor global
        self.melhor_custo_global = float('inf')
    
    def otimizar(self, funcao_custo):
        """
        Otimização via PSO
        """
        for iteracao in range(self.max_iter):
            # 1. Avaliar cada partícula
            for i, particula in enumerate(self.particulas):
                custo = funcao_custo(particula)
                
                # 2. Atualizar melhor pessoal
                if custo < self.melhor_custo_pessoal[i]:
                    self.melhor_pessoal[i] = particula.copy()
                    self.melhor_custo_pessoal[i] = custo
                
                # 3. Atualizar melhor global
                if custo < self.melhor_custo_global:
                    self.melhor_global = particula.copy()
                    self.melhor_custo_global = custo
            
            # 4. Atualizar velocidades e posições
            for i in range(len(self.particulas)):
                r1, r2 = random.random(), random.random()
                
                # V = w*V + c1*r1*(X_pessoal - X) + c2*r2*(X_global - X)
                self.velocidades[i] = (
                    0.7 * self.velocidades[i] +
                    2.0 * r1 * (self.melhor_pessoal[i] - self.particulas[i]) +
                    2.0 * r2 * (self.melhor_global - self.particulas[i])
                )
                
                # X = X + V
                self.particulas[i] += self.velocidades[i]
                
                # Clip aos limites [0, 40]
                self.particulas[i] = np.clip(self.particulas[i], 0, 40)
        
        return self.melhor_global, self.melhor_custo_global
```

#### **Vantagens / Desvantagens**

| Aspecto | PSO |
|--------|-----|
| **Velocidade Converge** | ✅ Rápido (10-20 iterações) |
| **Qualidade** | ⚠️ Bom (80-95% vs MILP) |
| **Implementação** | ✅ Simples |
| **Parallelização** | ✅ Boa |
| **Seu projeto** | ✅ JÁ TEM IMPLEMENTADO |

**Para seu artigo**: PSO é uma **excelente adicional** às 5 análises! Você poderia ter:
- Análise 1-4: Heurísticas
- Análise 5: MILP
- **Análise 6: PSO** ← Adicione isso!

---

### 3.3 Simulated Annealing

#### **Conceito**

Simula resfriamento de metal: aceitaeitas soluções ruins com probabilidade decrescente.

```python
import math
import random

class SimulatedAnnealing:
    def __init__(self, temp_inicial=1000, taxa_resfriamento=0.95):
        self.T = temp_inicial
        self.taxa = taxa_resfriamento
    
    def otimizar(self, solucao_inicial, funcao_custo, max_iter=1000):
        """
        Simulated Annealing
        """
        X = solucao_inicial.copy()
        custo_atual = funcao_custo(X)
        X_melhor = X.copy()
        custo_melhor = custo_atual
        
        historico = []
        
        for iteracao in range(max_iter):
            # 1. Gerar vizinho (modificar um gene aleatoriamente)
            X_novo = X.copy()
            idx_aleatorio = random.randint(0, len(X) - 1)
            X_novo[idx_aleatorio] += random.gauss(0, 2)  # Mutação pequena
            X_novo[idx_aleatorio] = np.clip(X_novo[idx_aleatorio], 0, 40)
            
            # 2. Avaliar nova solução
            custo_novo = funcao_custo(X_novo)
            delta_custo = custo_novo - custo_atual
            
            # 3. Aceitar / Rejeitar
            if delta_custo < 0 or random.random() < math.exp(-delta_custo / self.T):
                X = X_novo
                custo_atual = custo_novo
                
                # Atualizar melhor
                if custo_novo < custo_melhor:
                    X_melhor = X_novo.copy()
                    custo_melhor = custo_novo
            
            # 4. Resfriar
            self.T *= self.taxa
            
            historico.append(custo_melhor)
        
        return X_melhor, custo_melhor, historico

# Usar
sa = SimulatedAnnealing()
X_inicial = np.random.uniform(0, 40, 1440)
solucao_SA, custo_SA, hist = sa.otimizar(X_inicial, funcao_custo_microrrede)
print(f"Custo SA: R$ {custo_SA:.2f}")
```

**Vantagens/Desvantagens**: Similar a GA, mas **melhor para problemas contínuos**

---

## 4. MACHINE LEARNING / IA

### 4.1 Deep Reinforcement Learning (DRL)

#### **Conceito**

Treinar rede neural para aprender a política ótima: "Dado o estado atual, qual ação tomar?"

#### **Implementação com Stable Baselines3**

```python
import gymnasium as gym
from stable_baselines3 import PPO, DQN
import numpy as np

class MicrorredEnv(gym.Env):
    """Environment OpenAI Gym para microrrede"""
    
    def __init__(self, demanda, solar, custos):
        super().__init__()
        self.demanda = demanda
        self.solar = solar
        self.custos = custos
        self.t = 0
        self.max_t = len(demanda)
        
        # Estado: [E_bateria, E_diesel, P_demanda_atual, P_solar_atual, t_normalized]
        self.observation_space = gym.spaces.Box(low=0, high=1, shape=(5,), dtype=np.float32)
        
        # Ação: [P_diesel (0-40 kW), P_rede (0-100 kW)]
        self.action_space = gym.spaces.Box(low=0, high=40, shape=(1,), dtype=np.float32)
    
    def reset(self, seed=None):
        self.t = 0
        self.E_bat = 100
        self.E_diesel = 200
        
        state = self._get_state()
        return state, {}
    
    def _get_state(self):
        """Normalizar estado para [0, 1]"""
        return np.array([
            self.E_bat / 100,           # 0-1
            self.E_diesel / 200,        # 0-1
            self.demanda[self.t] / 100, # 0-1 (normalizado)
            self.solar[self.t] / 50,    # 0-1 (50kW max)
            self.t / self.max_t,        # 0-1
        ], dtype=np.float32)
    
    def step(self, action):
        """Executar ação"""
        P_diesel = action[0]  # 0-40 kW (output da rede neural)
        
        P_demanda = self.demanda[self.t]
        P_solar_t = self.solar[self.t]
        
        # Balanço
        P_bat = min(50, P_demanda - P_solar_t - P_diesel)
        if P_bat < 0:
            P_bat = 0
            P_rede = P_demanda - P_solar_t - P_diesel
        else:
            P_rede = 0
        
        # Custo instantâneo (negative reward para minimizar)
        custo = (P_diesel * self.custos['diesel'] + 
                P_rede * self.custos['rede']) / 60
        reward = -custo
        
        # Penalidades
        if self.E_bat < 20:
            reward -= 100  # Bateria muito baixa
        if P_rede > 100:
            reward -= 500  # Excesso de demanda da rede
        
        # Atualizar estado
        self.E_bat -= P_bat / 60
        self.E_bat = max(20, min(100, self.E_bat))
        self.E_diesel -= P_diesel / 60 * 0.2  # Consumo
        
        self.t += 1
        done = self.t >= self.max_t
        
        state = self._get_state()
        
        return state, reward, done, False, {}

# Treinar agente
env = MicrorredEnv(demanda[:1440], solar[:1440], 
                   custos={'diesel': 0.40, 'rede': 0.60})

# PPO (Policy Gradient) é geralmente melhor
modelo = PPO("MlpPolicy", env, verbose=1, learning_rate=3e-4)
modelo.learn(total_timesteps=100000)

# Salvar modelo treinado
modelo.save("modelo_microrrede_drl")

# Usar modelo
modelo = PPO.load("modelo_microrrede_drl")
obs, _ = env.reset()
for _ in range(1440):
    acao, _ = modelo.predict(obs)
    obs, reward, done, _, _ = env.step(acao)
```

#### **Vantagens / Desvantagens**

| Aspecto | DRL |
|--------|-----|
| **Otimalidade** | ❌ Subótimo (~80-90% vs MILP) |
| **Tempo Treinamento** | ❌ Longo (horas/dias) |
| **Tempo Inferência** | ✅ Rápido (<1 ms) |
| **Adapta a Mudanças** | ✅ Pode re-treinar |
| **Interpretabilidade** | ❌ "Caixa preta" |
| **Implementação** | ⚠️ Requer PyTorch/TensorFlow |
| **Melhor para** | ✅ Controle tempo-real embarcado |

**Caso de uso**: Dopo de treinar offline, DRL é excelente para **controle em tempo-real** (reage em <1ms).

---

### 4.2 Neural Networks (Supervised Learning)

#### **Conceito**

Treinar rede para: dados históricos → decisões ótimas

```python
import tensorflow as tf

class MicrorredNN:
    """Rede neural treinada com histórico de MILP"""
    
    def __init__(self):
        # Arquitetura: 5 inputs → [hidden 64, 32] → 1 output
        self.modelo = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(5,)),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')  # P_diesel ∈ [0, 40]
        ])
        
        self.modelo.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
    
    def treinar(self, X_train, y_train, epochs=50, batch_size=32):
        """
        X_train: histórico [E_bat, E_diesel, P_demanda, P_solar, score_histórico]
        y_train: ações ótimas do MILP [P_diesel_ótimo]
        """
        self.modelo.fit(X_train, y_train, 
                       epochs=epochs, 
                       batch_size=batch_size,
                       validation_split=0.2,
                       verbose=1)
    
    def predizer(self, estado):
        """Problema -> Predição de ação ótima"""
        P_diesel_pred = self.modelo.predict(estado.reshape(1, -1))[0, 0]
        return P_diesel_pred * 40  # Desnormalizar [0, 40]

# Uso: treinar com dados de MILP
# 1. Rodar MILP diversas vezes (50 microrredes diferentes)
milp_historico_X = []
milp_historico_y = []

for mr_id in range(1, 51):
    mr = Ler_Objeto(Microrrede, mr_id)
    milp = MILPMicrorredes(mr)
    milp.resolver()
    solucao = milp.extrair_solucao()
    
    # Extrair estados e ações
    for t in range(1440):
        estado = [solucao['Nivel_Bateria'][t],
                 solucao['Nivel_Diesel'][t],
                 mr.carga.demanda[t],
                 float(mr.solar.curva_geracao[t]),
                 t/1440]
        acao = solucao['Diesel'][t]
        
        milp_historico_X.append(estado)
        milp_historico_y.append(acao)

# 2. Treinar NN
nn = MicrorredNN()
X_train = np.array(milp_historico_X)
y_train = np.array(milp_historico_y) / 40  # Normalizar
nn.treinar(X_train, y_train)

# 3. Usar NN em produção (super rápido!)
estado_atual = [100, 150, 50, 30, 0.5]  # E_bat, E_diesel, P_dem, P_solar, t
P_diesel_ótima = nn.predizer(np.array(estado_atual))
```

#### **Vantagens / Desvantagens**

| Aspecto | NN Supervisionada |
|--------|-----|
| **Velocidade** | ✅ <1ms (após treino) |
| **Qualidade** | ✅ Réplica MILP (90-99%) |
| **Requer Dados** | ⚠️ Precisa de exemplos MILP |
| **Implementação** | ✅ Simples com TensorFlow |
| **Deploy** | ✅ Excelente (arquivo .h5, ~2MB) |
| **Interpretabilidade** | ❌ "Caixa preta" |

**Caso de uso perfeito**: **MILP offline** (resolver melhor estratégia) + **NN embarcada** (executar rápido)!

---

## 5. MÉTODOS AVANÇADOS: ROBUSTEZ E INCERTEZA

### 5.1 Otimização Robusta

#### **Conceito**

Em vez de otimizar para previsão única, otimiza um **intervalo de cenários**:

$$\min_x \max_u C(x, u) \text{ onde } u \in U_{\text{incerteza}}$$

#### **Implementação: Intervalo de Incerteza**

```python
class MILPRobusta:
    """MILP que lida com incertezas na previsão solar"""
    
    def __init__(self, microrrede, incerteza_solar=0.2):
        """
        incerteza_solar: desvio esperado (ex: 20% menos)
        """
        self.microrrede = microrrede
        self.incerteza = incerteza_solar
        
    def criar_modelo_robusto(self):
        """
        MILP com restrições robustas
        """
        modelo = LpProblem("Microrrede_Robusta", LpMinimize)
        
        # Mesmo que MILP padrão, mas com variáveis adicionais
        
        # Solar nominal
        curva_solar = self.microrrede.solar.curva_geracao
        
        # Solar no pior caso (20% menos)
        curva_solar_pior_caso = np.array(curva_solar) * (1 - self.incerteza)
        
        # Restrições para AMBOS os cenários
        for t in range(1440):
            # Cenário nominal
            modelo += (self.P_solar[t] <= curva_solar[t], 
                      f"Solar_nominal_{t}")
            
            # Cenário pior (CRÍTICO)
            modelo += (self.P_solar[t] <= curva_solar_pior_caso[t],
                      f"Solar_pior_caso_{t}")
            
            # Se solar falhar, bateria deve conseguir suprir
            # P_demanda <= P_solar_pior + P_bateria + P_diesel + P_rede
            modelo += (self.P_solar[t] + self.P_bateria[t] + self.P_diesel[t] + 
                      self.P_rede[t] >= self.demanda[t],
                      f"Balanço_robusto_{t}")
        
        return modelo

# Usar
milp_robusto = MILPRobusta(microrrede, incerteza_solar=0.30)
modelo = milp_robusto.criar_modelo_robusto()
modelo.solve()

# Resultado: Estratégia conservadora que funciona mesmo com 30% menos solar
```

#### **Comparação**

```
Previsão solar: 50 kW
MILP Standard:  Carrega bateria com os 50 kW previstos
Realidade:      Solar = 35 kW (30% menos)
Resultado:      Bateria carrega menos, diesel ativa mais
                Custo > esperado

MILP Robusto:   Carrega bateria assumindo 35 kW (pior caso)
Realidade:      Solar = 35 kW
Resultado:      Funciona perfeitamente
                Custo = esperado (sem surpresas)
```

#### **Trade-off**

```
MILP Standard: Ótimo se previsão acerta, subótimo se erra
MILP Robusto:  Subótimo se previsão acerta, ótimo se erra
               Escolher quando: incerteza > 15%
```

---

### 5.2 Stochastic Programming (Programação Estocástica)

#### **Conceito**

Em vez de um valor de solar, usa **distribuição de probabilidade**:

$$\min_x \mathbb{E}_{u \sim P}[C(x, u)]$$

#### **Exemplo com Cenários**

```python
class MILPEstocástico:
    """MILP que minimiza custo ESPERADO em múltiplos cenários"""
    
    def __init__(self, microrrede, cenarios_solar, probabilidades):
        """
        cenarios_solar: [cenario1, cenario2, ..., cenarioN]
        probabilidades: [p1, p2, ..., pN] som = 1
        """
        self.cenarios = cenarios_solar
        self.probs = probabilidades
    
    def criar_modelo(self):
        modelo = LpProblem("Microrrede_Estocástico", LpMinimize)
        
        # Variáveis de 1º estágio (decisão aqui, agora)
        # P_diesel, P_bateria_charge (MESMAS em todos cenários)
        self.P_diesel_stage1 = [LpVariable(f"P_diesel_{t}", 0, 40) 
                               for t in range(1440)]
        
        # Variáveis de 2º estágio (decisão depois, quando cenário realiza)
        # P_rede_cenario_s_t (depende do cenário)
        self.P_rede = {}
        for s, cenario in enumerate(self.cenarios):
            self.P_rede[s] = [LpVariable(f"P_rede_{s}_{t}", 0, 200) 
                             for t in range(1440)]
        
        # Função objetivo: mín custo esperado
        custo_esperado = 0
        
        for s, (cenario, prob) in enumerate(zip(self.cenarios, self.probs)):
            for t in range(1440):
                # Custo de diesel (1º estágio, certo)
                custo_diesel = prob * self.P_diesel_stage1[t] * 0.40 / 60
                
                # Custo de rede (2º estágio, incerto)
                custo_rede = prob * self.P_rede[s][t] * 0.60 / 60
                
                custo_esperado += custo_diesel + custo_rede
        
        modelo += custo_esperado
        
        # Restrições para cada cenário
        for s, cenario in enumerate(self.cenarios):
            for t in range(1440):
                # Balanço em cada cenário
                modelo += (cenario[t] + self.P_diesel_stage1[t] + 
                          self.P_rede[s][t] >= self.demanda[t],
                          f"Balanço_cen{s}_{t}")
        
        return modelo

# Gerar cenários a partir de previsão
previsao_solar_central = np.array([...])  # Previsão média
desvio = 0.15  # ±15%

cenarios = [
    previsao_solar_central * (1 - desvio),  # Otimista
    previsao_solar_central * 1.0,           # Central
    previsao_solar_central * (1 + desvio),  # Pessimista
]

probs = [0.25, 0.5, 0.25]  # Mais peso ao central

milp_estoc = MILPEstocástico(microrrede, cenarios, probs)
modelo = milp_estoc.criar_modelo()
modelo.solve()
```

#### **Vantagens**

```
Stochastic vs Robusta:

Robusta:      "Funciona no PIOR caso"
              Muito conservadora, custo alto se tudo der bem
              
Estocástica:  "Minimiza custo MÉDIO"
              Mais eficiente em expectativa
              Pode falhar em cenários de cauda (raro)
              
Melhor para: Quando há risco aceitável (não é crítico)
```

---

## 6. MÉTODOS DISTRIBUÍDOS (Multi-Microrrede)

### 6.1 Game Theory / Coordenação Distribuída

#### **Cenário**

Múltiplas microrredes que podem **comprar/vender entre si** (não só rede).

```
MR1 (Excesso solar) ←→ MR2 (Falta)
MR1 (Falta diesel) ←→ MR3 (Excesso)
```

#### **Abordagem: Mercado Intra-Microrrede**

```python
class JogoMicrorredes:
    """Game-theoretic dispatch entre múltiplas microrredes"""
    
    def __init__(self, microrredes, num_iteracoes=10):
        self.microrredes = microrredes
        self.num_iter = num_iteracoes
        self.precos_internos = [0.50] * len(microrredes)  # Preço de "balcão"
    
    def otimizar_descentralizado(self):
        """
        Algoritmo de iteração: cada MR otimiza seu próprio custo
        dado os preços de balcão
        """
        
        for iteracao in range(self.num_iter):
            print(f"Iteração {iteracao+1}/{self.num_iter}")
            
            # Cada MR otimiza para si
            for i, mr in enumerate(self.microrredes):
                # Usar MILP com preço interno do balcão
                milp = MILPMicrorredes(mr)
                
                # Modificar função objetivo:
                # min custo_diesel + custo_rede 
                #     + preço_balcão × (P_venda - P_compra)
                
                # P_venda > 0: MR vende ao balcão (recebe)
                # P_compra > 0: MR compra do balcão (paga)
                
                milp.adicionar_restricoes()
                
                # Função objetivo modificada
                custo_com_balcao = (
                    milp.custo_total +  # Custo internal
                    self.precos_internos[i] * (milp.P_venda - milp.P_compra_balcao)
                )
                
                milp.modelo += custo_com_balcao
                milp.resolver()
                
                # Registrar oferta/demanda de balcão
                oferta_balcao = milp.P_venda.sum()
                demanda_balcao = milp.P_compra_balcao.sum()
            
            # Atualizar preços de balcão via lei da oferta/demanda
            excesso_oferta = sum([oferta_balcao for i in range(len(self.microrredes))])
            excesso_demanda = sum([demanda_balcao for i in range(len(self.microrredes))])
            
            # Se há excesso de oferta, preço cai
            # Se há excesso de demanda, preço sobe
            for i in range(len(self.microrredes)):
                if excesso_demanda > excesso_oferta:
                    self.precos_internos[i] *= 1.01  # +1%
                else:
                    self.precos_internos[i] *= 0.99  # -1%
            
            print(f"  Preços internos: {self.precos_internos}")
        
        # Na convergência:
        # - Preços refletem equilíbrio supply/demand
        # - Cada MR maximiza seu lucro
        # - Resultado é viável e "justo"

# Usar
mrs = [Ler_Objeto(Microrrede, i) for i in range(1, 6)]
jogo = JogoMicrorredes(mrs, num_iteracoes=20)
jogo.otimizar_descentralizado()

print("✓ Convergência: marketplace intra-microrrede equilibrado")
```

#### **Vantagens**

```
- Escalável para muitas MRs
- Distribuído (sem servidor central)
- Justo economicamente
- Adaptativo (preços mudam em tempo-real)

Desvantagens:
- Convergência não garantida
- Pode não atingir ótimo global
- Complexo de implementar/debugar
```

---

## 7. TABELA COMPARATIVA: TODAS MET ODOLOGIAS

| Metodologia               | Optimalidade  | Tempo | Implementação  | Parallelizável | Melhor Para |
|---------------------------|---------------|-------|----------------|----------------|-------------|
| **Heurística**            | 70-80%        | <1s   | ⭐⭐⭐        | ❌            | Tempo-real |
| **MILP**                  | 100% ✓        | 20s   | ⭐⭐          | ❌            | Planejamento day-ahead |
| **Prog. Dinâmica**        | 100% ✓        | 1-5s  | ⭐⭐          | ❌            | Poucas variáveis estado |
| **Algoritmo Genético**    | 85-95%        | 10-30s| ⭐⭐          | ✅            | Problemas combinatórios |
| **PSO**                   | 85-95%        | 5-15s | ⭐⭐⭐        | ✅            | Problemas contínuos |
| **Simul. Annealing**      | 80-90%        | 2-10s | ⭐⭐⭐        | ❌            | Pequenos espaços |
| **Deep RL**               | 80-90%        | 0.1ms*| ⭐             | ✅            | Controle tempo-real |
| **Neural Network**        | 90-95%        | 0.5ms*| ⭐⭐           | ✅            | Replicar MILP rápido |
| **Otim. Robusta**         | 95%**         | 30s   | ⭐             | ❌            | Com incertezas |
| **Stochastic**            | 97%**         | 40s   | ⭐             | ❌            | Análise de risco |
| **Game Theory**           | 90-98%***     | iterações | ⭐         | ✅            | Multi-microrrede |

*Após treinar
**vs MILP padrão
***Ao convergir

---

## 8. RECOMENDAÇÃO PARA SEU ARTIGO

### 8.1 Estrutura Sugerida (6-7 Análises)

```
Análise 1-4: Heurísticas (como agora)
Análise 5: MILP (como agora)

ADICIONE:
Análise 6: PSO (seu projeto JÁ tem código!)
Análise 7: Neural Network Supervisionada
           (treinada com MILP como teacher)
```

### 8.2 "Cascata de Métodos"

**Proposta de arquitetura prática:**

```
Fase 1: OFFLINE (primeiro dia)
  ├─ Rodar MILP (20 seg)
  └─ Treinar NN com resultado MILP (1 min)

Fase 2: OPERAÇÃO Normal (dias 2+)
  ├─ A cada 1h: atualizar previsão solar
  ├─ Rodar MILP para próximas 24h (20 seg) [MPC ligeiro]
  └─ Distribuir comando a cada minuto via NN
     (subst MILP por NN: 20seg → 1ms)

Fase 3: CONTROLE em tempo-real
  ├─ Se demanda muda: heurística adapta
  ├─ Se falha: fallback para MPC
  └─ Nada bloqueia (sempre há backup)
```

**Benefício**: 
- Otimalidade de MILP (18% economia)
- Velocidade de NN (<1ms)
- Robustez de heurística
- Sem pontos de falha únicos

---

## 9. CÓDIGO INTEGRADO: Comparação de 7 Métodos

```python
def comparacao_todas_metodologias(microrrede, metodos=['heuristica', 'milp', 'pso', 'ga', 'sa', 'nn', 'robusto']):
    """
    Executa todos os métodos sequencialmente
    Retorna tabela comparativa
    """
    
    resultados = {}
    tempos = {}
    
    import time
    
    # 1. Heurística
    if 'heuristica' in metodos:
        start = time.time()
        custo_h, despacho_h = analise_4(microrrede)
        tempos['Heurística'] = time.time() - start
        resultados['Heurística'] = custo_h
    
    # 2. MILP
    if 'milp' in metodos:
        start = time.time()
        custo_m, _, _ = analise_5_milp(microrrede)
        tempos['MILP'] = time.time() - start
        resultados['MILP'] = custo_m['Total']
    
    # 3. PSO (use seu código em otmizadores/pso.py)
    if 'pso' in metodos:
        start = time.time()
        # custo_p = sua_funcao_pso(microrrede)
        # tempos['PSO'] = time.time() - start
        # resultados['PSO'] = custo_p
        pass
    
    # 4. GA
    if 'ga' in metodos:
        start = time.time()
        ga = MicrorredGA(demanda, solar, custos, pop_size=50, geracao_max=30)
        _, custo_ga, _ = ga.otimizar()
        tempos['GA'] = time.time() - start
        resultados['GA'] = custo_ga
    
    # ... (outros)
    
    # Tabela final
    df_resultado = pd.DataFrame({
        'Metodologia': list(resultados.keys()),
        'Custo (R$)': list(resultados.values()),
        'Tempo (seg)': list(tempos.values()),
        'vs MILP': [(resultados[m] - resultados['MILP'])/resultados['MILP']*100 
                    for m in resultados.keys()]
    })
    
    return df_resultado.sort_values('Custo (R$)')
```

---

## 10. CONCLUSÃO: Qual Metodologia Escolher?

### **Quick Decision Tree**

```
┌─ Precisa de otimalidade garantida?
│  ├─ SIM → MILP ✓
│  └─ NÃO → Próxima pergunta
│
├─ Tempo-real (<1ms)?
│  ├─ SIM → Neural Network (treinada com MILP) ✓
│  └─ NÃO → Próxima pergunta
│
├─ Muita incerteza (>20%)?
│  ├─ SIM → Otimização Robusta ✓
│  └─ NÃO → Próxima pergunta
│
├─ Múltiplas microrredes?
│  ├─ SIM → Game Theory / Market ✓
│  └─ NÃO → Próxima pergunta
│
└─ Quad rática rapidez?
   ├─ SIM → PSO ✓
   └─ NÃO → MILP é default ✓
```

### **Recomendação Final para Seu Projeto**

```
IMPLEMENTAR:
✅ Análises 1-4: Heurísticas (já tem)
✅ Análise 5: MILP (já tem)
✅ Análise 6: PSO (tem código, só integrar)
✅ Análise 7: Neural Network com TensorFlow

FUTURA MELHORIA:
⭐ MPC (MILP a cada 1h)
⭐ Otimização Robusta (incertezas)
⭐ Multi-MR com mercado (se expandir)
```

Isso daria um artigo **COMPLETO e PROFUNDO**, cobrindo o estado da arte em otimização de microrredes.
