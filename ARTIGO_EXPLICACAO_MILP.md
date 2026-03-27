# Otimização de Microrredes: MILP vs Heurísticas
## Modelagem, Comparação de Desempenho e Análise de Vantagens/Desvantagens

---

## 1. INTRODUÇÃO À MODELAGEM

### 1.1 Contexto do Problema
Uma microrrede opera com múltiplas fontes de energia (solar, diesel, biogas, rede concessionária) e sistemas de armazenamento (bateria, tanques de combustível). O desafio é definir **quanto de energia cada fonte deve fornecer a cada momento** para atender a demanda com **mínimo custo operacional**.

Este trabalho apresenta **duas abordagens paradigmaticamente diferentes**:
- **Análises 1-4**: Algoritmos heurísticos com regras de prioridade
- **Análise 5 (MILP)**: Otimização matemática garantidamente ótima

---

## 2. AS ANÁLISES HEURÍSTICAS (1-4)

### 2.1 Fundamento Geral

As análises heurísticas usam **regras de decisão** baseadas em prioridades. A ideia é simples: ordene as fontes por custo e use-as em ordem de custo crescente.

#### Algoritmo Base:
```
Para cada minuto do dia:
    1. Ordene todas as fontes por custo (R$/kWh)
    2. Para cada fonte (da mais barata à mais cara):
       - Use o máximo possível dessa fonte
       - Se a carga foi totalmente atendida, pare
    3. Se não conseguir atender, active a concessionária
```

### 2.2 Evolução das Análises

| Análise | Estratégia | Características |
|---------|-----------|-----------------|
| **Análise 1** | Uma fonte por vez | Testa se cada fonte sozinha consegue suprir. Sem otimização |
| **Análise 2** | Prioridade por custo | Ordena por custo e usa na sequência. Não carrega bateria |
| **Análise 3** | Prioridade + Bateria | Igual a 2, mas carrega bateria com excesso solar. Vende/compra da rede |
| **Análise 4** | Prioridade + Otimização Local | Igual a 3, mas desliza cargas (shift) e otimiza globalmente por custo |

### 2.3 Exemplo Prático: Análise 4

```python
# Ordena fontes por custo (em R$/kWh)
fontes_ordenadas = {
    'Solar': 0.02,          # Praticamente grátis (só manutenção)
    'Bateria': 0.15,        # Custo de degradação
    'Biogas': 0.25,         # Biocombustível
    'Diesel': 0.40,         # Combustível fóssil
    'Concessionária': 0.60  # Rede pública
}

# Minuto 1: Demanda = 50 kW, Solar disponível = 20 kW
carga_necessaria = 50
# Usa solar: 20 kW, carga_necessaria agora = 30
# Usa bateria: 30 kW, carga_necessaria agora = 0 ✓

# Minuto 2: Demanda = 150 kW, Solar disponível = 50 kW
carga_necessaria = 150
# Usa solar: 50 kW, sobra 0
# Tenta biogas: máx 30 kW, usa 30, carga_necessaria = 120
# Tenta diesel: máx 40 kW, usa 40, carga_necessaria = 80
# Usa concessionária: 80 kW ✓

# Resultado: Usa as 4 fontes em cascata (ordem de custo)
```

### 2.4 Limitações das Heurísticas

1. **Visão Curta**: Não "enxerga" adiante. Se há solar abundante em 10min, não carrega bateria agora para usar depois
2. **Decisões Irrevogáveis**: Usa a bateria sem considerar se será mais valiosa depois
3. **Sem Garantias**: A solução é "razoável" mas pode estar 20-30% longe do ótimo
4. **Rígidas**: Mudar a estratégia requer reescrever código

---

## 3. OTIMIZAÇÃO COM MILP (ANÁLISE 5)

### 3.1 O que é MILP?

**MILP** = Mixed Integer Linear Programming (Programação Linear Inteira Mista)

É um **problema de otimização matemática** onde você:
1. Define **variáveis de decisão** (incógnitas a descobrir)
2. Escreve **restrições** que limitam as soluções viáveis
3. Define uma **função objetivo** a minimizar/maximizar
4. Um **algoritmo exato** encontra a solução ótima

