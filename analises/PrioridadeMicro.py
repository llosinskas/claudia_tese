# Principal controle é o microgerenciamento do sistema de energia

# Rodar primeiro dia normalmente sem controle das cargas, depois analisar o perfil de consumo e ajustar as cargas com prioridade 2, 4
''' Análise 1
    Uso apenas de uma fonte de energia:
    -> se não conseguir alarme "não supri energia necessária"
    Análise 2  
    Otimiza a carga da bateria 
    Não desliza as cargas quando possível 
    Vende e compra da rede sem a interação com outras microrredes 

    Análise 3 
    Otimiza o carga da bateria
    Desliza as cargas quando possível 
    Vende e compra das microrredes 
'''
import pandas as pd 
import numpy as np 
from models.Microrrede import Microrrede, Balcao, Trade, Bateria, Diesel, Biogas, Solar, Carga, Concessionaria
from models.CRUD import Ler, Ler_Objeto
from Tools.GerarCurvaCarga import CurvaCarga
import streamlit as st 
def analise1( microrredes:Microrrede):
    
    resultado = []
    for microrrede in microrredes:
        st.subheader(f"{microrrede}")
        resultado_microrrede = pd.DataFrame(columns=['Carga', 'Bateria', 'Solar', 'Diesel', 'Biogas', 'Concessionaria'])
        carga = Ler_Objeto(Carga, microrrede.carga_id)
        curva_carga = CurvaCarga(carga)
        resultado_microrrede['Carga'] = curva_carga
        tota_carga = resultado_microrrede['Carga'].sum()
        concessionaria = Ler_Objeto(Concessionaria, microrrede.concessionaria_id)
        valor_concessionaria = []
        for carga_instantanea in curva_carga:
            valor = concessionaria.Preco_concessionaria(carga_instantanea)
            valor_concessionaria.append(valor)
        
        resultado_microrrede['Concessionaria'] = valor_concessionaria
        total_concessionaria = resultado_microrrede['Concessionaria'].sum()
        st.write(f"Cunsumo total diario {tota_carga:,.2f} kWh \n\
                 Custo de operar apenas pela rede R$ {total_concessionaria:,.2f}")
        if microrrede.bateria != None:
            bateria = Ler_Objeto(Bateria,microrrede.bateria_id)
            nivel = bateria.capacidade
            alerta_bateria = ""
            resultado_bateria = []
            for carga_instantanea in curva_carga:
                # A bateria supre toda a demanda
                if carga_instantanea<bateria.potencia: 
                    if nivel>bateria.capacidade_min:
                        nivel -= (carga_instantanea*bateria.eficiencia)/60 
                        custo_bateria = bateria.custo_kwh*carga_instantanea/60
                        resultado_bateria.append(custo_bateria)
                    else:
                        alerta_bateria = "Não consegue suprir a carga!"
                        resultado_bateria.append(0)
                elif carga_instantanea>bateria.potencia:
                    if nivel>bateria.capacidade_min:
                        nivel -= (bateria.potencia*bateria.eficiencia)/60 
                        custo_bateria = bateria.custo_kwh*bateria.potencia/60
                        resultado_bateria.append(custo_bateria)
                    else:
                        alerta_bateria = "Não consegue suprir a carga!"
                        resultado_bateria.append(0)

            resultado_microrrede['Bateria'] = resultado_bateria
            total_bateria = resultado_microrrede['Bateria'].sum()
            st.write(alerta_bateria)
            st.write(f"Custo de operar apenas com a bateria R${total_bateria:,.2f}")

        if microrrede.solar != None:
            solar = Ler_Objeto(Solar, microrrede.solar_id)
            resultado_solar=[]
            alerta_solar=""
            total_solar=0
            carga_instantanea = np.array(curva_carga, dtype=float)
            #geracao_solar = pd.to_numeric(solar.curva_geracao, errors='coerce')
            geracao_solar = solar.curva_geracao
            for i, geracao in enumerate(geracao_solar):
                geracao_float = pd.to_numeric(geracao, errors='coerce')
                if geracao_float > carga_instantanea[i-1]:
                    custo_solar = solar.custo_kwh*carga_instantanea[i-1]/60
                    resultado_solar.append(custo_solar)
                elif geracao_float<carga_instantanea[i-1]:
                    custo_solar = solar.custo_kwh*geracao_float/60
                    resultado_solar.append(custo_solar)
                    alerta_solar="O gerador não supri toda a demanda da carga"
            
            resultado_microrrede['Solar'] = resultado_solar
            total_solar = resultado_microrrede['Solar'].sum()
            st.write(alerta_solar)
            st.write(f"Custo de operar apenas com a bateria R${total_solar:,.2f}")
            

        if microrrede.diesel!=None:
            diesel = Ler_Objeto(Diesel, microrrede.diesel_id)
        if microrrede.biogas != None:
            biogas = Ler_Objeto(Biogas, microrrede.biogas_id)
       

        st.dataframe(resultado_microrrede)
        
        resultado.append(resultado_microrrede)

    #st.dataframe(resultado)
    return resultado

def analise2( microrrede:Microrrede):
    pass

def analise3( microrrede:Microrrede):
    pass


if __name__ =="__main__":
    microrredes = Ler(Microrrede)
    for microrrede in microrredes:
        analise1(microrrede)
