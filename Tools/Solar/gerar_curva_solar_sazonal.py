"""
Gerador de curvas solares sazonais usando pvlib.

Gera curvas de geração solar (1440 pontos = 1 dia em minutos) para cada
estação do ano, dada a localização geográfica e potência instalada.

Datas representativas (Hemisfério Sul):
  - Verão:     15 de Janeiro
  - Outono:    15 de Abril
  - Inverno:   15 de Julho
  - Primavera: 15 de Outubro
"""

import pvlib
import pandas as pd
import numpy as np
from typing import Dict, Optional


# Datas representativas de cada estação (Hemisfério Sul)
DATAS_ESTACOES = {
    "Verão":     "2026-01-15",
    "Outono":    "2026-04-15",
    "Inverno":   "2026-07-15",
    "Primavera": "2026-10-15",
}

ICONES_ESTACOES = {
    "Verão":     "🌞",
    "Outono":    "🍂",
    "Inverno":   "❄️",
    "Primavera": "🌸",
}


def gerar_curva_solar_estacao(
    latitude: float,
    longitude: float,
    potencia_kw: float,
    data: str,
    eficiencia: float = 0.8,
    timezone: str = "America/Sao_Paulo",
) -> np.ndarray:
    """
    Gera a curva de geração solar para um dia específico.
    
    Args:
        latitude: Latitude do local
        longitude: Longitude do local
        potencia_kw: Potência nominal instalada (kWp)
        data: Data no formato 'YYYY-MM-DD'
        eficiencia: Eficiência do sistema (0 a 1)
        timezone: Fuso horário
        
    Returns:
        np.ndarray de 1440 pontos (1 por minuto) com geração em kW
    """
    local = pvlib.location.Location(latitude, longitude, timezone)
    
    inicio = data
    fim = f"{data} 23:59:59"
    times = pd.date_range(start=inicio, end=fim, freq="1min", tz=timezone)
    
    posicao_solar = local.get_solarposition(times)
    irradiancia = local.get_clearsky(times)
    
    gerador = pvlib.irradiance.get_total_irradiance(
        surface_tilt=20,
        surface_azimuth=180,
        dni=irradiancia["dni"],
        ghi=irradiancia["ghi"],
        dhi=irradiancia["dhi"],
        solar_zenith=posicao_solar["apparent_zenith"],
        solar_azimuth=posicao_solar["azimuth"],
    )
    
    potencia_gerada = gerador["poa_global"] * potencia_kw / 1000 * eficiencia
    
    # Garantir que não ultrapasse a potência nominal
    curva = np.minimum(potencia_gerada.values, potencia_kw)
    
    # Garantir exatamente 1440 pontos
    if len(curva) < 1440:
        curva = np.pad(curva, (0, 1440 - len(curva)), mode="constant")
    elif len(curva) > 1440:
        curva = curva[:1440]
    
    return np.maximum(curva, 0.0)


def gerar_curvas_sazonais(
    latitude: float,
    longitude: float,
    potencia_kw: float,
    eficiencia: float = 0.8,
    estacoes: Optional[list] = None,
) -> Dict[str, np.ndarray]:
    """
    Gera curvas solares para todas as estações selecionadas.
    
    Args:
        latitude: Latitude do local
        longitude: Longitude do local
        potencia_kw: Potência nominal instalada (kWp)
        eficiencia: Eficiência do sistema (0 a 1)
        estacoes: Lista de estações a gerar (default: todas)
        
    Returns:
        Dict mapeando nome da estação -> np.ndarray(1440)
    """
    if estacoes is None:
        estacoes = list(DATAS_ESTACOES.keys())
    
    curvas = {}
    for estacao in estacoes:
        if estacao in DATAS_ESTACOES:
            curvas[estacao] = gerar_curva_solar_estacao(
                latitude=latitude,
                longitude=longitude,
                potencia_kw=potencia_kw,
                data=DATAS_ESTACOES[estacao],
                eficiencia=eficiencia,
            )
    
    return curvas