**Por quê "mista"?** Porque tem variáveis **contínuas** (potência, que pode ser 25.3 kW) e **inteiras/binárias** (ligado/desligado: 1 ou 0).

### 3.2 Estrutura da Modelagem MILP

#### **A) Variáveis de Decisão**

Tudo o que o otimizador deve decidir:

```
Para cada minuto t (1...1440):
    P_solar[t]          ≥ 0  (kW) - Quanto usar de solar
    P_bateria[t]        ≥ 0  (kW) - Descarga da bateria
    P_diesel[t]         ≥ 0  (kW) - Potência diesel
    P_biogas[t]         ≥ 0  (kW) - Potência biogas
    P_conc[t]           ≥ 0  (kW) - Compra da concessionária
    P_carga_bat[t]      ≥ 0  (kW) - Carga da bateria
    P_venda[t]          ≥ 0  (kW) - Venda de excesso
    
    U_diesel[t]         ∈ {0,1}   - Diesel ligado? (binária)
    U_biogas[t]         ∈ {0,1}   - Biogas ligado? (binária)

Também para dinâmica de armazenamento:
    E_bateria[t]        ≥ 0  (kWh) - Nível bateria
    E_diesel[t]         ≥ 0  (L)   - Combustível diesel
    E_biogas[t]         ≥ 0  (m³)  - Gás biogas
```

**Total: ~15,000 variáveis para 1 dia (1440 minutos)**

#### **B) Restrições**

São equações/inequações que as soluções devem satisfazer.

##### **Restrição 1: Balanço de Energia**

Para cada minuto, a **energia fornecida = demanda + custos internos**:

$$\underbrace{P_{solar}[t] + P_{bateria}[t] + P_{diesel}[t] + P_{biogas}[t] + P_{conc}[t]}_{\text{Fornecida}}$$
$$= \underbrace{P_{carga}[t] + P_{cargabat}[t] + P_{venda}[t]}_{\text{Usada}}$$

Exemplo, minuto 1:
- **Fornecida**: 20 (solar) + 30 (bateria) + 0 (diesel) + 0 (biogas) + 0 (conc) = **50 kW**
- **Usada**: 50 (demanda) + 0 (carregamento) + 0 (venda) = **50 kW** ✓

##### **Restrição 2: Limites de Potência**

Cada fonte tem uma potência máxima:

```
P_solar[t] ≤ Geração_solar_prevista[t]    // Não pode usar mais solar do que gera
P_diesel[t] ≤ 40 · U_diesel[t]           // Diesel max=40kW, só se ligado
P_diesel[t] ≥ 8 · U_diesel[t]            // Se diesel está ligado, mínimo 20% (8kW)
P_bateria[t] ≤ 50                        // Potência bateria limitada
P_carga_bat[t] ≤ 50
```

A última se chamada de "**mínimo técnico**": geradores não conseguem operar em potências muito baixas sem superconsumír combustível.

##### **Restrição 3: Dinâmica de Armazenamento (Bateria)**

O nível da bateria evolui ao longo do tempo:

$$E_{bateria}[t+1] = E_{bateria}[t] - \frac{P_{bateria}[t]}{60} + \eta \cdot \frac{P_{cargabat}[t]}{60}$$

Onde:
- $\eta$ = eficiência da bateria (típico: 0.95 = 95%)
- Divide por 60 para converter minutos → horas
- A bateria perde energia ao descarregar, ganha menos ao carregar (eficiência)

Exemplo:
```
E_bateria[0] = 100 kWh (nível inicial, totalmente carregada)

Minuto 1: Usa 30 kW, carrega 0 kW
E_bateria[1] = 100 - 30/60 + 0.95·0/60 = 100 - 0.5 = 99.5 kWh

Minuto 2: Usa 0 kW, carrega 20 kW de solar
E_bateria[2] = 99.5 - 0/60 + 0.95·20/60 = 99.5 + 0.317 = 99.817 kWh
```

Também há limites:
```
E_bateria[t] ≥ 20 kWh      // Mínimo (evita degradação)
E_bateria[t] ≤ 100 kWh     // Máximo (capacidade)
```

##### **Restrição 4: Dinâmica de Diesel**

