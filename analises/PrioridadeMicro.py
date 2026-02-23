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
from Tools.Diesel.Ferramentas_diesel import Preco_tanque_diesel
from Tools.Biogas.Ferramentas_biogas import Preco_tanque_biogas
from Tools.Bateria.Ferramentas_bateria import Cap_Day, Carregar_bateria, Tempo_Carga
import streamlit as st 
import json

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
            geracao_solar = json.loads(solar.curva_geracao)
            
            for i, geracao in enumerate(geracao_solar):
                geracao_float = pd.to_numeric(geracao, errors='coerce')
                if geracao_float > carga_instantanea[i]:
                    custo_solar = solar.custo_kwh*carga_instantanea[i]/60
                    resultado_solar.append(custo_solar)
                elif geracao_float<carga_instantanea[i]:
                    custo_solar = solar.custo_kwh*geracao_float/60
                    resultado_solar.append(custo_solar)
                    alerta_solar="O gerador não supri toda a demanda da carga"
            
            resultado_microrrede['Solar'] = resultado_solar
            total_solar = resultado_microrrede['Solar'].sum()
            st.write(alerta_solar)
            st.write(f"Custo de operar apenas com Gerador Solar R${total_solar:,.2f}")

        if microrrede.diesel!=None:
            diesel = Ler_Objeto(Diesel, microrrede.diesel_id)
            nivel = diesel.tanque
            alerta_diesel = "" 
            resultado_diesel = []
            
            for carga_instantanea in curva_carga:
                if carga_instantanea<diesel.potencia:
                    alerta_diesel, nivel, valor = Preco_tanque_diesel(nivel, carga_instantanea,diesel)
                    resultado_diesel.append(valor)    
                elif carga_instantanea > diesel.potencia:
                    alerta_diesel,nivel, valor = Preco_tanque_diesel(nivel, diesel.potencia, diesel)
                    resultado_diesel.append(valor)
                
            resultado_microrrede['Diesel'] = resultado_diesel
            total_diesel = resultado_microrrede['Diesel'].sum()
            
            st.write(alerta_diesel)
            st.write(f"Custo Diesel com apenas Gerador Diesel R${total_diesel:,.2f}")

        if microrrede.biogas != None:
            biogas = Ler_Objeto(Biogas, microrrede.biogas_id)
            nivel = biogas.tanque
            alerta_biogas=""
            resultado_biogas=[]
            for carga_instantanea in curva_carga:
                if carga_instantanea<biogas.potencia:
                    alerta_biogas, nivel, valor = Preco_tanque_biogas(nivel, carga_instantanea, biogas)
                    resultado_biogas.append(valor)
                elif carga_instantanea>biogas.potencia:
                    alerta_biogas, nivel, valor = Preco_tanque_biogas(nivel, biogas.potencia, biogas)
                    resultado_biogas.append(valor)
            resultado_microrrede["Biogas"] = resultado_biogas
            total_biogas = resultado_microrrede["Biogas"].sum()
            st.write(alerta_biogas)
            st.write(f"Custo Biogas com apenas uso do gerador Biogas R${total_biogas:,.2f}")

        st.dataframe(resultado_microrrede)
        
        resultado.append(resultado_microrrede)

    #st.dataframe(resultado)
    return resultado

