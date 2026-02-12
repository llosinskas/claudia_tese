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
    carga_array = []
    for minuto in range(min_dia):
        if int(tempo_liga) <= minuto < int(tempo_desliga):
            carga_array.append(potencia)
        else:
            carga_array.append(0)
   
    return carga_array