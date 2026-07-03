from models.Microrrede import Carga
import numpy as np 



def CurvaCarga(carga:Carga):
    cargasFixa = carga.cargaFixa
    curva = np.zeros(1440)
    for cargaFixa in cargasFixa:
        curva_carga = Curva_carga(cargaFixa.potencia, cargaFixa.tempo_liga, cargaFixa.tempo_desliga)
        curva = [x+y for x,y in zip(curva, curva_carga)]
    return curva

def Curva_carga(potencia, tempo_liga, tempo_desliga, min_dia=1440):
    carga_array = np.zeros(min_dia)
    # Ensure indices are within bounds
    liga = max(0, min(int(tempo_liga), min_dia))
    desliga = max(0, min(int(tempo_desliga), min_dia))
    carga_array[liga:desliga] = potencia
    return carga_array