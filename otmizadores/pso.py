import numpy as np

# Dimensão: 3*T (diesel, charge, discharge)
T = (3)
dim = 3*T

def project_bounds(x):
    # Aplica limites por faixa
    x = x.copy()
    x[:T] = np.clip(x[:T], 0, P_diesel_max)         # diesel
    x[T:2*T] = np.clip(x[T:2*T], 0, P_batt_ch_max)  # charge
    x[2*T:] = np.clip(x[2*T:], 0, P_batt_dis_max)   # discharge
    return x

def evaluate(x):
    # Decodifica
    Pd   = x[:T]
    Pch  = x[T:2*T]
    Pdis = x[2*T:]
    # Dinâmica SOC
    soc = np.zeros(T)
    soc[0] = SOC0 + dt*((Pch[0]/eta_ch) - (Pdis[0]*eta_dis))
    for t in range(1, T):
        soc[t] = soc[t-1] + dt*((Pch[t]/eta_ch) - (Pdis[t]*eta_dis))
    # Penaliza violação de SOC
    pen_soc = np.sum(np.maximum(0, SOC_min - soc) + np.maximum(0, soc - SOC_max))*1000

    # Balanço => grid compra/venda implícita
    net = load - solar - Pd - Pdis*eta_dis + Pch/eta_ch
    # net > 0 => precisa comprar; net < 0 => vende
    buy = np.maximum(0, net)
    sell = np.maximum(0, -net)

    cost = dt*(np.dot(grid_price, buy) - np.dot(feed_in, sell) + diesel_cost*np.sum(Pd)
               + batt_penalty*(np.sum(Pch/eta_ch) + np.sum(Pdis*eta_dis)))
    return cost + pen_soc

def pso_optimize(iterations=200, swarm_size=50, w=0.7, c1=1.4, c2=1.4):
    # Inicialização
    X = np.random.rand(swarm_size, dim)
    # escalar para limites
    X[:, :T]    *= P_diesel_max
    X[:, T:2*T] *= P_batt_ch_max
    X[:, 2*T:]  *= P_batt_dis_max
    V = np.zeros_like(X)

    pbest = X.copy()
    pbest_val = np.array([evaluate(project_bounds(x)) for x in X])
    gbest_idx = np.argmin(pbest_val)
    gbest = pbest[gbest_idx].copy()
    gbest_val = pbest_val[gbest_idx]

    for it in range(iterations):
        r1, r2 = np.random.rand(swarm_size, dim), np.random.rand(swarm_size, dim)
        V = w*V + c1*r1*(pbest - X) + c2*r2*(gbest - X)
        X = project_bounds(X + V)

        vals = np.array([evaluate(x) for x in X])
        improved = vals < pbest_val
        pbest[improved] = X[improved]
        pbest_val[improved] = vals[improved]
        gbest_idx = np.argmin(pbest_val)
        gbest = pbest[gbest_idx].copy()
        gbest_val = pbest_val[gbest_idx]

    return gbest, gbest_val

gbest, gbest_val = pso_optimize()
print("PSO custo:", round(gbest_val, 2))
Pd_pso   = gbest[:T]
Pch_pso  = gbest[T:2*T]
Pdis_pso = gbest[2*T:]