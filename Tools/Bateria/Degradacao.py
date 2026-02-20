import numpy as np




# Ciclo de vida do banco de bateria 
def Cap_Day(n_ciclos, vida_bateria, capacidade_bateria):

    capacidade_bateria = []
    for n in range(n_ciclos+1):
        theeta =[]
        for day in range(int(vida_bateria[n])):
            theeta.append(((float(day)/vida_bateria[n])*90)*np.pi/180)
            capacidade = (20*np.exp(0.000258*(day))*np.cos(theeta[day]))+80
            capacidade =(capacidade*vida_bateria[n])/100
            if len(capacidade_bateria)<=(20*365)-1:
                capacidade_bateria.append(capacidade)
            else:
                break
    return capacidade_bateria