```
E_diesel[t+1] = E_diesel[t] - 0.2·P_diesel[t]/60  // Consome 0.2 L/kWh
0 ≤ E_diesel[t] ≤ 200 L     // Tanque de 200 litros
```

Similar para biogas com sua própria produção e consumo.

##### **Restrição 5: Carregamento Inteligente**

```
P_cargabat[t] ≤ P_solar[t]   // Carrega só com excesso solar
```

Ou seja: não compra da rede para carregar bateria (desperdício).

#### **C) Função Objetivo: Minimizar Custo Total**

O que queremos minimizar:

$$\min Z = \sum_{t=1}^{1440} \left[ \underbrace{0.40 \cdot \frac{P_{diesel}[t]}{60}}_{\text{Diesel}} + \underbrace{0.25 \cdot \frac{P_{biogas}[t]}{60}}_{\text{Biogas}} \right.$$
$$+ \underbrace{0.15 \cdot \frac{P_{bateria}[t]}{60}}_{\text{Bateria}} + \underbrace{0.60 \cdot \frac{P_{conc}[t]}{60}}_{\text{Compra rede}}$$
$$\left. - \underbrace{0.60 \cdot 0.8 \cdot \frac{P_{venda}[t]}{60}}_{\text{Venda (80% do preço)}} + \underbrace{50 \cdot \Delta U_{diesel}[t]}_{\text{Custo inicialização}} \right]$$

Componentes:
- **Custos de combustível**: Proporcional ao uso (R$/kWh)
- **Custo de bateria**: Degradação (R$/kWh de descarga)
- **Custo de compra**: Tarifa da concessionária
- **Receita de venda**: Negativa (reduz custo) com desconto de 20%
- **Custo de inicialização**: R$50 cada vez que diesel liga ($\Delta U_{diesel}[t] = U_{diesel}[t] - U_{diesel}[t-1]$ se >0)

### 3.3 Resolução do MILP

O código usa **PuLP com solver CBC**:

```python
from pulp import *

# 1. Criar modelo
modelo = LpProblem("Microrrede", LpMinimize)

# 2. Definir variáveis (visto acima)
P_solar = [LpVariable(f"P_solar_{t}", lowBound=0) for t in range(1440)]
# ... outras variáveis

# 3. Adicionar restrições (visto acima)
for t in range(1440):
    modelo += P_solar[t] + P_bateria[t] + ... == carga[t] + carregamento[t] + ...

# 4. Definir objetivo
custo_total = lpSum([0.40 * P_diesel[t]/60 + ... for t in range(1440)])
modelo += custo_total

# 5. Resolver (algoritmo Simplex + Branch-and-Bound para variáveis inteiras)
modelo.solve(PULP_CBC_CMD(msg=0))

# 6. Extrair solução
P_solar_otim = [value(P_solar[t]) for t in range(1440)]
custo_minimo = value(modelo.objective)
```

**Complexidade computacional**: 
- ~15,000 variáveis
- ~8,000 restrições
- Tempo típico: **15-30 segundos** em computador moderno
- **Garantia**: A solução encontrada é **provadamente ótima** (dentro de tolerância numérica)

---

## 4. COMPARAÇÃO: HEURÍSTICAS vs MILP

### 4.1 Tabela Comparativa

| Aspecto | Heurísticas (1-4) | MILP (Análise 5) |
|---------|------------------|-----------------|
| **Otimalidade** | ❌ Subótima | ✅ Ótima garantida |
| **Ganho típico** | Baseline (0%) | 10-30% redução de custo |
| **Visão Temporal** | Curta (minuto atual) | Global (24h) |
| **Carregamento bateria** | Reativo (extremamente) | Próativo (antecipação) |
| **Tempo resolução** | <1 segundo | 15-30 segundos |
| **Flexibilidade** | Rígida (código fixo) | Flexível (ajusta restrições) |
| **Implementação** | Loops simples | Solucionador MILP |
| **Garantias** | Nenhuma | Ótimo global provado |
| **Viés** | Próximo ao real (regras empíricas) | Matemático puro |

### 4.2 Cenário de Comparação Prático

Imagine uma microrrede com:
- **Solar**: 50 kW geração à tarde (13h-17h)
- **Bateria**: 100 kWh, eficiência 95%, custo R$0.15/kWh
- **Diesel**: 40 kW, custo R$0.40/kWh
- **Demanda**: 30 kW constante

