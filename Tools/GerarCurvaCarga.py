def Curva_carga(potencia, tempo_liga, tempo_desliga, min_dia=1440):
    carga_array = []
    for minuto in range(min_dia):
        if int(tempo_liga) <= minuto < int(tempo_desliga):
            carga_array.append(potencia)
        else:
            carga_array.append(0)
   
    return carga_array