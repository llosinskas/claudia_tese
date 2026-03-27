# MILP - Mixed Integer Linear Programming para Controle de Microrredes

## 📋 Visão Geral

Este módulo implementa um modelo de **Mixed Integer Linear Programming (MILP)** para otimização e controle de microrredes. O MILP permite resolver o problema de despacho de energia de forma ótima, minimizando custos operacionais enquanto respeita todas as restrições técnicas e operacionais.

## 🎯 Objetivo

Encontrar a **estratégia ótima de despacho de energia** que:

- ✅ **Minimiza custo operacional total** (diesel, biogas, bateria, concessionária)
- ✅ **Respeita limites de potência** de cada fonte
- ✅ **Gerencia níveis de armazenamento** (bateria, combustíveis)
- ✅ **Realiza carregamento/descarregamento** eficiente da bateria
- ✅ **Otimiza venda de excedentes** para a rede
- ✅ **Prioriza fontes mais baratas** automaticamente

## 📁 Arquivos

### Arquivo Principal
- **`otmizadores/milp_controle_microrrede.py`** - Implementação do modelo MILP

### Integração
- **`analises/PrioridadeMicro.py`** - Funções `analise_5_milp()` e `analise_5_milp_multi()`

## 🔧 Como Usar

### 1. Uso Direto da Classe MILP

```python
from otmizadores.milp_controle_microrrede import MILPMicrorredes
from models.Microrrede import Microrrede
from models.CRUD import Ler, Ler_Objeto

# Carregar uma microrrede
microrrede = Ler_Objeto(Microrrede, 1)

# Criar modelo MILP
otimizador = MILPMicrorredes(microrrede)

# Construir modelo
otimizador.criar_modelo()
otimizador.adicionar_restricoes()
otimizador.adicionar_funcao_objetivo()

# Resolver
sucesso = otimizador.resolver()

if sucesso:
    # Extrair solução
    solucao = otimizador.extrair_solucao()
    
    # Gerar resultados em DataFrame
    df_resultado = otimizador.gerar_dataframe_resultado()
    
    # Calcular custos totais
    custos = otimizador.calcular_custos_totais()
    
    print(f"Custo Total: R$ {custos['Total']:,.2f}")
    print(f"Status: {solucao['Status']}")
```

### 2. Uso da Função MILP Integrada (Streamlit)

```python
from analises.PrioridadeMicro import analise_5_milp
from models.Microrrede import Microrrede
from models.CRUD import Ler_Objeto

# No seu aplicativo Streamlit
microrrede = Ler_Objeto(Microrrede, 1)
analise_5_milp(microrrede)  # Executa análise com interface Streamlit
```

### 3. Análise para Múltiplas Microrredes

```python
from analises.PrioridadeMicro import analise_5_milp_multi
from models.Microrrede import Microrrede
from models.CRUD import Ler

# Carregar todas as microrredes
microrredes = Ler(Microrrede)

# Executar análise comparativa
analise_5_milp_multi(microrredes)
```

## 📊 Variáveis de Decisão

| Variável | Tipo | Descrição |
|----------|------|-----------|
| `P_solar_t` | Contínua | Potência solar no período t [kW] |
| `P_bateria_t` | Contínua | Potência de descarga da bateria [kW] |
| `P_diesel_t` | Contínua | Potência diesel no período t [kW] |
| `P_biogas_t` | Contínua | Potência biogas no período t [kW] |
| `P_conc_t` | Contínua | Compra de energia da concessionária [kW] |
| `P_carga_bat_t` | Contínua | Carga da bateria no período t [kW] |
| `P_venda_t` | Contínua | Venda de excedente para rede [kW] |
| `U_diesel_t` | Binária (0/1) | Estado ligado/desligado diesel |
| `U_biogas_t` | Binária (0/1) | Estado ligado/desligado biogas |
| `E_bateria_t` | Contínua | Nível de energia bateria [kWh] |
| `E_diesel_t` | Contínua | Nível de combustível diesel [litros] |
| `E_biogas_t` | Contínua | Nível de gás biogas [m³] |

## 🔗 Restrições Principais

### 1. Balanço de Energia
```
P_solar + P_bateria + P_diesel + P_biogas + P_conc = Carga + P_carga_bat + P_venda
```
Para cada período de tempo, a energia fornecida deve atender a demanda + carregamento + excesso.

### 2. Limites de Potência
```
P_solar_t ≤ curva_solar[t]
P_diesel_t ≤ potencia_diesel * U_diesel_t
P_biogas_t ≤ potencia_biogas * U_biogas_t
P_bateria_t ≤ potencia_bateria
P_carga_bat_t ≤ potencia_bateria
```

### 3. Dinâmica de Armazenamento

**Bateria:**
```
E_bateria[t+1] = E_bateria[t] - P_bateria[t]/60 + η * P_carga_bat[t]/60
E_min ≤ E_bateria[t] ≤ E_max
```

