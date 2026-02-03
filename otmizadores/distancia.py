import numpy as np 
from math import radians, cos, sin, asin, sqrt

# Formula de Haversine para calcular a distância entre dois pontos geográficos
def distancia_haversine(lat1, lon1, lat2, lon2):
    # Converte graus para radianos
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Diferenças
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    
    # Fórmula de Haversine
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    
    # Raio da Terra em quilômetros (use 3956 para milhas)
    r = 6371.0 
    distancia = c * r
    return distancia