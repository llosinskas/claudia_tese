import pvlib
import pandas as pd 
from models.Microrrede import Solar
import json
def gerar_solar(potencia_kw,latitude, longitude,eficiencia=0.8, inicio="2026-02-04", fim="2026-02-04 23:59:59", freq='1min'):
    timezone = 'America/Sao_Paulo'
    local = pvlib.location.Location(latitude, longitude, 'America/Sao_Paulo')
    
    times = pd.date_range(start=inicio, end=fim, freq=freq, tz=timezone)
    
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

    potencia_gerada = gerador['poa_global'] * potencia_kw / 1000*eficiencia  # Convertir de W a kW
    return potencia_gerada


def Valor_solar(solar:Solar, cargas):
    acumulado=0 
    valores=[]
    alerta = ""
    curva_gerador =json.loads(solar.curva_geracao)

    custo_por_kWh = solar.custo_kwh
    custo_atual = 0
    for i, carga in enumerate(cargas):
    
        if curva_gerador[i]<carga:
            alerta="Não atende a carga"
            custo_atual=curva_gerador[i]*custo_por_kWh/60
            acumulado+=custo_atual
            valores.append(custo_atual)
        else:
            custo_atual=carga*custo_por_kWh/60
            acumulado+=custo_atual
            valores.append(custo_atual)
    return valores, acumulado, alerta