def analise2( microrredes:Microrrede):
    
    for microrrede in microrredes:
        bateria = microrrede.bateria
        biogas = microrrede.biogas
        diesel = microrrede.diesel
        concessionaria = microrrede.concessionaria
        solar = microrrede.solar
        curva_solar = []    
        if solar != None:
            curva_solar = json.loads(solar.curva_geracao)
        st.subheader(f"{microrrede}")
        resultado_microrrede = pd.DataFrame(columns=['Carga', 'Bateria', 'Solar', 'Diesel', 'Biogas', 'Concessionaria'])
        carga = Ler_Objeto(Carga, microrrede.carga_id)
        curva_carga = CurvaCarga(carga)
        resultado_microrrede['Carga'] = curva_carga
        tempo_recarga_bateria = 0
        custo_kwh = pd.DataFrame()
        if bateria != None:     
            custo_kwh_bateria = bateria.custo_kwh
            custo_kwh.loc[0, 'Bateria'] = custo_kwh_bateria
            tempo_recarga_bateria = Tempo_Carga(bateria)
            nivel_instantaneo_bateria = bateria.capacidade
        elif bateria == None:
            custo_kwh.loc[0, 'Bateria'] = None
            
        if biogas != None:
            custo_kwh_biogas = biogas.custo_por_kWh
            custo_kwh.loc[0, 'Biogas'] = custo_kwh_biogas
        elif biogas == None:
            custo_kwh.loc[0, 'Biogas'] = None

        if diesel != None:
            custo_kwh_diesel = diesel.custo_por_kWh
            custo_kwh.loc[0, 'Diesel'] = custo_kwh_diesel
        elif diesel == None:
            custo_kwh.loc[0, 'Diesel'] = None
        #if concessionaria != None:
        #    custo_kwh_concessionaria = concessionaria.tarifa
        #    custo_kwh.loc[0, 'Concessionaria'] = custo_kwh_concessionaria
        #elif concessionaria == None:
        #    custo_kwh.loc[0, 'Concessionaria'] = None
        if solar != None:  
            custo_kwh_solar = solar.custo_kwh
            custo_kwh.loc[0, 'Solar'] = custo_kwh_solar
        elif solar == None:
            custo_kwh.loc[0, 'Solar'] = None
        custo_kwh_ordenado = custo_kwh.sort_values(by=0, axis=1)
        st.write("Custo por kWh de cada fonte de energia:")
        st.dataframe(custo_kwh)
        st.dataframe(custo_kwh_ordenado)
        
        nivel_bateria = np.zeros(len(curva_carga))
        nivel_biogas = np.zeros(len(curva_carga))
        nivel_diesel = np.zeros(len(curva_carga))
        


        uso_solar = np.zeros(len(curva_carga))
        uso_diesel=np.zeros(len(curva_carga))
        uso_biogas=np.zeros(len(curva_carga))   
        uso_bateria = np.zeros(len(curva_carga))
        uso_concessionaria = np.zeros(len(curva_carga))

        custo_solar = np.zeros(len(curva_carga))
        custo_diesel = np.zeros(len(curva_carga))
        custo_biogas = np.zeros(len(curva_carga))
        custo_bateria = np.zeros(len(curva_carga))
        custo_concessionaria = np.zeros(len(curva_carga))

        for i, carga_instantanea in enumerate(curva_carga):
            carga_necessaria = carga_instantanea
            
            for fonte in custo_kwh_ordenado.columns:
                if carga_necessaria <= 0:
                    break

                if fonte == 'Solar' and solar != None:
                    if curva_solar[i] >= carga_instantanea:
                        custo_solar[i] = carga_instantanea*solar.custo_kwh/60
                        uso_solar[i] = carga_instantanea
                        if bateria != None:
                            nivel, alerta, energia_rejeitada = Carregar_bateria(nivel, bateria, (curva_solar[i]-carga_instantanea))
                            uso_solar[i] = curva_solar[i]-energia_rejeitada
                            nivel_instantaneo_bateria = nivel
                        carga_necessaria = 0
                    elif curva_solar[i] < carga_instantanea:
                        custo_solar[i] = curva_solar[i]*solar.custo_kwh/600
                        carga_necessaria -= curva_solar[i]
                        uso_solar[i] = curva_solar[i]
            
                elif fonte == 'Bateria' and bateria != None and carga_necessaria > 0:
                    
                    if bateria.potencia >= carga_necessaria:
                        if nivel_instantaneo_bateria > bateria.capacidade_min:
                            custo_bateria[i] = carga_necessaria*bateria.custo_kwh/60
                            carga_necessaria = 0

                    elif bateria.potencia < carga_necessaria:
                        custo_bateria[i] = bateria.potencia*bateria.custo_kwh/60
                        carga_necessaria -= bateria.potencia
                
                
                elif fonte == 'Biogas' and biogas != None and carga_necessaria > 0:
                    if biogas.potencia >= carga_necessaria:
                        resultado_microrrede.loc[i, 'Biogas'] = carga_necessaria*biogas.custo_por_kWh/60
                        carga_necessaria = 0
                    elif biogas.potencia < carga_necessaria:
                        resultado_microrrede.loc[i, 'Biogas'] = biogas.potencia*biogas.custo_por_kWh/60
                        carga_necessaria -= biogas.potencia
                elif fonte == 'Diesel' and diesel != None and carga_necessaria > 0:
                    if diesel.potencia >= carga_necessaria:
                        resultado_microrrede.loc[i, 'Diesel'] = carga_necessaria*diesel.custo_por_kWh/60
                        carga_necessaria = 0
                    elif diesel.potencia < carga_necessaria:
                        resultado_microrrede.loc[i, 'Diesel'] = diesel.potencia*diesel.custo_por_kWh/60
                        carga_necessaria -= diesel.potencia
                elif fonte == 'Concessionaria' and concessionaria != None and carga_necessaria > 0:
                    resultado_microrrede.loc[i, 'Concessionaria'] = carga_necessaria*concessionaria.tarifa/60
                    carga_necessaria = 0
            
                
            # Caso não haja a bateria, não tem que otimizar a recarga da bateria 
            if bateria == None:
                pass
            # caso haja a bateria tem que otimizar a recarga da bateria, ou seja, usar a bateria para suprir a carga quando possível e recarregar a bateria quando houver excesso de geração solar ou quando o preço da concessionária for baixo
            # há bateria e solar, otimiza a recarga da bateria usando o excesso de geração solar para recarregar a bateria e usar a bateria para suprir a carga quando possível, caso contrário, compra da concessionária no final do dia
            elif bateria != None:
                nivel = bateria.capacidade
                if solar != None:
                    if carga_instantanea<curva_solar[i]:
                        curva_solar[i]  
                        
                elif solar == None:
                    pass

        uso_energia = pd.DataFrame({
            "Solar": uso_solar, 
            "Bateria": uso_bateria,
            "Biogas": uso_biogas,
            "Diesel": uso_diesel,
            "Concessionaria": uso_concessionaria
            
            })
        st.line_chart(uso_energia)
        
        
def analise3( microrrede:Microrrede):
    pass


if __name__ =="__main__":
    microrredes = Ler(Microrrede)
    for microrrede in microrredes:
        analise1(microrrede)