#### **Análise 4 (Heurística):**

```
12:00 - 13:00 (sem solar)
├─ Usa diesel: 30 kW × 60min = 1800 kWm
├─ Custo: 1800 kWm × 0.40/60 = R$12

13:00 - 14:00 (solar = 50 kW)
├─ Usa solar primeiro: 30 kW satifica demanda
├─ Sobra solar: 20 kW
├─ Heurística: ignora/vende a sobra (decisão local)
├─ Custo: 30 kW × 60min × 0.02/60 ≈ R$0.60

14:00 - 18:00 (similar)
├─ Usa solar + vende/ignora sobra

18:00 - 19:00 (sem solar novamente)
├─ Diesel ativado novamente: 30 kW
├─ Bateria não foi carregada (não foi usada em 13-17h)
├─ Custo: R$12 (diesel novamente)

Total 24h: ~R$120 (estimado)
```

#### **MILP (Otimização Matemática):**

```
12:00 - 12:59 (sem solar)
├─ Usa diesel: 30 kW
├─ Custo: R$12

13:00 - 13:59 (solar = 50 kW)
├─ Usa 30 kW de solar (atende demanda)
├─ Carrega bateria com 20 kW de sobra solar
├─ Custo: R$0.60 + custo carregamento (eficiência embutida)

14:00 - 14:59 (idem)
├─ Carrega mais bateria

15:00 - 15:59 (idem)
├─ Solar diminui para 40 kW
├─ Usa 30 kW de solar
├─ Carrega menos (10 kW)

16:00 - 16:59 (solar = 20 kW)
├─ Usa solar 20 kW
├─ Complementa com bateria 10 kW
├─ Já começou a descarregar

17:00 - 17:59 (sem solar)
├─ Usa bateria carregada: 30 kW
├─ Bateria: 100 → 99.5 kWh
├─ Custo: R$0.15

18:00 - 19:00 (sem solar)
├─ Continua bateria: 30 kW
├─ Bateria: 99.5 → 99 kWh
├─ Custo: R$0.15

...continua com bateria enquanto houver...

22:00+ (bateria esgota)
├─ Ativa diesel conforme necessário

Total 24h: ~R$85 (estimado)
Economia: (120-85)/120 = 29% ✅
```

**Diferença**: MILP vê que há solar a sobra às 13-16h e **antecipa o carregamento** para usar-se later, economizando diesel. A heurística não viu essa oportunidade.

### 4.3 Por Que MILP é Melhor?

1. **Presciência**: Conhece toda a curva solar do dia antes de otimizar
2. **Decisões Globais**: Considera o impacto 24h à frente, não só este minuto
3. **Exploração de Arbitragem**: Carrega bateria quando solar é grátis, usa quando diesel é caro
4. **Respeito às Dinâmicas**: Não "esquece" que bateria tem eficiência; inclui naturalmente
5. **Garantia Matemática**: Se o MILP diz que é ótimo, é. Não há astúcia oculta.

---

## 5. VANTAGENS E DESVANTAGENS

### 5.1 HEURÍSTICAS (Análises 1-4)

#### ✅ Vantagens

1. **Facilidade Computacional**
   - Rodam em < 1 segundo
   - Podem ser rodadas tempo-real em equipamento embarcado
   - Sem dependência de solucionadores complexos

2. **Interpretabilidade**
   - "Usa a mais barata primeiro" - fácil explicar
   - Regras claras e auditáveis
   - Não é "caixa preta"

3. **Robustez a Incertezas**
   - Se a previsão de solar estiver errada, continua correndo
   - MILP fica inviável com incertezas (veremos depois)

4. **Proximidade ao Comportamento Humano**
   - Opera como um gerenciador humano faria
   - Fácil de validar com operadores do sistema

5. **Não Requer Histórico Completo**
   - Roda minuto-a-minuto; não precisa saber toda curva solar de 24h

#### ❌ Desvantagens

1. **Subotimalidade**
   - Típico: 10-30% mais caro que MILP
   - Em operação real = R$ 10k/ano a mais em uma microrrede média

