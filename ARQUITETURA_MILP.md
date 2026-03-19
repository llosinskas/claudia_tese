# Arquitetura - MILP para Microrredes

## 📊 Fluxo de Dados e Integração

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BANCO DE DADOS (SQLAlchemy)                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Microrrede → Solar, Diesel, Biogas, Bateria, Concessionária      │   │
│  │ Carga → CargaFixa (com prioridades 1-4)                          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────────────────────┘
                 │
                 ├─► GeradorCurvaCarga │ GerarSolar 
                 │   (1440 pontos/dia)
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              CLASSE MILPMicrorredes (Novo Módulo)                       │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ 1. criar_modelo()              (Cria variáveis de decisão)       │   │
│  │    - P_solar, P_diesel, ..., U_diesel (binária), E_bateria       │   │
│  │                                                                  │   │
│  │ 2. adicionar_restricoes()      (Restrições técnicas)             │   │
│  │    - Balanço de energia                                          │   │
│  │    - Limites de potência                                         │   │
│  │    - Dinâmica de armazenamento                                   │   │
│  │    - Prioridades de carregamento                                 │   │
│  │                                                                  │   │
│  │ 3. adicionar_funcao_objetivo() (Minimiza custo)                  │   │
│  │    - Custo diesel + biogas + bateria + concessionária            │   │
│  │    - Menos receita de venda                                      │   │
│  │                                                                  │   │
│  │ 4. resolver()                  (Usa PuLP + CBC solver)           │   │
│  │    - Retorna status ótimo/viável/infeasível                      │   │
│  │                                                                  │   │
│  │ 5. extrair_solucao()           (Extrai variáveis)                │   │
│  │    - Despacho por período + níveis de armazenamento              │   │
│  │    - Status de resolução                                         │   │ 
│  │                                                                  │   │
│  │ 6. gerar_dataframe_resultado() (Formata como pandas.DataFrame)   │   │
│  │    - Colunas: Solar, Bateria, Diesel, Biogas, Concessionária     │   │
│  │    - Linhas: 1440 períodos do dia                                │   │
│  │                                                                  │   │
│  │ 7. calcular_custos_totais()    (Resumo financeiro)               │   │
│  │    - Custo por fonte + custo total                               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────────────────────┘
                  │
              ┌───┴────────────────────────────────────────┐
              │                                            │
              ▼                                            ▼
    ┌──────────────────────────┐            ┌──────────────────────────┐
    │  analise_milp()          │            │ analise_5_milp()         │
    │  (Função wrapper)        │            │ (Integração Streamlit)   │
    │                          │            │                          │
    │  - Chama classe          │            │ - Exibe interface        │
    │  - Trata erros           │            │ - Gráficos interativos   │
    │  - Retorna dict          │            │ - Tabelas comparativas   │
    └──────────────────────────┘            │ - Métricas em tempo real │
                                            │ - Download de dados      │
                                            └──────────────────────────┘
                                                    │
                                                    ▼
                                           ┌──────────────────────────┐
                                           │   Streamlit Dashboard    │
                                           │   (Home.py / pages/...)  │
                                           │                          │
                                           │  📊 Análises 1-5         │
                                           │  📈 Gráficos             │
                                           │  📋 Relatórios           │
                                           └──────────────────────────┘
```

## 🔀 Integração com Análises Existentes

```
                      ┌─────────────────────────────┐
                      │  PrioridadeMicro.py         │
                      ├─────────────────────────────┤
                      │ Análise 1: Heurística       │
                      │ (Carga simples da rede)     │
                      │                             │
                      │ Análise 2: Heurística       │
                      │ (Prioriza fontes baratas)   │
                      │                             │
                      │ Análise 3: Heurística       │
                      │ (Com deslizamento de carga) │
                      │                             │
                      │ Análise 4: Heurística       │
                      │ (Otimização local)          │
                      │                             │
          ┌──────────►│ Análise 5: ⭐ MILP NOVO   │◄────────┐
          │           │ (Otimização Global Ótima)   │       │
          │           └─────────────────────────────┘       │
          │                                                 │
      Importação       Cada análise é independente      Pode comparar
   do novo módulo      Usa mesma base de dados         resultados
                       Mesmos objetos Microrrede
```

## 🔧 Componentes do MILP

```
┌──────────────────────────────────────────────────────────────────┐
│                    SOLVER MILP (CBC via PuLP)                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Entrada:                                                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ • Variáveis: 1440*8 = ~11,500 contínuas + ~2,880 binárias  │  │
│  │ • Restrições: 1440*8 + dinâmica = ~12,000                  │  │
│  │ • Função objetivo: Linear em todas as variáveis            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Processamento:                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CBC Solver (Open-Source)                                   │  │
│  │ • Relaxação LP → Branch & Cut → Solução Inteira            │  │
│  │ • Tempo típico: 10-30 segundos                             │  │
│  │ • Garantia: Solução ÓTIMA (ou aproximação com GAP)         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Saída:                                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Status: Optimal (1), Feasible (0), Infeasible (-1)         │  │
│  │ Valores: P_solar[t], P_diesel[t], ..., E_bateria[t]        │  │
│  │ Custo: Valor mínimo encontrado                             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## 📁 Árvore de Arquivos Expandida