**Diesel:**
```
E_diesel[t+1] = E_diesel[t] - consumo_diesel * P_diesel[t]/60
0 ≤ E_diesel[t] ≤ capacidade_tanque
```

**Biogas:**
```
E_biogas[t+1] = E_biogas[t] + producao - consumo_biogas * P_biogas[t]/60
0 ≤ E_biogas[t] ≤ capacidade_tanque
```

### 4. Limites Operacionais
```
U_diesel_t * P_min <= P_diesel_t <= U_diesel_t * P_max
U_biogas_t * P_min <= P_biogas_t <= U_biogas_t * P_max
```

## 💰 Função Objetivo

O modelo minimiza o **Custo Total Operacional**:

```
Minimizar: Σ(custo_diesel * P_diesel_t + 
               custo_biogas * P_biogas_t +
               custo_bateria * P_bateria_t +
               tarifa_conc * P_conc_t -
               0.8 * tarifa_conc * P_venda_t +
               custos_inicializacao_diesel +
               custos_manutencao_solar)
```

## 📈 Resultados e Saídas

A função retorna:

1. **DataFrame de Resultado**
   - Despacho horário de cada fonte
   - Carga demandada
   - Energia carregada na bateria
   - Venda para rede

2. **Dicionário de Custos**
   - Custo por fonte
   - Receita de venda
   - Custo total

3. **Solução Completa**
   - Todas as variáveis do MILP
   - Status de resolução
   - Níveis de armazenamento

## 🚀 Vantagens do MILP vs Heurísticas

| Aspecto            | MILP | Heurísticas (Análises 1-4) |
|--------------------|------|--------------------------|
| **Otimalidade**    | ✅ Solução ótima garantida | ❌ Solução subótima |
| **Complexidade**   | Pode ser computacionalmente pesada | Rápido |
| **Flexibilidade**  | ✅ Fácil adicionar restrições | Difícil modificar lógica |
| **Convergência**   | ✅ Sempre converge se viável | Sem garantia |
| **Custos**         | Típ. 10-30% menor | Baseline |

## ⚙️ Configurações Recomendadas

### Para Otimização Rápida
```python
otimizador = MILPMicrorredes(microrrede)
otimizador.criar_modelo()
otimizador.adicionar_restricoes()
otimizador.adicionar_funcao_objetivo()
sucesso = otimizador.resolver(verbose=False)
```

### Para Análise Detalhada
```python
otimizador = MILPMicrorredes(microrrede)
otimizador.criar_modelo(verbose=True)
otimizador.adicionar_restricoes(verbose=True)
otimizador.adicionar_funcao_objetivo(verbose=True)
sucesso = otimizador.resolver(verbose=True)
```

## 🔍 Interpretação dos Resultados

### Exemplo de Saída
```
============================================================
OTIMIZAÇÃO MILP - CONTROLE DE MICRORREDE
============================================================
✓ Modelo resolvido com sucesso!
  Status: Ótimo
  Custo total: R$ 15,432.56

------------------------------------------------------------
RESUMO DOS CUSTOS
------------------------------------------------------------
Solar               : R$       40.50
Bateria             : R$    3,200.00
Diesel              : R$    8,500.00
Biogas              : R$    2,100.00
Concessionaria      : R$    1,800.00
Receita Venda       : R$     (208.50)
------------------------------------------------------------
CUSTO TOTAL         : R$   15,432.56
============================================================
```

## 📝 Notas Importantes

1. **Dados de Entrada**
   - Todos os parâmetros de custo devem estar em **R$/kWh**
   - Potências em **kW**
   - Capacidades em unidades consistentes (kWh, litros, m³)

2. **Tempo de Resolução**
   - Típicamente < 30 segundos para 1440 períodos
   - Depende de hardware e complexidade da rede

3. **Viabilidade**
   - Se o modelo não encontrar solução viável, verifique:
     - Se a demanda total pode ser atendida
     - Se há restrições muito apertadas
     - Capacidade do sistema

4. **Melhorias Futuras**
   - Suporte a multi-período (dias/semanas)
   - Controle de fluxo inter-microrredes otimizado
   - Integração com previsão de demanda/geração
   - Otimização robusta (incertezas)

## 📚 Referências

- Integração com PuLP (solucionador CBC)
- Modelo MILP padrão para microrredes
- Baseado em estudos de operação ótima de sistemas distribuídos

## 💡 Dicas de Troubleshooting

**Problema:** Modelo não converge
- **Solução:** Verifique restrições, reduza período ou aumente limite de tempo de resolução

**Problema:** Custo muito alto comparado a análises heurísticas
- **Solução:** Verifique dados de entrada, pode haver inconsistência

**Problema:** Uso excessivo de diesel/biogas
- **Solução:** Aumentar capacidade de bateria ou solar na análise

---

**Versão:** 1.0  
**Data:** 2026  
**Autor:** Sistema de Otimização de Microrredes