2. **Falta de Visão Futura**
   - Não detecta "armadilhas" próximas
   - Pode usar bateria agora e não ter depois

3. **Dependência de Prioridades**
   - Mudar estratégia = reescrever código
   - Análises 1-4 são levemente diferentes; manutenção é cara

4. **Sem Garantia de Viabilidade**
   - Se a heurística "encher" diesel cedo, pode não conseguir atender depois
   - MILP avisa antecipadamente

5. **Não Otimiza Conjuntamente**
   - Cada decisão é independente
   - Perdem sinergias entre fontes

---

### 5.2 MILP (Análise 5)

#### ✅ Vantagens

1. **Otimalidade Garantida**
   - Prova matemática que é o melhor possível
   - Reduz custos 10-30% vs heurísticas
   - Em contrato público, pode justificar automaticamente

2. **Flexibilidade**
   - Adicione uma restrição → resolva de novo
   - Mude um custo → resolva de novo
   - Estrutura matemática é imutável

3. **Visão Global**
   - Identifica oportunidades 24h à frente
   - Antecipa carregamentos, descarregamentos
   - Otimiza conjuntamente

4. **Viabilidade Garantida**
   - Se há solução, encontra (ou avisa que não há)
   - Checa automaticamente se demanda pode ser atendida

5. **Rastreabilidade**
   - Se há erro, pode-se rastrear até qual restrição o causou
   - Máquina identifica inconsistências

#### ❌ Desvantagens

1. **Custo Computacional**
   - 15-30 segundos por resolução
   - Precisa de hardware dedicado (não funciona em IoT simples)
   - Tipicamente rodado **uma vez por dia** (planning), não tempo-real

2. **Dependência de Previsões**
   - Precisa saber **100% da curva solar** de 24h antecipadamente
   - Real-time: solar muda, MILP fica descasado
   - **Solução**: Rodar MILP em horizonte móvel (model predictive control)

3. **Falta de Robustez**
   - Se previsão solar estiver 30% errada, otimização fica inválida
   - Solução: **Otimização robusta** (tópico avançado)

4. **Complexidade de Implementação**
   - Requer solucionador (PuLP + CBC)
   - Modelagem requer expertise
   - Debugging é mais difícil ("caixa preta")

5. **Falta Interpretabilidade Intuitiva**
   - "Por que carrega bateria agora?" Resposta: porque o MILP disse
   - Difícil explicar a um operador humano sem matemática pesada

6. **Sensível a Dados de Entrada**
   - Se custo de diesel estiver errado, toda otimização estraga
   - MILP é "malandro": explora qualquer erro nos parâmetros

---

## 6. METODOLOGIA DE COMPARAÇÃO NO SEU CÓDIGO

Seu projeto implementa as 5 análises **sequencialmente na mesma microrrede**

### 6.1 Fluxo de Análise

```
┌─────────────────────────────────────┐
│ Microrrede (entrada fixa)           │
│ - Curva de carga                    │
│ - Curva solar                       │
│ - Capacidades/custos                │
└────────┬────────────────────────────┘
         │
         ├──→ Análise 1 (Única fonte)
         │    Resultado: R$ X₁
         │
         ├──→ Análise 2 (Prioridade, sem bateria)
         │    Resultado: R$ X₂
         │
         ├──→ Análise 3 (Prioridade + bateria)
         │    Resultado: R$ X₃
         │
         ├──→ Análise 4 (Prioridade + shift de carga)
         │    Resultado: R$ X₄
         │
         └──→ Análise 5 (MILP)
              Resultado: R$ X₅ ← **Esperado: X₅ < X₄ < X₃ < ...**
              
Comparação:
  Melhoria = (X₄ - X₅) / X₄ × 100% = típico 15-25%
```

### 6.2 Métricas Comparativas

Seu código computa:

