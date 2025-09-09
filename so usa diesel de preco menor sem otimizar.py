import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# -----------------------------
# 1. Parâmetros do sistema
# -----------------------------
preco_diesel = 6.00         # R$/kWh
preco_rede_compra = 0.80    # R$/kWh
preco_bateria_OM = 0.05     # R$/kWh
preco_venda_excedente = 0.40  # R$/kWh
eficiencia_bateria = 0.9
dod = 0.8

# -----------------------------
# 2. Geração de dados sintéticos
# -----------------------------
dias = 7
horas = dias * 24
np.random.seed(42)

# Solar (kW)
solar = np.maximum(0, np.sin(np.linspace(0, dias*np.pi, horas)) * 5 + np.random.normal(0, 0.3, horas))

# Cargas (kW)
carga1 = np.random.uniform(1.5, 2.5, horas)
carga2 = np.random.uniform(0.5, 1.5, horas)
carga_total = carga1 + carga2

# -----------------------------
# 3. Função de simulação
# -----------------------------
def simular(cap_bateria, limite_diesel, limite_rede, detalhar=False):
    bateria = 0
    diesel_total = 0
    rede_compra_total = 0
    rede_venda_total = 0

    # Para detalhamento
    hist_solar_carga = []
    hist_solar_bat = []
    hist_bat_carga = []
    hist_diesel_carga = []
    hist_rede_carga = []
    hist_venda = []
    hist_bat_soc = []

    for h in range(horas):
        demanda = carga_total[h]
        geracao = solar[h]

        solar_para_carga = 0
        solar_para_bat = 0
        bat_para_carga = 0
        diesel_para_carga = 0
        rede_para_carga = 0
        venda_rede = 0

        # Passo 1: atende carga com solar
        if geracao >= demanda:
            solar_para_carga = demanda
            sobra = geracao - demanda

            # Carrega bateria primeiro
            capacidade_restante = cap_bateria - bateria
            carga_bat = min(sobra * eficiencia_bateria, capacidade_restante)
            bateria += carga_bat
            solar_para_bat = carga_bat / eficiencia_bateria
            sobra -= carga_bat / eficiencia_bateria

            # Se ainda sobra energia → vende para rede
            if sobra > 0:
                venda_rede = sobra
                rede_venda_total += sobra

        else:
            solar_para_carga = geracao
            deficit = demanda - geracao

            # Passo 2: usa bateria
            descarga_bat = min(deficit, bateria * dod)
            bateria -= descarga_bat
            bat_para_carga = descarga_bat
            deficit -= descarga_bat

            # Passo 3: se diesel for mais barato que rede → usa diesel
            if preco_diesel < preco_rede_compra and deficit > 0:
                diesel_usado = min(deficit, limite_diesel)
                diesel_total += diesel_usado
                diesel_para_carga = diesel_usado
                deficit -= diesel_usado

            # Passo 4: compra da rede
            if deficit > 0:
                rede_usada = min(deficit, limite_rede)
                rede_compra_total += rede_usada
                rede_para_carga = rede_usada
                deficit -= rede_usada

        if detalhar:
            hist_solar_carga.append(solar_para_carga)
            hist_solar_bat.append(solar_para_bat)
            hist_bat_carga.append(bat_para_carga)
            hist_diesel_carga.append(diesel_para_carga)
            hist_rede_carga.append(rede_para_carga)
            hist_venda.append(venda_rede)
            hist_bat_soc.append(bateria)

    custo_total = (diesel_total * preco_diesel) + \
                  (rede_compra_total * preco_rede_compra) + \
                  (cap_bateria * preco_bateria_OM * dias) - \
                  (rede_venda_total * preco_venda_excedente)

    if detalhar:
        return custo_total, diesel_total, rede_compra_total, rede_venda_total, {
            "solar_carga": hist_solar_carga,
            "solar_bat": hist_solar_bat,
            "bat_carga": hist_bat_carga,
            "diesel_carga": hist_diesel_carga,
            "rede_carga": hist_rede_carga,
            "venda": hist_venda,
            "soc": hist_bat_soc
        }
    else:
        return custo_total, diesel_total, rede_compra_total, rede_venda_total

# -----------------------------
# 4. Função objetivo
# -----------------------------
def func_obj(x):
    cap_bat, lim_diesel, lim_rede = x
    if cap_bat < 0 or lim_diesel < 0 or lim_rede < 0:
        return 1e6
    custo, _, _, _ = simular(cap_bat, lim_diesel, lim_rede)
    return custo

# -----------------------------
# 5. Otimização
# -----------------------------
x0 = [10, 5, 10]
res = minimize(func_obj, x0, method='Powell')
cap_otim, diesel_otim, rede_otim = res.x

# -----------------------------
# 6. Simulação final detalhada
# -----------------------------
custo_final, diesel_final, rede_compra_final, rede_venda_final, hist = simular(cap_otim, diesel_otim, rede_otim, detalhar=True)

# -----------------------------
# 7. Resultados
# -----------------------------
print("Resultados da Otimização:")
print(f"Capacidade ótima da bateria: {cap_otim:.2f} kWh")
print(f"Limite diário de diesel: {diesel_otim:.2f} kWh")
print(f"Limite diário de compra da rede: {rede_otim:.2f} kWh")
print(f"Diesel consumido total: {diesel_final:.2f} kWh")
print(f"Rede comprada total: {rede_compra_final:.2f} kWh")
print(f"Excedente vendido total: {rede_venda_final:.2f} kWh")
print(f"Custo líquido final: R$ {custo_final:.2f}")

# -----------------------------
# 8. Gráficos diários empilhados
# -----------------------------
df_hist = pd.DataFrame(hist)
df_hist['Hora'] = range(horas)

for dia in range(dias):
    df_dia = df_hist[dia*24:(dia+1)*24]
    plt.figure(figsize=(10,5))
    plt.stackplot(df_dia['Hora'] % 24,
                  df_dia['solar_carga'],
                  df_dia['bat_carga'],
                  df_dia['diesel_carga'],
                  df_dia['rede_carga'],
                  labels=['Solar → Carga', 'Bateria → Carga', 'Diesel → Carga', 'Rede → Carga'],
                  alpha=0.8)
    plt.plot(df_dia['Hora'] % 24, df_dia['soc'], label='SoC Bateria (kWh)', color='black', linestyle='--')
    plt.title(f'Fluxos de Energia - Dia {dia+1}')
    plt.xlabel('Hora do dia')
    plt.ylabel('Potência (kW)')
    plt.legend(loc='upper right')
    plt.grid()
    plt.show()

# -----------------------------
# 9. Gráfico de vendas de energia
# -----------------------------
plt.figure(figsize=(12,4))
plt.bar(range(horas), df_hist['venda'], color='orange', label='Venda para rede')
plt.xlabel('Hora')
plt.ylabel('kW vendidos')
plt.title('Energia vendida para a rede')
plt.legend()
plt.grid()
plt.show()


