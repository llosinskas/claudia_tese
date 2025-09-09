import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, value, LpContinuous

# ==============================
# Parâmetros do sistema (edite aqui)
# ==============================
preco_diesel_kWh       = 0.70   # R$/kWh
preco_rede_compra_kWh  = 0.80   # R$/kWh
preco_bateria_OM_kWh   = 0.05   # R$/kWh descarregado (O&M/degradação)
preco_venda_kWh        = 0.40   # R$/kWh exportado à rede

eta_ch   = 0.95   # eficiência de carga (bateria aumenta SOC em eta_ch * energia_solar_usada)
eta_dis  = 0.95   # eficiência de descarga (entrega = eta_dis * energia_tirada)
DoD      = 0.80   # profundidade de descarga máxima (SOC mínimo = 20%)

cap_bateria_kWh = 12.0   # capacidade nominal (kWh) — pode otimizar no futuro se quiser
soc0_frac       = 0.50   # SOC inicial (fração da capacidade)

pot_extra_kW    = 3.0    # potência máx. da carga extra (kW)
lim_diesel_kW   = None   # limite de potência do diesel (kW) ou None
lim_rede_kW     = None   # limite de potência da rede (kW)   ou None

penalidade_deficit = 50.0  # R$/kWh não atendido (para evitar cortes)

# Diesel só pode operar se for mais barato que rede
diesel_permitido = preco_diesel_kWh < preco_rede_compra_kWh

# ==============================
# Dados sintéticos (1 dia, 24h)
# ==============================
np.random.seed(7)
h = np.arange(24)

# Solar (kW): sino com ruído, pico próximo ao meio-dia
mu, sigma = 12, 3.0
solar_base = np.exp(-0.5*((h-mu)/sigma)**2)
solar_kWp  = 7.5
nuvens     = np.clip(np.random.normal(1.0, 0.1, 24), 0.75, 1.15)
S = solar_kWp * solar_base * nuvens
S[S < 0.05] = 0.0  # zera rabos

# Carga principal (kW): base + picos manhã/noite
def gauss(x, m, s, a): return a*np.exp(-0.5*((x-m)/s)**2)
load_base = 2.2 + np.random.normal(0, 0.05, 24)
load_peak = gauss(h, 8,  1.6, 1.8) + gauss(h, 19, 1.8, 2.0)
L = np.clip(load_base + load_peak, 1.5, None)

# ==============================
# Modelo de otimização (LP)
# ==============================
T = range(24)
cap = cap_bateria_kWh
soc_min = (1.0 - DoD) * cap
soc0 = soc0_frac * cap

m = LpProblem("Despacho_custo_minimo_24h", LpMinimize)

# Variáveis por hora
s2load   = LpVariable.dicts("solar_to_load",   T, lowBound=0, cat=LpContinuous)
s2batt   = LpVariable.dicts("solar_to_batt",   T, lowBound=0, cat=LpContinuous)  # energia solar usada para carregar
s2extra  = LpVariable.dicts("solar_to_extra",  T, lowBound=0, cat=LpContinuous)
s2export = LpVariable.dicts("solar_to_export", T, lowBound=0, cat=LpContinuous)

batt_out = LpVariable.dicts("batt_to_load_out", T, lowBound=0, cat=LpContinuous) # energia RETIRADA da bateria
diesel   = LpVariable.dicts("diesel_to_load",  T, lowBound=0 if diesel_permitido else 0, upBound=None if diesel_permitido else 0, cat=LpContinuous)
grid     = LpVariable.dicts("grid_to_load",    T, lowBound=0, cat=LpContinuous)
shortage = LpVariable.dicts("shortage",        T, lowBound=0, cat=LpContinuous)

SOC      = LpVariable.dicts("SOC", T, lowBound=soc_min, upBound=cap, cat=LpContinuous)

# Limites de potência (se definidos)
if lim_diesel_kW is not None and diesel_permitido:
    for t in T:
        m += diesel[t] <= lim_diesel_kW
if lim_rede_kW is not None:
    for t in T:
        m += grid[t] <= lim_rede_kW

# Balanço de solar (split do recurso solar)
for t in T:
    m += s2load[t] + s2batt[t] + s2extra[t] + s2export[t] <= S[t], f"solar_split_{t}"

# Carga extra só pode usar excedente solar e é limitada
for t in T:
    m += s2extra[t] <= pot_extra_kW, f"extra_cap_{t}"
    # (já implícito por solar_split que é só solar)

# Balanço da demanda principal (o que chega à carga)
# Nota: energia entregue pela bateria = eta_dis * batt_out[t]
for t in T:
    m += s2load[t] + eta_dis*batt_out[t] + diesel[t] + grid[t] + shortage[t] == L[t], f"load_balance_{t}"

# Dinâmica da bateria
for t in T:
    if t == 0:
        m += SOC[t] == soc0 + eta_ch*s2batt[t] - batt_out[t], f"soc_0"
    else:
        m += SOC[t] == SOC[t-1] + eta_ch*s2batt[t] - batt_out[t], f"soc_{t}"

# (Opcional) manter SOC final próximo do inicial (fechamento de ciclo)
# m += SOC[23] >= soc0 * 0.9
# m += SOC[23] <= soc0 * 1.1

# Diesel só permitido se preço < rede (já tratado ao criar variável).
# Se quiser permitir empate (<=), troque a condição em diesel_permitido.