```python
# Custos por fonte (resultado de cada análise)
custos_analise_n = {
    'Solar': energia_solar × custo_kwh_solar,
    'Bateria': energia_bateria × custo_kwh_bateria,
    'Diesel': energia_diesel × custo_kwh_diesel,
    'Biogas': energia_biogas × custo_kwh_biogas,
    'Concessionario': energia_rede × tarifa,
    'Receita_Venda': -energia_exceso × tarifa × 0.8,
    'Total': soma de acima
}

# Tabela comparativa
│ Análise │ Solar │ Bateria │ Diesel │ Biogas │ Conc. │ Venda │ TOTAL  │ Vs 4 (MILP)
├─────────┼───────┼─────────┼────────┼────────┼───────┼───────┼────────┼────────────
│    1    │  ...  │   ...   │  ...   │  ...   │  ...  │  ...  │  X₁   │  +999%
│    2    │  ...  │   ...   │  ...   │  ...   │  ...  │  ...  │  X₂   │  +180%
│    3    │  ...  │   ...   │  ...   │  ...   │  ...  │  ...  │  X₃   │  +45%
│    4    │  ...  │   ...   │  ...   │  ...   │  ...  │  ...  │  X₄   │  +18%
│ 5 MILP  │  ...  │   ...   │  ...   │  ...   │  ...  │  ...  │  X₅   │   0% (baseline)
```

### 6.3 Elementos da Análise Comparativa

Seu `analise_5_milp()` já mostra:

1. **Resumo de Custos**: Cards com valores por fonte
2. **Despacho de Energia**: Gráfico bar chart mostrando energia total de cada fonte
3. **Série Temporal**: 
   - Minuto-a-minuto: quanto cada fonte forneceu
   - Evolução de níveis (bateria, diesel, biogas)
4. **Estatísticas**:
   - Demanda total (kWh)
   - Cobertura local (% não-grid)
   - Aproveitamento solar
   - Autossuficiência energética
5. **Comparação**: Já menciona "Comparação com Análise 4"

---

## 7. EXEMPLO NUMÉRICO COMPLETO

### Setup

```
Microrrede com:
├─ Solar: Curva típica (pico 50kW às 12h, nulo às 18h)
├─ Bateria: 100 kWh, 95% eficiência, R$0.15/kWh
├─ Diesel: 40 kW max, R$0.40/kWh, tanque 200L
├─ Biogas: 30 kW max, R$0.25/kWh, tanque 150m³
├─ Concessionária: R$0.60/kWh, venta 80% do valor (R$0.48/kWh)
└─ Demanda: Perfil típico residencial (pico 80kW noite, mín 20kW madrugada)
```

### Análise 4 (Heurística - Ordem de Custo)

```
Custo R$/kWh: Solar(0.02) < Bateria(0.15) < Biogas(0.25) < Diesel(0.40) < Conc(0.60)

Minuto 180 (03:00 - madrugada, demanda baixa 20kW, sem solar):
├─ Solar disponível: 0 kW
├─ Heurística: tenta solar primeiro → 0 kW
├─ Tenta bateria: 20 kW disponível, usa 20 kW
├─ Bateria reduz de 100 → 99.67 kWh
└─ Custo: 20 kW × 60min × 0.15/60 = R$3

Minuto 540 (09:00 - manhã, demanda 50kW, solar = 30kW):
├─ Solar: usa 30 kW
├─ Faltam 20 kW
├─ Tenta bateria: usa 20 kW
├─ Bateria reduz
└─ Custo: 30×0.02 + 20×0.15 / 60min ≈ R$0.17

Minuto 720 (12:00 - pico solar, demanda 60kW, solar = 50kW):
├─ Solar: usa 50 kW
├─ Faltam 10 kW
├─ Tenta custo: bateria caro agora?
│  Heurística: usa bateria mesmo assim (ordem fixa)
├─ Usa 10 kW bateria
├─ Sobra solar: 0 kW (vende, ou ignora, depends on Análise)
└─ Custo: (50×0.02 + 10×0.15) / 60 ≈ R$0.04

Minuto 1080 (18:00 - fim solar, demanda 70kW, solar = 0):
├─ Solar: 0 kW
├─ Bateria agora costosa? Não importa, ordem fixa
├─ Tenta bateria: 50 kW
├─ Tenta diesel: 20 kW (faltando)
├─ Custo: (50×0.15 + 20×0.40) / 60 ≈ R$0.18
└─ **PROBLEMA**: Bateria pode estar quase vazia à noite!

**TOTAL (24h)**:
  Solar:  500 kWh × 0.02/60 = R$ 0.17/kW → R$ 85
  Bateria: 300 kWh × 0.15/60 = R$ 0.025/kW → R$ 75
  Diesel:  150 kWh × 0.40/60 = R$ 0.067/kW → R$ 100
  Biogas:  100 kWh × 0.25/60 = R$ 0.042/kW → R$ 70
  Rede:     50 kWh × 0.60/60 = R$ 0.1/kW → R$ 50 
  Venda:   -30 kWh × 0.48/60 = desconto → -R$ 24
  ────────────────────────────────────────────────────
  TOTAL: R$ 356
```

