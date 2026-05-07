"""Teste rápido MG-02 - verificar oscilação recarga"""
import json, numpy as np, time
from models.Microrrede import Microrrede, Bateria, Biogas, Diesel, Carga, Solar, Concessionaria, CargaFixa
from Tools.geradorSolar import gerar_solar
from otmizadores.milp_controle_microrrede import MILPMicrorredes_ComDeslizamento

curva_solar = gerar_solar(100, -31.91, -52.9)
mg2 = Microrrede(
    nome="MG - 02", coordenada_x=-31.91, coordenada_y=-52.9,
    bateria=Bateria(potencia=40, capacidade=150, bateria="LiFePO4", nivel=80, eficiencia=95, capacidade_min=20, capacidade_max=80, custo_kwh=0.5),
    solar=Solar(potencia=100, custo_kwh=0.3, curva_geracao=json.dumps(curva_solar.tolist())),
    concessionaria=Concessionaria(nome="CEEE equatorial", tarifa=0.8, demanda=100, grupo="B"),
    biogas=Biogas(potencia=0, custo_por_kWh=0.4, nivel=100, tanque=500, geracao=0, consumo_50=0.3, consumo_75=0.45, consumo_100=0.6),
    diesel=Diesel(potencia=5.5, custo_por_kWh=2.0, nivel=100, tanque=40, consumo_50=0.4, consumo_75=0.35, consumo_100=0.3),
    carga=Carga(cargaFixa=[
        CargaFixa(nome="Ordenha manha", potencia=12.5, tempo_liga=300, tempo_desliga=420, prioridade=1),
        CargaFixa(nome="Ordenha tarde", potencia=12.5, tempo_liga=960, tempo_desliga=1080, prioridade=1),
        CargaFixa(nome="Resfriador pós ordenha manhã", potencia=5, tempo_liga=420, tempo_desliga=600, prioridade=1),
        CargaFixa(nome="Resfriador", potencia=2.5, tempo_liga=600, tempo_desliga=960, prioridade=1),
        CargaFixa(nome="Resfriador pós ordenha Tarde", potencia=5, tempo_liga=1080, tempo_desliga=1260, prioridade=1),
        CargaFixa(nome="Refregerador Noite", potencia=2.5, tempo_liga=1260, tempo_desliga=1439, prioridade=1),
        CargaFixa(nome="Refrigerador Madrugada", potencia=2.5, tempo_liga=0, tempo_desliga=300, prioridade=1),
        CargaFixa(nome="Irrigação Madrugada", potencia=66.6, tempo_liga=0, tempo_desliga=480, prioridade=2),
        CargaFixa(nome="Irrigação Madrugada 1", potencia=88.8, tempo_liga=700, tempo_desliga=1180, prioridade=2),
        CargaFixa(nome="Cerca elétrica", potencia=0.01, tempo_liga=0, tempo_desliga=1439, prioridade=1),
        CargaFixa(nome="Bomba de água manhã", potencia=1, tempo_liga=360, tempo_desliga=400, prioridade=1),
        CargaFixa(nome="Bomba d'água Meio dia", potencia=1, tempo_liga=720, tempo_desliga=750, prioridade=2),
        CargaFixa(nome="Bomba d'água Noite", potencia=1, tempo_liga=1020, tempo_desliga=1060, prioridade=2),
        CargaFixa(nome="Residencial - Propriedade 1", potencia=4, tempo_liga=1020, tempo_desliga=1380, prioridade=1),
        CargaFixa(nome="Residencial - Propriedade 2", potencia=6, tempo_liga=1020, tempo_desliga=1380, prioridade=1),
        CargaFixa(nome="Residencial - Propriedade 3", potencia=8, tempo_liga=1020, tempo_desliga=1380, prioridade=1),
        CargaFixa(nome="Residencial - Propriedade 4", potencia=3, tempo_liga=1020, tempo_desliga=1380, prioridade=1),
        CargaFixa(nome="Res1Base", potencia=0.5, tempo_liga=0, tempo_desliga=1439, prioridade=1),
        CargaFixa(nome="Res2Base", potencia=0.6, tempo_liga=0, tempo_desliga=1439, prioridade=1),
        CargaFixa(nome="Res3Base", potencia=0.8, tempo_liga=0, tempo_desliga=1439, prioridade=1),
        CargaFixa(nome="Res4Base", potencia=0.5, tempo_liga=0, tempo_desliga=1439, prioridade=1),
    ])
)

t0 = time.time()
otm = MILPMicrorredes_ComDeslizamento(mg2, passo_deslizamento=15)
otm.criar_modelo(); otm.adicionar_restricoes(); otm.adicionar_funcao_objetivo()
sucesso = otm.resolver()
print(f"Tempo: {time.time()-t0:.1f}s")

if sucesso:
    sol = otm.extrair_solucao()
    # Contar transições de modo
    bat_mode = np.array([1 if sol['Bateria'][t] > 0.01 else (0 if sol['Carga_Bateria'][t] < 0.01 else -1) for t in range(1440)])
    switches = np.sum(np.abs(np.diff(bat_mode)) > 0)
    print(f"Custo: R$ {sol['Custo_Total']:.2f}")
    print(f"Transições de modo bateria: {switches}")
    print(f"Bateria desc: {sol['Bateria'].sum()/60:.1f} kWh, carga: {sol['Carga_Bateria'].sum()/60:.1f} kWh")
    print(f"Pico rede: {sol['Concessionaria'].max():.2f} kW")
    print(f"Nível bat: ini={sol['Nivel_Bateria'][0]:.1f}, min={sol['Nivel_Bateria'].min():.1f}, fim={sol['Nivel_Bateria'][-1]:.1f}")
    
    print(f"\nPerfil horário:")
    for h in range(24):
        s, e = h*60, min((h+1)*60, 1440)
        d = sol['Bateria'][s:e].mean()
        c = sol['Carga_Bateria'][s:e].mean()
        n = sol['Nivel_Bateria'][s]
        sl = sol['Solar'][s:e].mean()
        r = sol['Concessionaria'][s:e].mean()
        print(f"  {h:02d}h  Desc:{d:6.2f}  Carga:{c:6.2f}  Nível:{n:6.1f}  Solar:{sl:6.2f}  Rede:{r:6.2f}")