# Função objetivo: minimizar custo líquido (custos - receita)
cost = lpSum([
    preco_diesel_kWh * diesel[t] +
    preco_rede_compra_kWh * grid[t] +
    preco_bateria_OM_kWh * (eta_dis * batt_out[t]) -  # custo por kWh ENTREGUE
    preco_venda_kWh * s2export[t]
    for t in T
]) + penalidade_deficit * lpSum([shortage[t] for t in T])

m += cost

# Resolver
m.solve()

print("Status:", LpStatus[m.status])

# Extrair solução
sol = {
    "Hora": list(T),
    "Solar (kW)": [S[t] for t in T],
    "Carga (kW)": [L[t] for t in T],
    "Solar→Carga": [value(s2load[t]) for t in T],
    "Solar→Bateria (energia solar)": [value(s2batt[t]) for t in T],
    "Solar→Carga Extra": [value(s2extra[t]) for t in T],
    "Solar→Exportação": [value(s2export[t]) for t in T],
    "Bateria→Carga (entregue)": [eta_dis*value(batt_out[t]) for t in T],
    "Bateria Saída (bruta)": [value(batt_out[t]) for t in T],
    "Diesel→Carga": [value(diesel[t]) for t in T],
    "Rede→Carga": [value(grid[t]) for t in T],
    "Déficit": [value(shortage[t]) for t in T],
    "SOC (kWh)": [value(SOC[t]) for t in T],
}
df = pd.DataFrame(sol)

# Métricas e custos
diesel_energy  = df["Diesel→Carga"].sum()
grid_buy       = df["Rede→Carga"].sum()
batt_delivered = df["Bateria→Carga (entregue)"].sum()
solar_load     = df["Solar→Carga"].sum()
solar_to_batt  = df["Solar→Bateria (energia solar)"].sum()
solar_extra    = df["Solar→Carga Extra"].sum()
solar_export   = df["Solar→Exportação"].sum()
short_total    = df["Déficit"].sum()

cost_diesel = diesel_energy * preco_diesel_kWh
cost_grid   = grid_buy * preco_rede_compra_kWh
cost_batt   = batt_delivered * preco_bateria_OM_kWh
revenue     = solar_export * preco_venda_kWh
cost_short  = short_total * penalidade_deficit
net_cost    = cost_diesel + cost_grid + cost_batt - revenue + cost_short

print("\n=== RESUMO (Otimização 24h) ===")
print(f"Carga total:           {df['Carga (kW)'].sum():.2f} kWh")
print(f" Atendida por Solar:   {solar_load:.2f} kWh")
print(f" Atendida por Bateria: {batt_delivered:.2f} kWh")
print(f" Atendida por Diesel:  {diesel_energy:.2f} kWh")
print(f" Atendida por Rede:    {grid_buy:.2f} kWh")
print(f" Déficit:              {short_total:.2f} kWh")
print("\nExcedente solar:")
print(f"  → Bateria (energia solar): {solar_to_batt:.2f} kWh")
print(f"  → Carga extra:             {solar_extra:.2f} kWh")
print(f"  → Venda (export):          {solar_export:.2f} kWh")
print("\nEconomia (R$):")
print(f"  Diesel:         {cost_diesel:8.2f}")
print(f"  Rede (compra):  {cost_grid:8.2f}")
print(f"  Bateria (O&M):  {cost_batt:8.2f}")
print(f"  Receita venda: -{revenue:8.2f}")
print(f"  Penalidade:     {cost_short:8.2f}")
print(f"= CUSTO LÍQUIDO:  {net_cost:8.2f}")

# ==============================
# Gráficos
# ==============================

# 1) Fontes que atendem a carga principal
plt.figure(figsize=(11,5))
plt.stackplot(
    df["Hora"],
    df["Solar→Carga"],
    df["Bateria→Carga (entregue)"],
    df["Diesel→Carga"],
    df["Rede→Carga"],
    labels=["Solar→Carga", "Bateria→Carga", "Diesel→Carga", "Rede→Carga"],
    alpha=0.9
)
plt.plot(df["Hora"], df["Carga (kW)"], "--", label="Carga", linewidth=2)
plt.title("Atendimento da Carga por Fonte (24h) — Ótimo de Custo")
plt.xlabel("Hora")
plt.ylabel("Energia (kWh)")
plt.legend(loc="upper left")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# 2) Destino do excedente solar (após atender carga)
plt.figure(figsize=(11,5))
plt.stackplot(
    df["Hora"],
    df["Solar→Bateria (energia solar)"],
    df["Solar→Carga Extra"],
    df["Solar→Exportação"],
    labels=["Solar→Bateria (energia solar)", "Solar→Carga Extra", "Venda para Rede"],
    alpha=0.9
)
plt.title("Alocação do Excedente Solar (24h) — Ótimo de Custo")
plt.xlabel("Hora")
plt.ylabel("Energia (kWh)")
plt.legend(loc="upper left")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# 3) SOC da bateria
plt.figure(figsize=(11,3.8))
plt.plot(df["Hora"], df["SOC (kWh)"], label="SOC (kWh)")
plt.axhline(soc_min, color="gray", linestyle="--", linewidth=1, label="SOC mínimo")
plt.axhline(cap,     color="gray", linestyle=":",  linewidth=1, label="Capacidade")
plt.title("Estado de Carga da Bateria (24h)")
plt.xlabel("Hora")
plt.ylabel("kWh")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
