import pvlib
import pandas as pd 
import json
from pydantic import BaseModel, Field, field_validator
from typing import List, Union, Optional

# ==========================================
# SCHEMAS (PYDANTIC)
# ==========================================
class GeracaoSolarRequest(BaseModel):
    potencia_kw: float = Field(..., gt=0, description="Potência instalada em kW")
    latitude: float
    longitude: float
    eficiencia: float = Field(0.8, ge=0, le=1.0)
    inicio: str = "2026-02-04"
    fim: str = "2026-02-04 23:59:59"
    freq: str = "1min"

class SolarModel(BaseModel):
    """Modelo Pydantic que substitui a dependência do SQLAlchemy para a lógica de negócio."""
    custo_kwh: float = Field(..., description="Custo de operação/manutenção por kWh")
    curva_geracao: Union[str, List[float]] = Field(..., description="Curva de geração em JSON string ou lista")

    @field_validator('curva_geracao')
    def parse_curva(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("curva_geracao deve ser um JSON válido se for string")
        return v

class ValorSolarResponse(BaseModel):
    valores: List[float]
    acumulado: float
    alerta: str
    curva_gerador: List[float]


# ==========================================
# FUNÇÕES DE NEGÓCIO
# ==========================================
def gerar_solar(request: GeracaoSolarRequest) -> List[float]:
    """Gera a curva de potência solar baseada na localização e tempo especificados."""
    timezone = 'America/Sao_Paulo'
    local = pvlib.location.Location(request.latitude, request.longitude, timezone)
    
    times = pd.date_range(start=request.inicio, end=request.fim, freq=request.freq, tz=timezone)
    
    posicao_solar = local.get_solarposition(times)
    irradiancia = local.get_clearsky(times)
    
    gerador = pvlib.irradiance.get_total_irradiance(
        surface_tilt=20,
        surface_azimuth=180,
        dni=irradiancia['dni'],
        ghi=irradiancia['ghi'],
        dhi=irradiancia['dhi'],
        solar_zenith=posicao_solar['apparent_zenith'],
        solar_azimuth=posicao_solar['azimuth']
    )

    potencia_gerada = gerador['poa_global'] * request.potencia_kw / 1000 * request.eficiencia
    
    # Retorna como lista para fácil serialização na API FastAPI
    return potencia_gerada.tolist()


def Valor_solar(solar: SolarModel, cargas: List[float]) -> ValorSolarResponse:
    """Calcula os custos de operação da fonte solar frente à uma curva de cargas."""
    acumulado = 0.0 
    valores = []
    alerta = ""
    
    curva_gerador = solar.curva_geracao
    custo_por_kWh = solar.custo_kwh
    
    for i, carga in enumerate(cargas):
        # Proteção caso a curva geradora seja menor que a curva de cargas
        if i >= len(curva_gerador):
            break
            
        geracao_minuto = curva_gerador[i]
        
        if geracao_minuto < carga:
            alerta = "Não atende a carga"
            custo_atual = geracao_minuto * custo_por_kWh / 60
        else:
            custo_atual = carga * custo_por_kWh / 60
            
        acumulado += custo_atual
        valores.append(custo_atual)
            
    return ValorSolarResponse(
        valores=valores,
        acumulado=acumulado,
        alerta=alerta,
        curva_gerador=curva_gerador
    )