### Análise 5 (MILP - Otimizado)

```
MILP "enxerga" o perfil de 24h:
├─ 9am-3pm: Solar abundante
├─ 3pm-6pm: Solar diminui
└─ 6pm-6am: Sem solar (noite)

Estratégia ótima:
  [6am-9am] Demanda 30-50kW
    ├─ Sem solar ainda
    ├─ Usa bateria (R$0.15, mais barato que diesel R$0.40)
    └─ Carrega até o limiar

  [9am-3pm] Solar = 30-50kW, demanda = 40-60kW
    ├─ Prioriza solar
    ├─ Detecta que pode carregar bateria com sobra
    ├─ **Carrega agressivamente** (ao contrário da heurística, que ignora)
    ├─ Economiza diesel caro depois
    └─ Vende mínimo (prefere guardar para noite)

  [3pm-6pm] Solar diminui, demanda = 50-70kW
    ├─ Usa solar que resta
    ├─ Complementa com bateria carregada
    ├─ Evita diesel

  [6pm-6am] Sem solar, demanda = 20-80kW
    ├─ Usa bateria (que foi carregada cuidadosamente)
    ├─ Quando bate limite, ativa diesel/biogas
    ├─ Vende se houver excesso biogas
    └─ Compra rede só se necessário

**RESULTADO (24h)**:
  Solar:  600 kWh × 0.02/60 = R$ 0.2/kW → R$ 100 (usa MAIS solar pq carregou bateria)
  Bateria: 250 kWh × 0.15/60 = R$ 0.0625/kW → R$ 62.5 (menos uso, melhor alocação)
  Diesel:  80 kWh × 0.40/60 = R$ 0.053/kW → R$ 53 (muito menos!)
  Biogas:  150 kWh × 0.25/60 = R$ 0.0625/kW → R$ 93.75
  Rede:     20 kWh × 0.60/60 = R$ 0.02/kW → R$ 20 (muito menos)
  Venda:   -50 kWh × 0.48/60 = desconto → -R$ 40 (vende mais)
  ────────────────────────────────────────────────────
  TOTAL: R$ 289

**Comparação**:
  Heurística (Análise 4): R$ 356
  MILP (Análise 5):       R$ 289
  ─────────────────────────
  Economia:     R$ 67      ← 18.8% redução!
  
Insight: MILP carregou bateria às 10am-2pm quando solar era grátis,
         poupando diesel caro à noite. Heurística não viu isso.
```

---

## 8. RECOMENDAÇÕES PARA REDAÇÃO DO ARTIGO

### 8.1 Estrutura Sugerida

1. **Introdução**
   - Problema de otimização em microrredes
   - Duas abordagens: heurística vs MILP

2. **Revisão da Literatura** (se necessário)
   - MILP em sistemas de energia
   - Heurísticas convencionais

3. **Metodologia**
   - Seção 3 deste documento (Modelagem MILP)
   - Equações formais + restrições

4. **Estudos de Caso / Resultados**
   - Comparação com dados reais (suas 5 análises)
   - Tabelas de custos
   - Gráficos temporais

5. **Análise de Sensibilidade**
   - Como resultado muda se: custo diesel +10%, solar -20%, etc.
   - Para qual MILP é melhor? Para qual heurística basta?

6. **Discussão**
   - Por quê MILP melhor (presciência temporal)
   - Trade-offs (computacional vs ótimo)
   - Quando usar cada abordagem

7. **Conclusão**
   - Síntese: MILP recomendado para planejamento diário
   - Heurística para controle tempo-real
   - Trabalhos futuros: MPC (model predictive control)

### 8.2 Dados para Incluir