```
c:\Users\lucas\OneDrive\...\claudia_tese v2\
│
├── 🆕 MILP_GUIA_RAPIDO.md              ← LEIA PRIMEIRO (guia rápido)
│
├── otmizadores/
│   ├── 🆕 milp_controle_microrrede.py  ← Classe MILPMicrorredes (CORE)
│   ├── 🆕 exemplo_milp.py              ← 3 exemplos executáveis
│   ├── 🆕 MILP_README.md               ← Documentação técnica
│   ├── gestor_energia.py
│   ├── otmizador1.py
│   ├── pso.py
│   ├── pulp2.py
│   ├── simulador_energia.py
│   └── __pycache__/
│
├── analises/
│   ├── PrioridadeMicro.py              ← MODIFICADO: +analise_5_milp
│   ├── PrioridadeGestor.py
│   ├── __pycache__/
│   └── ...
│
├── models/
│   ├── Microrrede.py
│   ├── CRUD.py
│   └── ...
│
├── Home.py                              ← Ponto de entrada Streamlit
├── requirements.txt                     ← PuLP já está aqui!
└── ...
```

## 🎯 Exemplo de Execução Completa

```
1. USUÁRIO CLICA EM "Análise 5 - MILP"
        │
        ▼
2. Streamlit carrega microrrede do banco
        │
        ▼
3. MILPMicrorredes(microrrede) ← instancia
        │
        ├─► criar_modelo()       (define variáveis)
        ├─► adicionar_restricoes() (define restrições)
        ├─► adicionar_funcao_objetivo() (define custo)
        │
        ▼
4. resolver()                   ← chama CBC solver
        │
        ├─ Se viável: retorna True
        └─ Se infeasível: retorna False
        │
        ▼
5. extrair_solucao() + gerar_dataframe_resultado()
        │
        ▼
6. Interface Streamlit exibe:
        ├─ 📊 Gráficos de despacho
        ├─ 💰 Custos por fonte
        ├─ 📈 Evolução temporal
        ├─ 📋 Tabelas detalhadas
        └─ ✅ Comparação com Análise 4
        │
        ▼
7. USUÁRIO TOMA DECISÃO BASEADO NA OTIMIZAÇÃO
```

## 🔍 Comparação Análises 1-5

```
┌─────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ ASPECTO     │ ANÁLISE 1    │ ANÁLISE 2    │ ANÁLISE 3    │ ANÁLISE 4    │ ANÁLISE 5 ⭐ │
├─────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ Abordagem   │ Sequencial   │ Heurística   │ Heurística   │ Heurística   │ MILP ÓTIMA   │
│ Otimização  │ ❌ Nenhuma   │ ✓ Local      │ ✓ Local      │ ✓ Local    │ ✅ Global    │
│ Tempo       │ <1s          │ <1s          │ <1s          │ <1s          │ ~30s         │
│ Custo       │ Alto         │ Médio        │ Médio-Baixo  │ Baixo        │ Mínimo ✅   │
│ Prioridade  │ Manual       │ Manual       │ Manual       │ Manual       │ Automática   │
│ Bateria     │ Básico       │ Otimizdo     │ Otimizado    │ Otimizado    │ Ótimo        │
│ Despacho    │ Sequencial   │ Ordenado     │ Deslizável   │ Local        │ Global       │
│ Confiança   │ Baixa        │ Média        │ Média        │ Alta         │ Máxima ✅    │
└─────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

## 📞 Contatos entre Módulos

```
milp_controle_microrrede.py
    │
    ├─► importa: models.Microrrede (classes Solar, Diesel, etc.)
    ├─► importa: models.CRUD (Ler, Ler_Objeto)
    ├─► importa: Tools.GerarCurvaCarga (CurvaCarga)
    ├─► importa: pulp (LpProblem, LpVariable, etc.)
    └─► importa: pandas, numpy, json
            │
            ▼
PrioridadeMicro.py
    │
    ├─► importa: otmizadores.milp_controle_microrrede
    ├─► exporta: analise_5_milp(), analise_5_milp_multi()
    └─► usa em Streamlit via: st.subheader, st.line_chart, etc.
            │
            ▼
Home.py (ou pages/Analises.py)
    │
    └─► chama: analise_5_milp(microrrede)
        exibe resultado no Streamlit
```

## 🚀 Pipeline de Dados Completo

```
DADOS BRUTOS (banco de dados)
    Microrrede(id=1)
        ├─ solar: Solar(...)
        │   └─ curva_geracao: [12.5, 25.3, 40.1, ..., 5.2] (1440 floats)
        ├─ diesel: Diesel(potencia=50kW, custo_por_kWh=2.50)
        ├─ biogas: Biogas(potencia=30kW, custo_por_kWh=1.80)
        ├─ bateria: Bateria(cap=200kWh, efic=95%, custo=0.30/kWh)
        ├─ concessionaria: Concessionaria(tarifa=1.50/kWh)
        └─ carga: Carga(id=...) → CurvaCarga → [2.1, 2.3, 2.5, ..., 2.2]
            │
            ▼
        PROBLEMA OTIMIZAÇÃO
            Minimize: Custo operacional total
            Sujeito a: Balanço energético + Restrições técnicas
            │
            ▼
        SOLVER MILP (CBC)
            ~30 segundos de processamento
            │
            ▼
        SOLUÇÃO ÓTIMA
            ├─ P_solar[t]: [12.5, 25.3, 40.1, ..., 5.2] kW
            ├─ P_diesel[t]: [0, 0, 0, ..., 15.3] kW
            ├─ P_bateria[t]: [5.1, 3.2, 8.5, ..., 12.1] kW
            ├─ E_bateria[t]: [200, 195, 190, ..., 155] kWh
            └─ Custo Total: R$ 2,543.50
            │
            ▼
        RESULTADOS (DataFrame + Gráficos)
            Exibição em Streamlit com:
            ├─ Despacho ao longo do dia
            ├─ Custos por fonte
            ├─ Níveis de armazenamento
            ├─ Métrica de autossuficiência
            └─ Comparação com análises anteriores
```

---

**Diagrama atualizado:** Março 2026  
**Versão MILP:** 1.0
