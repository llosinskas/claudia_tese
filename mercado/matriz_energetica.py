"""
Cálculo da composição da matriz energética e definição de preço de oferta.
"""

from dataclasses import dataclass
import numpy as np

from mercado.resultado_analise import ResultadoAnalise


@dataclass
class MatrizEnergetica:
    """Composição da matriz energética de uma microrrede em um instante de tempo."""
    perc_solar: float
    perc_bateria: float
    perc_diesel: float
    perc_biogas: float
    perc_concessionaria: float
    custo_medio_kwh: float     # R$/kWh médio ponderado da matriz


def calcular_matriz_instantanea(resultado: ResultadoAnalise, t: int) -> MatrizEnergetica:
    """
    Calcula a matriz energética no instante t, ou seja, a proporção de cada fonte
    no total de energia fornecida, e o custo médio ponderado por kWh.
    """
    u_sol = resultado.uso_solar[t]
    u_bat = resultado.uso_bateria[t]
    u_die = resultado.uso_diesel[t]
    u_bio = resultado.uso_biogas[t]
    u_con = resultado.uso_concessionaria[t]
    
    total_uso = u_sol + u_bat + u_die + u_bio + u_con
    
    if total_uso <= 0:
        # Se não há uso, retorna uma matriz vazia com custo zero
        return MatrizEnergetica(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    
    p_sol = u_sol / total_uso
    p_bat = u_bat / total_uso
    p_die = u_die / total_uso
    p_bio = u_bio / total_uso
    p_con = u_con / total_uso
    
    # Custo unitário por kWh de cada fonte (se existir)
    mr = resultado.microrrede
    c_sol = mr.solar.custo_kwh if mr.solar else 0.0
    c_bat = mr.bateria.custo_kwh if mr.bateria else 0.0
    c_die = mr.diesel.custo_por_kWh if mr.diesel else 0.0
    c_bio = mr.biogas.custo_por_kWh if mr.biogas else 0.0
    c_con = mr.concessionaria.tarifa if mr.concessionaria else 0.0
    
    # Preço médio ponderado = Sum(proporção * custo_fonte)
    custo_medio = (p_sol * c_sol) + (p_bat * c_bat) + (p_die * c_die) + (p_bio * c_bio) + (p_con * c_con)
    
    return MatrizEnergetica(
        perc_solar=p_sol * 100,
        perc_bateria=p_bat * 100,
        perc_diesel=p_die * 100,
        perc_biogas=p_bio * 100,
        perc_concessionaria=p_con * 100,
        custo_medio_kwh=custo_medio
    )

def calcular_matriz_acumulada(resultado: ResultadoAnalise) -> MatrizEnergetica:
    """
    Calcula a matriz energética acumulada (total do dia) de uma microrrede.
    """
    u_sol = resultado.uso_solar.sum()
    u_bat = resultado.uso_bateria.sum()
    u_die = resultado.uso_diesel.sum()
    u_bio = resultado.uso_biogas.sum()
    u_con = resultado.uso_concessionaria.sum()
    
    total_uso = u_sol + u_bat + u_die + u_bio + u_con
    
    if total_uso <= 0:
        return MatrizEnergetica(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    
    p_sol = u_sol / total_uso
    p_bat = u_bat / total_uso
    p_die = u_die / total_uso
    p_bio = u_bio / total_uso
    p_con = u_con / total_uso
    
    mr = resultado.microrrede
    c_sol = mr.solar.custo_kwh if mr.solar else 0.0
    c_bat = mr.bateria.custo_kwh if mr.bateria else 0.0
    c_die = mr.diesel.custo_por_kWh if mr.diesel else 0.0
    c_bio = mr.biogas.custo_por_kWh if mr.biogas else 0.0
    c_con = mr.concessionaria.tarifa if mr.concessionaria else 0.0
    
    custo_medio = (p_sol * c_sol) + (p_bat * c_bat) + (p_die * c_die) + (p_bio * c_bio) + (p_con * c_con)
    
    return MatrizEnergetica(
        perc_solar=p_sol * 100,
        perc_bateria=p_bat * 100,
        perc_diesel=p_die * 100,
        perc_biogas=p_bio * 100,
        perc_concessionaria=p_con * 100,
        custo_medio_kwh=custo_medio
    )

def preco_oferta(resultado: ResultadoAnalise, t: int, margem: float = 0.05) -> float:
    """
    Define o preço de venda da energia no instante t com base na matriz energética.
    Preço = Custo Médio Ponderado * (1 + margem)
    Se o custo médio for 0 (ex: só solar grátis), o preço mínimo pode ser baseado no solar ou 0.
    """
    matriz = calcular_matriz_instantanea(resultado, t)
    
    # Se custo_medio é 0, mas existe excesso (provavelmente solar), 
    # cobra pelo menos o custo do solar + margem para ter algum lucro.
    custo_base = matriz.custo_medio_kwh
    if custo_base <= 0.001 and resultado.microrrede.solar:
        custo_base = resultado.microrrede.solar.custo_kwh
        
    preco = custo_base * (1.0 + margem)
    
    # Opcional: Garante que o preço não exceda o preço da concessionária, senão ninguém compra
    tarifa_rede = resultado.microrrede.concessionaria.tarifa if resultado.microrrede.concessionaria else float('inf')
    
    # Limita o preço a 95% da tarifa da rede (sempre um desconto)
    return min(preco, tarifa_rede * 0.95)