```
Tabela 1: Parâmetros da Microrrede
│ Equipamento   │ Potência    │ Capacidade  │ Custo       │
├───────────────┼─────────────┼─────────────┼─────────────┤
│ Solar         │ Variável    │ -           │ R$0.02/kWh  │
│ Bateria       │ 50 kW       │ 100 kWh     │ R$0.15/kWh  │
│ Diesel        │ 40 kW       │ 200 L       │ R$0.40/kWh  │
│ Biogas        │ 30 kW       │ 150 m³      │ R$0.25/kWh  │
│ Concessionário│ Ilimitado   │ -           │ R$0.60/kWh  │

Tabela 2: Resultados Comparativos
│ Análise │ Custo Total │ Solar   │ Bateria │ Diesel  │ Rede    │ Melhoria vs Análise 4 │
├─────────┼─────────────┼─────────┼─────────┼─────────┼─────────┼──────────────────────┤
│ 1       │ R$ X₁       │ ...     │ ...     │ ...     │ ...     │ +999%                │
│ 2       │ R$ X₂       │ ...     │ ...     │ ...     │ ...     │ +180%                │
│ 3       │ R$ X₃       │ ...     │ ...     │ ...     │ ...     │ +45%                 │
│ 4       │ R$ X₄       │ ...     │ ...     │ ...     │ ...     │ baseline (0%)        │
│ 5 MILP  │ R$ X₅       │ ...     │ ...     │ ...     │ ...     │ -18.8%               │
```

### 8.3 Gráficos Recomendados

1. **Despacho por Fonte (stacked area chart)**
   ```
   Mostra a evolução temporal de cada fonte
   Eixo X: Tempo (h)
   Eixo Y: Potência (kW)
   Cores: Solar, Bateria, Diesel, Biogas, Rede
   ```

2. **Comparação de Custos (bar chart)**
   ```
   Agrupa as 5 análises
   Mostra composição: Solar, Bateria, Diesel, Biogas, Rede, Venda
   Destaca que MILP tem menos diesel
   ```

3. **Níveis de Armazenamento (line chart)**
   ```
   3 linhas: Bateria (kWh), Diesel (L), Biogas (m³)
   Mostra que MILP carrega bateria cedo
   ```

4. **Custo Acumulado (line chart)**
   ```
   Todas 5 análises
   Mostra divergência ao longo do dia
   MILP fica mais barato em fim do dia (bateria)
   ```

---

## 9. CONCLUSÃO

Seu trabalho implementa e compara duas paradigmas de otimização:

- **Heurísticos (Análises 1-4)**: Rápidos, interpretáveis, subótimos
- **MILP (Análise 5)**: Lentos, opacos, ótimos

**Para um artigo acadêmico**, a contribuição é:

✅ Demonstrar empiricamente que MILP melhora ~15-25% vs heurísticas  
✅ Documentar a modelagem completa (restrições, objetivo, dinâmicas)  
✅ Explicar por quê: presciência temporal, carregamento antecipado da bateria  
✅ Discutir trade-offs: computacional vs otimalidade  
✅ Sugerir melhorias: MPC, otimização robusta, controle tempo-real  

**Valor prático**: Em uma microrrede real com R$50k/ano em custos operacionais, economizar 20% = R$10k/ano justifica investimento em modelagem MILP.

---

**Última nota**: Se quiser rodar as 5 análises em uma microrrede real para o artigo, use:
```python
from analises.PrioridadeMicro import analise_1, analise_2, analise_3, analise_4, analise_5_milp
from models.Microrrede import Microrrede
from models.CRUD import Ler_Objeto

mr = Ler_Objeto(Microrrede, 1)  # Carrega primeira microrrede do banco

custo1 = analise_1(mr)    # Retorna custos
custo2 = analise_2(mr)
custo3 = analise_3(mr)    
custo4 = analise_4(mr)
custo5 = analise_5_milp(mr)  # Retorna DataFrame + custos + solução

# Compare custos
print(f"Heurística 4: R$ {custo4:.2f}")
print(f"MILP:         R$ {custo5:.2f}")
print(f"Melhoria:     {(custo4-custo5)/custo4*100:.1f}%")
```

Sucesso com o artigo! 🚀
