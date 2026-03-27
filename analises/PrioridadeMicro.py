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

    Análsise 4 
    Otimiza o carga da bateria
    Desliza as cargas quando possível 
    Otimiza pelo custo global de energia
    Vende e compra das microrredes 

'''
import pandas as pd 
import numpy as np 
from Tools.Carga.Ferramentas_cargas import Otimizado
from models.Microrrede import Microrrede, Balcao, Trade, Bateria, Diesel, Biogas, Solar, Carga
from models.CRUD import Ler, Ler_Objeto
from Tools.GerarCurvaCarga import CurvaCarga
from Tools.Diesel.Ferramentas_diesel import Consumo_diesel, Preco_tanque_diesel
from Tools.Biogas.Ferramentas_biogas import Consumo_biogas, Geracao_biogas_instantanea, Preco_tanque_biogas
from Tools.Bateria.Ferramentas_bateria import Carregar_bateria, Descarrega_bateria, Tempo_Carga
import streamlit as st 
import json
from Tools.Graficos.Sankey_Chart import sankey_chart
from otmizadores.milp_controle_microrrede import analise_milp as analise_milp_func, MILPMicrorredes
from otmizadores.pso import analise_pso as analise_pso_func, PSOMicrorredes

def analise_1(microrrede: Microrrede):
    resultado_microrrede = pd.DataFrame(columns=['Carga', 'Bateria', 'Solar', 'Diesel', 'Biogas', 'Concessionaria'])
    carga = microrrede.carga
    curva_carga = CurvaCarga(carga)
    resultado_microrrede['Carga'] = curva_carga
    total_carga = resultado_microrrede['Carga'].sum()
    concessionaria = microrrede.concessionaria
    valor_concessionaria = np.zeros(1440)
    for i,carga_instantanea in enumerate(curva_carga):
        valor = concessionaria.Preco_concessionaria(carga_instantanea)
        valor_concessionaria[i] = (valor)
    resultado_microrrede['Concessionaria'] = valor_concessionaria
    total_concessionaria = resultado_microrrede['Concessionaria'].sum()
 
    nivel_bateria       = 0.0
    alerta_bateria      = ""
    resultado_bateria   = np.zeros(1440)
    total_bateria       = 0.0
     
    alerta_solar        = ""
    resultado_solar     = np.zeros(1440)
    total_solar         = 0.0
    total_solar         = 0.0

    alerta_diesel       = ""
    nivel_diesel        = 0.0   
    resultado_diesel    = np.zeros(1440)
    total_diesel        = 0.0

    alerta_biogas       = ""
    resultado_biogas    = np.zeros(1440)
    total_biogas        = 0.0
    
    if microrrede.bateria != None:
        bateria = microrrede.bateria
        nivel_bateria = bateria.capacidade
        for i,carga_instantanea in enumerate(curva_carga):
            # A bateria supre toda a demanda
            if carga_instantanea<bateria.potencia: 
                if nivel_bateria>bateria.capacidade_min:
                    nivel_bateria -= (carga_instantanea*bateria.eficiencia)/60 
                    custo_bateria = bateria.custo_kwh*carga_instantanea/60
                    resultado_bateria[i] = custo_bateria
                else:
                    alerta_bateria = "Não consegue suprir a carga!"
                    
            elif carga_instantanea>bateria.potencia:
                if nivel_bateria>bateria.capacidade_min:
                    nivel_bateria -= (bateria.potencia*bateria.eficiencia)/60 
                    custo_bateria = bateria.custo_kwh*bateria.potencia/60
                    resultado_bateria[i] = custo_bateria
                else:
                    alerta_bateria = "Não consegue suprir a carga!"
                    
        resultado_microrrede['Bateria'] = resultado_bateria
        total_bateria = resultado_microrrede['Bateria'].sum()
   
    if microrrede.solar != None:
        solar = microrrede.solar
        carga_instantanea = np.array(curva_carga, dtype=float)
        geracao_solar = json.loads(solar.curva_geracao)
        
        if len(geracao_solar) == len(carga_instantanea):
            for i, geracao in enumerate(geracao_solar):
                geracao_float = pd.to_numeric(geracao, errors='coerce')
                if geracao_float > carga_instantanea[i]:
                    custo_solar = solar.custo_kwh*carga_instantanea[i]/60
                    resultado_solar[i] = custo_solar
                elif geracao_float<carga_instantanea[i]:
                    custo_solar = solar.custo_kwh*geracao_float/60
                    resultado_solar[i]=custo_solar
                    alerta_solar="O gerador não supri toda a demanda da carga"
        else:
            alerta_solar="Erro na leitura dos dados do gerador solar"
        
        resultado_microrrede['Solar'] = resultado_solar
        total_solar = resultado_microrrede['Solar'].sum()
    
    if microrrede.diesel!=None:
            diesel = microrrede.diesel
            nivel_diesel = diesel.tanque
            
            for i,carga_instantanea in enumerate(curva_carga):
                if carga_instantanea<diesel.potencia:
                    alerta_diesel, nivel_diesel, valor = Preco_tanque_diesel(nivel_diesel, carga_instantanea,diesel)
                    resultado_diesel[i]=valor
                elif carga_instantanea > diesel.potencia:
                    alerta_diesel,nivel_diesel, valor = Preco_tanque_diesel(nivel_diesel, diesel.potencia, diesel)
                    resultado_diesel[i]=valor
                
            resultado_microrrede['Diesel'] = resultado_diesel
            total_diesel = resultado_microrrede['Diesel'].sum()
            
    if microrrede.biogas != None:
            biogas = microrrede.biogas
            nivel = biogas.tanque
            
            for i,carga_instantanea in enumerate(curva_carga):
                if carga_instantanea<biogas.potencia:
                    alerta_biogas, nivel, valor = Preco_tanque_biogas(nivel, carga_instantanea, biogas)
                    resultado_biogas[i] = valor
                elif carga_instantanea>biogas.potencia:
                    alerta_biogas, nivel, valor = Preco_tanque_biogas(nivel, biogas.potencia, biogas)
                    resultado_biogas[i] = valor
                
            resultado_microrrede["Biogas"] = resultado_biogas
            total_biogas = resultado_microrrede["Biogas"].sum()
    
    return total_carga, total_concessionaria,alerta_bateria, total_bateria,alerta_solar, total_solar, alerta_diesel, total_diesel, alerta_biogas, total_biogas,resultado_microrrede

def analise_2(microrrede: Microrrede):
    bateria = microrrede.bateria
    biogas = microrrede.biogas
    diesel = microrrede.diesel
    concessionaria = microrrede.concessionaria
    solar = microrrede.solar
    curva_solar = []    
    if solar != None:
        curva_solar = json.loads(solar.curva_geracao)
    resultado_microrrede = pd.DataFrame(columns=['Carga', 'Bateria', 'Solar', 'Diesel', 'Biogas', 'Concessionaria'])
    carga = microrrede.carga
    curva_carga = CurvaCarga(carga)
    resultado_microrrede['Carga'] = curva_carga
    tempo_recarga_bateria = 0  
    custo_kwh = pd.DataFrame()
    geracao_biogas = 0
    nivel_instantaneo_biogas = 0
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
        geracao_biogas = Geracao_biogas_instantanea(biogas)
        nivel_instantaneo_biogas = biogas.tanque

    elif biogas == None:
        custo_kwh.loc[0, 'Biogas'] = None
            
    if diesel != None:
        custo_kwh_diesel = diesel.custo_por_kWh
        custo_kwh.loc[0, 'Diesel'] = custo_kwh_diesel
        nivel_instantaneo_diesel = diesel.tanque
    elif diesel == None:
        custo_kwh.loc[0, 'Diesel'] = None
    if solar != None:  
        custo_kwh_solar = solar.custo_kwh
        custo_kwh.loc[0, 'Solar'] = custo_kwh_solar
    elif solar == None:
        custo_kwh.loc[0, 'Solar'] = None
    custo_kwh_ordenado = custo_kwh.sort_values(by=0, axis=1)
    nivel_bateria = np.zeros(len(curva_carga))
    nivel_biogas = np.zeros(len(curva_carga))
    nivel_diesel = np.zeros(len(curva_carga))
    
    uso_solar = np.zeros(len(curva_carga))
    uso_diesel=np.zeros(len(curva_carga))
    uso_biogas=np.zeros(len(curva_carga))   
    uso_bateria = np.zeros(len(curva_carga))
    uso_concessionaria = np.zeros(len(curva_carga))
    total_carga = 0
    sobra = []
    total_sobra = 0
    sum_fontes = np.zeros(len(curva_carga))
    custo_solar = np.zeros(len(curva_carga))
    custo_diesel = np.zeros(len(curva_carga))
    custo_biogas = np.zeros(len(curva_carga))
    custo_bateria = np.zeros(len(curva_carga))
    custo_concessionaria = np.zeros(len(curva_carga))
    custo_total_instantaneo = np.zeros(len(curva_carga))
    custo_total = 0
    for i, carga_instantanea in enumerate(curva_carga):
        carga_necessaria = carga_instantanea
        total_carga += carga_instantanea
        if biogas != None:
            if nivel_instantaneo_biogas < biogas.tanque:
                nivel_instantaneo_biogas += geracao_biogas
            nivel_biogas[i] = nivel_instantaneo_biogas
        if diesel != None:
            nivel_diesel[i] = nivel_instantaneo_diesel

        for fonte in custo_kwh_ordenado.columns:
            if carga_necessaria <= 0:
                break
            
            match fonte:
                case 'Solar':

                    if solar != None:
                        if curva_solar[i] >= carga_necessaria:
                            uso_solar[i] = carga_necessaria
                            custo_solar[i] = uso_solar[i]*solar.custo_kwh/60
                            carga_necessaria = 0
                            if bateria != None:
                                nivel_instantaneo_bateria, alerta, energia_rejeitada = Carregar_bateria(nivel_instantaneo_bateria, bateria, (curva_solar[i]-carga_necessaria)/60)
                                nivel_bateria[i] = nivel_instantaneo_bateria/60

                        elif curva_solar[i] < carga_necessaria:
                            custo_solar[i] = curva_solar[i]*solar.custo_kwh/60
                            uso_solar[i] = curva_solar[i]
                            carga_necessaria -= uso_solar[i]

                case 'Bateria':
                    if bateria != None:
                        if bateria.potencia >= carga_necessaria:
                            if nivel_instantaneo_bateria > bateria.capacidade_min:
                                
                                # uso_bateria[i] = carga_necessaria/(bateria.eficiencia/100)/60
                                uso_bateria[i] = carga_necessaria
                                custo_bateria[i] = uso_bateria[i]*bateria.custo_kwh/60
                                nivel_instantaneo_bateria = Descarrega_bateria(nivel_instantaneo_bateria, carga_necessaria/60, bateria)
                                nivel_bateria[i] = nivel_instantaneo_bateria
                                carga_necessaria = 0


                        elif bateria.potencia < carga_necessaria:
                            if nivel_instantaneo_bateria > bateria.capacidade_min:
                                uso_bateria[i] = bateria.potencia
                                custo_bateria[i] = uso_bateria[i]*bateria.custo_kwh/60
                                nivel_instantaneo_bateria = Descarrega_bateria(nivel_instantaneo_bateria, bateria.potencia/60, bateria)
                                nivel_bateria[i] = nivel_instantaneo_bateria                               
                                carga_necessaria -= bateria.potencia

                case 'Biogas':
                    if biogas != None:
                        if biogas.potencia >= carga_necessaria:
                            if nivel_instantaneo_biogas > 0:
                                uso_biogas[i] = carga_necessaria
                                custo_biogas[i] = uso_biogas[i]*biogas.custo_por_kWh/60
                                alerta, nivel_instantaneo_biogas,consumo=Consumo_biogas(nivel_instantaneo_biogas, carga_necessaria, biogas)

                                carga_necessaria = 0

                        elif biogas.potencia < carga_necessaria:
                            if nivel_instantaneo_biogas > 0:
                                uso_biogas[i] = biogas.potencia
                                custo_biogas[i] = uso_biogas[i]*biogas.custo_por_kWh/60
                                nivel_instantaneo_biogas -= uso_biogas[i]/60
                            carga_necessaria -= biogas.potencia
                case 'Diesel':
                    if fonte == 'Diesel' and diesel != None:
                        if diesel.potencia >= carga_necessaria:
                            if nivel_instantaneo_diesel > 0:
                                uso_diesel[i] = carga_necessaria    
                                custo_diesel[i] = uso_diesel[i]*diesel.custo_por_kWh/60
                                alerta, nivel_instantaneo_diesel, consumo = Consumo_diesel(nivel_instantaneo_diesel, carga_necessaria, diesel)
                                carga_necessaria = 0
                        
                        elif diesel.potencia < carga_necessaria:
                            if nivel_instantaneo_diesel > 0:
                                uso_diesel[i] = diesel.potencia
                                custo_diesel[i] = uso_diesel[i]*diesel.custo_por_kWh/60
                                alerta, nivel_instantaneo_diesel, consumo = Consumo_diesel(nivel_instantaneo_diesel, uso_diesel[i], diesel)
                                carga_necessaria -= diesel.potencia
            
        # Sobra de energia (venda para a rede)
        sobra_instantanea = 0
        if diesel != None:
            sobra_instantanea = diesel.potencia
        elif biogas != None:
            sobra_instantanea += biogas.potencia
        elif bateria != None:
            sobra_instantanea += bateria.potencia
        elif solar != None:
            sobra_instantanea += curva_solar[i]

        if sobra_instantanea > carga_instantanea:
            sobra.append(sobra_instantanea - carga_instantanea)
        
        custo_total_instantaneo[i] = custo_solar[i] + custo_bateria[i] + custo_biogas[i] + custo_diesel[i]+ custo_concessionaria[i]
        
        # Falta de energia (Compra da rede)            
        sum_fontes[i] = (uso_bateria[i]+uso_biogas[i]+uso_diesel[i]+uso_solar[i])
        
        falta = curva_carga[i] - (uso_bateria[i]+uso_biogas[i]+uso_diesel[i]+uso_solar[i])   
        if curva_carga[i] >= falta:
            uso_concessionaria[i] = falta
            custo_concessionaria[i] = uso_concessionaria[i]*concessionaria.tarifa/60
      
    total_uso_solar = uso_solar.sum()
    total_uso_bateria = uso_bateria.sum()
    total_uso_biogas = uso_biogas.sum()
    total_uso_diesel = uso_diesel.sum()
    total_uso_concessionaria = uso_concessionaria.sum()
    total_sobra = sum(sobra)
    
    total = pd.DataFrame({
        "Solar": total_uso_solar, 
        "Bateria": total_uso_bateria,
        "Biogas": total_uso_biogas,
        "Diesel": total_uso_diesel,
        "Concessionaria": total_uso_concessionaria,
        "Sobra": total_sobra
        }, index=[0])
    demanda_negativa = -np.abs(curva_carga)
    uso_energia = pd.DataFrame({
        "Solar": uso_solar, 
        "Bateria": uso_bateria,
        "Biogas": uso_biogas,
        "Diesel": uso_diesel,
        "Concessionaria": uso_concessionaria,
        "Carga": demanda_negativa
        })
    niveis_tanques = pd.DataFrame({
        "Bateria": nivel_bateria, 
        "Biogas": nivel_biogas,
        "Diesel": nivel_diesel,
        })

    custo_total = custo_total_instantaneo.sum()

    return custo_kwh_ordenado, total_uso_diesel, total_uso_bateria, total_uso_concessionaria, total_uso_biogas, total_uso_solar, total_sobra, total_carga, total, uso_energia, niveis_tanques, custo_total, custo_total_instantaneo


# Deslizar as cargas para os horários de menor custo, priorizando o uso das fontes mais baratas, e otimizando o uso da bateria para suprir os picos de carga.    
def analise3( microrredes:Microrrede):
    
    for microrrede in microrredes:
        st.subheader(f"{microrrede}")

        bateria = microrrede.bateria
        biogas = microrrede.biogas
        diesel = microrrede.diesel
        concessionaria = microrrede.concessionaria
        solar = microrrede.solar
        
        curva_solar = []    
        if solar != None:
            curva_solar = json.loads(solar.curva_geracao)
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
            geracao_biogas = Geracao_biogas_instantanea(biogas)
            nivel_instantaneo_biogas = biogas.tanque

        elif biogas == None:
            custo_kwh.loc[0, 'Biogas'] = None
            
        if diesel != None:
            custo_kwh_diesel = diesel.custo_por_kWh
            custo_kwh.loc[0, 'Diesel'] = custo_kwh_diesel
            nivel_instantaneo_diesel = diesel.tanque
        elif diesel == None:
            custo_kwh.loc[0, 'Diesel'] = None
        if solar != None:  
            custo_kwh_solar = solar.custo_kwh
            custo_kwh.loc[0, 'Solar'] = custo_kwh_solar
        elif solar == None:
            custo_kwh.loc[0, 'Solar'] = None
        custo_kwh_ordenado = custo_kwh.sort_values(by=0, axis=1)
        st.write("Custo por kWh de cada fonte de energia:")
        st.dataframe(custo_kwh_ordenado, hide_index=True)
        
        nivel_bateria = np.zeros(len(curva_carga))
        nivel_biogas = np.zeros(len(curva_carga))
        nivel_diesel = np.zeros(len(curva_carga))
        
        uso_solar = np.zeros(len(curva_carga))
        uso_diesel=np.zeros(len(curva_carga))
        uso_biogas=np.zeros(len(curva_carga))   
        uso_bateria = np.zeros(len(curva_carga))
        uso_concessionaria = np.zeros(len(curva_carga))
        total_carga = 0
        sobra = []
        total_sobra = 0


        custo_solar = np.zeros(len(curva_carga))
        custo_diesel = np.zeros(len(curva_carga))
        custo_biogas = np.zeros(len(curva_carga))
        custo_bateria = np.zeros(len(curva_carga))
        custo_concessionaria = np.zeros(len(curva_carga))
        custo_total_instantaneo = np.zeros(len(curva_carga))
        custo_total = 0    

        for i, carga_instantanea in enumerate(curva_carga):
            carga_necessaria = carga_instantanea
            total_carga += carga_instantanea
            if biogas != None:
                if nivel_instantaneo_biogas < biogas.tanque:
                    nivel_instantaneo_biogas += geracao_biogas
                nivel_biogas[i] = nivel_instantaneo_biogas
            if diesel != None:
                nivel_diesel[i] = nivel_instantaneo_diesel

            for fonte in custo_kwh_ordenado.columns:
                if carga_necessaria <= 0:
                    break
                
                match fonte:
                    case 'Solar':

                        if solar != None:
                            if curva_solar[i] >= carga_necessaria:
                                uso_solar[i] = carga_necessaria
                                custo_solar[i] = uso_solar[i]*solar.custo_kwh/60
                                carga_necessaria = 0
                                if bateria != None:
                                    nivel_instantaneo_bateria, alerta, energia_rejeitada = Carregar_bateria(nivel_instantaneo_bateria, bateria, (curva_solar[i]-carga_necessaria)/60)
                                    nivel_bateria[i] = nivel_instantaneo_bateria/60

                            elif curva_solar[i] < carga_necessaria:
                                custo_solar[i] = curva_solar[i]*solar.custo_kwh/60
                                uso_solar[i] = curva_solar[i]
                                carga_necessaria -= uso_solar[i]

                    case 'Bateria':
                        if bateria != None:
                            if bateria.potencia >= carga_necessaria:
                                if nivel_instantaneo_bateria > bateria.capacidade_min:
                                    
                                    # uso_bateria[i] = carga_necessaria/(bateria.eficiencia/100)/60
                                    uso_bateria[i] = carga_necessaria
                                    custo_bateria[i] = uso_bateria[i]*bateria.custo_kwh/60
                                    nivel_instantaneo_bateria = Descarrega_bateria(nivel_instantaneo_bateria, carga_necessaria/60, bateria)
                                    nivel_bateria[i] = nivel_instantaneo_bateria
                                    carga_necessaria = 0


                            elif bateria.potencia < carga_necessaria:
                                if nivel_instantaneo_bateria > bateria.capacidade_min:
                                    uso_bateria[i] = bateria.potencia
                                    custo_bateria[i] = uso_bateria[i]*bateria.custo_kwh/60
                                    nivel_instantaneo_bateria = Descarrega_bateria(nivel_instantaneo_bateria, bateria.potencia/60, bateria)
                                    nivel_bateria[i] = nivel_instantaneo_bateria                               
                                    carga_necessaria -= bateria.potencia

                    case 'Biogas':
                        if biogas != None:
                            if biogas.potencia >= carga_necessaria:
                                if nivel_instantaneo_biogas > 0:
                                    uso_biogas[i] = carga_necessaria
                                    custo_biogas[i] = uso_biogas[i]*biogas.custo_por_kWh/60
                                    alerta, nivel_instantaneo_biogas,consumo=Consumo_biogas(nivel_instantaneo_biogas, carga_necessaria, biogas)

                                    carga_necessaria = 0

                            elif biogas.potencia < carga_necessaria:
                                if nivel_instantaneo_biogas > 0:
                                    uso_biogas[i] = biogas.potencia
                                    custo_biogas[i] = uso_biogas[i]*biogas.custo_por_kWh/60
                                    nivel_instantaneo_biogas -= uso_biogas[i]/60
                                carga_necessaria -= biogas.potencia
                    case 'Diesel':
                        if fonte == 'Diesel' and diesel != None:
                            if diesel.potencia >= carga_necessaria:
                                if nivel_instantaneo_diesel > 0:
                                    uso_diesel[i] = carga_necessaria    
                                    custo_diesel[i] = uso_diesel[i]*diesel.custo_por_kWh/60
                                    alerta, nivel_instantaneo_diesel, consumo = Consumo_diesel(nivel_instantaneo_diesel, carga_necessaria, diesel)
                                    carga_necessaria = 0
                            
                            elif diesel.potencia < carga_necessaria:
                                if nivel_instantaneo_diesel > 0:
                                    uso_diesel[i] = diesel.potencia
                                    custo_diesel[i] = uso_diesel[i]*diesel.custo_por_kWh/60
                                    alerta, nivel_instantaneo_diesel, consumo = Consumo_diesel(nivel_instantaneo_diesel, uso_diesel[i], diesel)
                                    carga_necessaria -= diesel.potencia
                
                # Sobra de energia (venda para a rede)
                sobra_instantanea = 0
                if diesel != None:
                    sobra_instantanea = diesel.potencia
                elif biogas != None:
                    sobra_instantanea += biogas.potencia
                elif bateria != None:
                    sobra_instantanea += bateria.potencia
                elif solar != None:
                    sobra_instantanea += curva_solar[i]

                if sobra_instantanea > carga_instantanea:
                    sobra.append(sobra_instantanea - carga_instantanea)
                
                custo_total_instantaneo[i] = custo_solar[i] + custo_bateria[i] + custo_biogas[i] + custo_diesel[i]+ custo_concessionaria[i]
                
                # Falta de energia (Compra da rede)            
                falta = curva_carga[i] - (uso_bateria[i]+uso_biogas[i]+uso_diesel[i]+uso_solar[i])   
                if curva_carga[i] >= falta:
                    uso_concessionaria[i] = falta
                    custo_concessionaria[i] = uso_concessionaria[i]*concessionaria.tarifa/60
                    
        
        total_uso_solar = uso_solar.sum()
        total_uso_bateria = uso_bateria.sum()
        total_usio_biogas = uso_biogas.sum()
        total_uso_diesel = uso_diesel.sum()
        total_uso_concessionaria = uso_concessionaria.sum()
        total_sobra = sum(sobra)
        sankey_chart(uso_diesel=total_uso_diesel, uso_bateria=total_uso_bateria, uso_concessionaria=total_uso_concessionaria, uso_biogas=total_usio_biogas, uso_solar=total_uso_solar, sobra=total_sobra, carga=total_carga)
        total = pd.DataFrame({
            "Solar": total_uso_solar, 
            "Bateria": total_uso_bateria,
            "Biogas": total_usio_biogas,
            "Diesel": total_uso_diesel,
            "Concessionaria": total_uso_concessionaria,
            "Sobra": total_sobra
            }, index=[0])
        st.dataframe(total.style.format("{:,.2f} kWh"))

        uso_energia = pd.DataFrame({
            "Solar": uso_solar, 
            "Bateria": uso_bateria,
            "Biogas": uso_biogas,
            "Diesel": uso_diesel,
            "Concessionaria": uso_concessionaria,
            "Carga": curva_carga
            })
        st.line_chart(uso_energia)
        niveis_tanques = pd.DataFrame({
            "Bateria": nivel_bateria, 
            "Biogas": nivel_biogas,
            "Diesel": nivel_diesel,
            })
        st.line_chart(niveis_tanques)
        custo_total = custo_total_instantaneo.sum()
        st.subheader("Custo de energia da microrrede para operar")
        st.write(f"Custo total da microrrede: R$ {custo_total:,.2f}")
        st.line_chart(custo_total_instantaneo)

def analise4( microrredes:Microrrede):
    for microrrede in microrredes:
        st.subheader(f"{microrrede}")
        curva_custo, curva_custo_otimizado = Otimizado(microrrede)   
        curva_custo_total = curva_custo.sum()
        st.write(f"Curva de custo da microrrede sem otimização: R$ {curva_custo_total:,.2f}")
        curva_custo_otimizado_total = curva_custo_otimizado.sum()
        st.write(f"Curva de custo da microrrede com otimização: R$ {curva_custo_otimizado_total:,.2f}")
        
        df  = pd.DataFrame({
            "Curva de custo sem otimização": curva_custo,
            "Curva de custo com otimização": curva_custo_otimizado
        })
        st.line_chart(df, x_label="Tempo (min)", y_label="Potência (kW)")


def analise_5_milp(microrrede: Microrrede):
    """
    Análise 5 - MILP
    Otimiza o controle da microrrede usando Mixed Integer Linear Programming
    
    Características:
    - Minimiza custo total operacional
    - Otimiza o despacho de todas as fontes de energia
    - Controla carregamento/descarregamento da bateria
    - Gerencia níveis de combustível (diesel, biogas)
    - Considera venda de excedente de energia para a rede
    - Respeita restrições de potência de cada fonte
    """
    st.subheader("Análise 5: Otimização MILP")
    st.write("""
    Esta análise utiliza **Mixed Integer Linear Programming (MILP)** para otimizar 
    o controle da microrrede. O modelo minimiza o custo operacional total considerando:
    - Custos de geração de cada fonte (Solar, Diesel, Biogas, Bateria)
    - Custo de compra da concessionária
    - Receita de venda de excedentes
    - Restrições de capacidade e operação de cada fonte
    - Dinâmica dos sistemas de armazenamento (bateria, tanques)
    """)
    
    with st.spinner("Otimizando microrrede com MILP..."):
        # Executar otimização MILP
        df_resultado, custos, solucao = analise_milp_func(microrrede)
        
        if df_resultado is None:
            st.error("❌ Não foi possível resolver o modelo MILP")
            return
        
        # ===== RESUMO DE CUSTOS =====
        st.subheader("📊 Resumo de Custos")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Solar", f"R$ {custos.get('Solar', 0):,.2f}")
        with col2:
            st.metric("Bateria", f"R$ {custos.get('Bateria', 0):,.2f}")
        with col3:
            st.metric("Diesel", f"R$ {custos.get('Diesel', 0):,.2f}")
        with col4:
            st.metric("Biogas", f"R$ {custos.get('Biogas', 0):,.2f}")
        
        col5, col6, col7 = st.columns(3)
        
        with col5:
            st.metric("Concessionária", f"R$ {custos.get('Concessionaria', 0):,.2f}")
        with col6:
            st.metric("Receita Venda", f"R$ {custos.get('Receita_Venda', 0):,.2f}")
        with col7:
            st.metric("**CUSTO TOTAL**", f"R$ {custos.get('Total', 0):,.2f}", 
                     delta=None, delta_color="inverse")
        
        # ===== USO DE ENERGIA POR FONTE =====
        st.subheader("⚡ Despacho de Energia")
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de barras com uso por fonte
            totais_uso = {
                'Solar': df_resultado['Solar'].sum(),
                'Bateria': df_resultado['Bateria'].sum(),
                'Diesel': df_resultado['Diesel'].sum(),
                'Biogas': df_resultado['Biogas'].sum(),
                'Concessionária': df_resultado['Concessionaria'].sum(),
            }
            df_totais = pd.DataFrame({
                'Fonte': list(totais_uso.keys()),
                'Energia (kWh)': list(totais_uso.values())
            })
            st.bar_chart(df_totais.set_index('Fonte'), width=400, height=300)
        
        with col2:
            # Tabela de resumo
            st.write("**Resumo de Uso por Fonte:**")
            df_resumo = pd.DataFrame({
                'Fonte': ['Solar', 'Bateria', 'Diesel', 'Biogas', 'Concessionária', 'Venda'],
                'Energia (kWh)': [
                    f"{df_resultado['Solar'].sum():.2f}",
                    f"{df_resultado['Bateria'].sum():.2f}",
                    f"{df_resultado['Diesel'].sum():.2f}",
                    f"{df_resultado['Biogas'].sum():.2f}",
                    f"{df_resultado['Concessionaria'].sum():.2f}",
                    f"{df_resultado['Venda'].sum():.2f}",
                ]
            })
            st.dataframe(df_resumo, hide_index=True)
        
        # ===== SÉRIES TEMPORAIS =====
        st.subheader("📈 Evolução Temporal")
        
        # Uso diário de cada fonte
        tab1, tab2, tab3 = st.tabs(["Despacho em Tempo Real", "Níveis de Armazenamento", "Custos Instantâneos"])
        
        with tab1:
            df_uso = pd.DataFrame({
                'Solar': df_resultado['Solar'],
                'Bateria': df_resultado['Bateria'],
                'Diesel': df_resultado['Diesel'],
                'Biogas': df_resultado['Biogas'],
                'Concessionária': df_resultado['Concessionaria'],
                'Carga': df_resultado['Carga']
            })
            st.line_chart(df_uso, width=None, height=400)
            st.caption("Despacho de energia de cada fonte ao longo do dia")
        
        with tab2:
            df_niveis = pd.DataFrame({
                'Bateria (kWh)': solucao['Nivel_Bateria'][:-1],
                'Diesel (L)': solucao['Nivel_Diesel'][:-1],
                'Biogas (m³)': solucao['Nivel_Biogas'][:-1]
            })
            st.line_chart(df_niveis, width=None, height=400)
            st.caption("Evolução dos níveis de armazenamento")
        
        with tab3:
            df_custos = pd.DataFrame({
                'Custo Total': solucao.get('Custo_Total_Instante', np.zeros(len(df_resultado)))
            })
            st.line_chart(df_custos, width=None, height=400)
            st.caption("Custo operacional instantâneo")
        
        # ===== ESTATÍSTICAS =====
        st.subheader("📋 Estatísticas")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            carga_total = df_resultado['Carga'].sum()
            st.metric("Demanda Total", f"{carga_total:.2f} kWh")
        
        with col2:
            # Taxa de cobertura local (não da rede)
            cobertura_local = ((carga_total - df_resultado['Concessionaria'].sum()) / carga_total * 100) if carga_total > 0 else 0
            st.metric("Cobertura Local", f"{cobertura_local:.1f}%")
        
        with col3:
            # Aproveitamento solar
            aproveitamento = (df_resultado['Solar'].sum() / (df_resultado['Solar'].sum() + df_resultado['Venda'].sum()) * 100) if (df_resultado['Solar'].sum() + df_resultado['Venda'].sum()) > 0 else 0
            st.metric("Aproveit. Solar", f"{aproveitamento:.1f}%")
        
        with col4:
            # Taxa de autossuficiência energética
            energia_propria = carga_total - df_resultado['Concessionaria'].sum()
            autossuficiencia = (energia_propria / carga_total * 100) if carga_total > 0 else 0
            st.metric("Autossuficiência", f"{autossuficiencia:.1f}%")
        
        # Comparação com análise anterior
        st.subheader("🔄 Comparação com Análise 4")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Custo Análise 4 (Heurística):** R$ X.XX")
            st.write("**Custo Análise 5 (MILP):** R$ {:.2f}".format(custos.get('Total', 0)))
        
        with col2:
            economia = 0  # Seria calculado comparando com análise 4
            if economia >= 0:
                st.success(f"**Economia com MILP:** R$ {abs(economia):.2f}")
            else:
                st.warning(f"**Custo adicional:** R$ {abs(economia):.2f}")
        
        # ===== DADOS DETALHADOS =====
        st.subheader("📑 Dados Detalhados")
        st.dataframe(df_resultado.style.format("{:.4f}"), width='stretch')
        #if st.checkbox("Mostrar planilha completa"):
        #    st.dataframe(df_resultado.style.format("{:.4f}"), use_container_width=True)


def analise_5_milp_multi(microrredes: list):
    """
    Análise 5 MILP para múltiplas microrredes
    
    Args:
        microrredes: Lista de objetos Microrrede
    """
    st.subheader("Análise 5: Otimização MILP - Múltiplas Microrredes")
    
    # Processar cada microrrede
    resultados_globais = {}
    
    for microrrede in microrredes:
        st.write(f"### 🔧 Processando: {microrrede}")
        
        with st.spinner(f"Otimizando {microrrede}..."):
            df_resultado, custos, solucao = analise_milp_func(microrrede)
        
        if df_resultado is not None:
            resultados_globais[str(microrrede)] = {
                'dataframe': df_resultado,
                'custos': custos,
                'solucao': solucao
            }
            
            st.success(f"✓ {microrrede} otimizada com custo total: R$ {custos.get('Total', 0):,.2f}")
        else:
            st.error(f"✗ Erro ao otimizar {microrrede}")
    
    # Resumo comparativo
    if resultados_globais:
        st.subheader("📊 Resumo Comparativo")
        
        dados_comparacao = []
        for nome_rede, resultado in resultados_globais.items():
            custos = resultado['custos']
            df = resultado['dataframe']
            dados_comparacao.append({
                'Microrrede': nome_rede,
                'Custo Total (R$)': custos.get('Total', 0),
                'Carga Total (kWh)': df['Carga'].sum(),
                'Autossuficiência': ((df['Carga'].sum() - df['Concessionaria'].sum()) / df['Carga'].sum() * 100),
            })
        
        df_comparacao = pd.DataFrame(dados_comparacao)
        st.dataframe(df_comparacao.style.format({
            'Custo Total (R$)': '{:,.2f}',
            'Carga Total (kWh)': '{:,.2f}',
            'Autossuficiência': '{:.1f}%'
        }), use_container_width=True)


def analise_6_pso(microrrede: Microrrede):
    """
    Análise 6 - PSO (Particle Swarm Optimization)
    Otimiza o controle da microrrede usando algoritmo de enxame de partículas
    
    Características:
    - Minimiza custo total operacional
    - Metaheurística baseada em comportamento social
    - Menor tempo computacional que MILP
    - Múltiplas iterações para convergência
    """
    st.subheader("Análise 6: Otimização PSO (Particle Swarm Optimization)")
    st.write("""
    Esta análise utiliza **PSO (Particle Swarm Optimization)** para otimizar 
    o controle da microrrede. Este algoritmo metaheurístico:
    - Simula o comportamento de um enxame de partículas
    - Busca a solução ótima através de exploração e exploração
    - Mais rápido que MILP mantendo boa qualidade de solução
    - Ideal para problemas com estrutura não-linear
    """)
    
    # Parâmetros do PSO com keys únicas baseadas no ID da microrrede
    col1, col2, col3 = st.columns(3)
    with col1:
        iteracoes = st.slider("Iterações PSO", 20, 200, 50, step=10, key=f"pso_iter_{microrrede.id}")
    with col2:
        tamanho_enxame = st.slider("Tamanho do Enxame", 10, 100, 30, step=5, key=f"pso_enxame_{microrrede.id}")
    with col3:
        velocidade = st.slider("Coeficiente de Inércia (w)", 0.1, 1.0, 0.7, step=0.1, key=f"pso_vel_{microrrede.id}")
    
    with st.spinner("Otimizando microrrede com PSO..."):
        try:
            # Executar otimização PSO
            df_resultado, custos, solucao = analise_pso_func(
                microrrede, 
                iteracoes=iteracoes,
                tamanho_enxame=tamanho_enxame
            )
            
            if df_resultado is None:
                st.error("❌ Não foi possível resolver o modelo PSO")
                return
            
            # ===== RESUMO DE CUSTOS =====
            st.subheader("💰 Resumo de Custos")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Solar", f"R$ {custos.get('Solar', 0):,.2f}")
            with col2:
                st.metric("Bateria", f"R$ {custos.get('Bateria', 0):,.2f}")
            with col3:
                st.metric("Diesel", f"R$ {custos.get('Diesel', 0):,.2f}")
            with col4:
                st.metric("Biogas", f"R$ {custos.get('Biogas', 0):,.2f}")
            
            col5, col6 = st.columns(2)
            
            with col5:
                st.metric("Concessionária", f"R$ {custos.get('Concessionaria', 0):,.2f}")
            with col6:
                st.metric("**CUSTO TOTAL PSO**", f"R$ {custos.get('Total', 0):,.2f}", 
                         delta=None, delta_color="inverse")
            
            # ===== CONVERGÊNCIA DO PSO =====
            if 'Convergencia' in solucao and solucao['Convergencia']:
                st.subheader("📉 Convergência do Algoritmo")
                df_convergencia = pd.DataFrame({
                    'Iteração': range(len(solucao['Convergencia'])),
                    'Melhor Custo (R$)': solucao['Convergencia']
                })
                st.line_chart(df_convergencia.set_index('Iteração'), height=300)
                st.caption("Evolução do melhor custo encontrado a cada iteração")
            
            # ===== USO DE ENERGIA POR FONTE =====
            st.subheader("⚡ Despacho de Energia")
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de barras com uso por fonte
                totais_uso = {
                    'Solar': df_resultado['Solar'].sum(),
                    'Bateria': df_resultado['Bateria'].sum(),
                    'Diesel': df_resultado['Diesel'].sum(),
                    'Biogas': df_resultado['Biogas'].sum(),
                    'Concessionária': df_resultado['Concessionaria'].sum(),
                }
                df_totais = pd.DataFrame({
                    'Fonte': list(totais_uso.keys()),
                    'Energia (kWh)': list(totais_uso.values())
                })
                st.bar_chart(df_totais.set_index('Fonte'), width=400, height=300)
            
            with col2:
                # Tabela de resumo
                st.write("**Resumo de Uso por Fonte:**")
                df_resumo = pd.DataFrame({
                    'Fonte': ['Solar', 'Bateria', 'Diesel', 'Biogas', 'Concessionária', 'Venda'],
                    'Energia (kWh)': [
                        f"{df_resultado['Solar'].sum():.2f}",
                        f"{df_resultado['Bateria'].sum():.2f}",
                        f"{df_resultado['Diesel'].sum():.2f}",
                        f"{df_resultado['Biogas'].sum():.2f}",
                        f"{df_resultado['Concessionaria'].sum():.2f}",
                        f"{df_resultado['Venda'].sum():.2f}",
                    ]
                })
                st.dataframe(df_resumo, hide_index=True)
            
            # ===== SÉRIES TEMPORAIS =====
            st.subheader("📈 Evolução Temporal")
            
            tab1, tab2, tab3 = st.tabs(["Despacho em Tempo Real", "Níveis de Armazenamento", "Comparação de Fontes"])
            
            with tab1:
                df_uso = pd.DataFrame({
                    'Solar': df_resultado['Solar'],
                    'Bateria': df_resultado['Bateria'],
                    'Diesel': df_resultado['Diesel'],
                    'Biogas': df_resultado['Biogas'],
                    'Concessionária': df_resultado['Concessionaria'],
                    'Carga': df_resultado['Carga']
                })
                st.line_chart(df_uso, width=None, height=400)
                st.caption("Despacho de energia de cada fonte ao longo do dia")
            
            with tab2:
                df_niveis = pd.DataFrame({
                    'Bateria (kWh)': solucao['Nivel_Bateria'][:-1] if 'Nivel_Bateria' in solucao else [],
                    'Diesel (L)': solucao['Nivel_Diesel'][:-1] if 'Nivel_Diesel' in solucao else [],
                    'Biogas (m³)': solucao['Nivel_Biogas'][:-1] if 'Nivel_Biogas' in solucao else []
                })
                if not df_niveis.empty:
                    st.line_chart(df_niveis, width=None, height=400)
                    st.caption("Evolução dos níveis de armazenamento")
            
            with tab3:
                # Comparação de fontes de energia
                df_comparacao_fontes = pd.DataFrame({
                    'Tempo (min)': range(len(df_resultado)),
                    'Demanda': df_resultado['Carga'],
                    'Geração Local': df_resultado['Solar'] + df_resultado['Bateria'] + df_resultado['Diesel'] + df_resultado['Biogas']
                })
                st.line_chart(df_comparacao_fontes.set_index('Tempo (min)'), height=400)
                st.caption("Comparação entre demanda e capacidade de geração local")
            
            # ===== ESTATÍSTICAS =====
            st.subheader("📋 Estatísticas e Indicadores")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                carga_total = df_resultado['Carga'].sum()
                st.metric("Demanda Total", f"{carga_total:.2f} kWh")
            
            with col2:
                # Taxa de cobertura local (não da rede)
                cobertura_local = ((carga_total - df_resultado['Concessionaria'].sum()) / carga_total * 100) if carga_total > 0 else 0
                st.metric("Cobertura Local", f"{cobertura_local:.1f}%")
            
            with col3:
                # Aproveitamento solar
                total_solar = df_resultado['Solar'].sum() + df_resultado['Venda'].sum()
                aproveitamento = (df_resultado['Solar'].sum() / total_solar * 100) if total_solar > 0 else 0
                st.metric("Aproveit. Solar", f"{aproveitamento:.1f}%")
            
            with col4:
                # Taxa de autossuficiência energética
                energia_propria = carga_total - df_resultado['Concessionaria'].sum()
                autossuficiencia = (energia_propria / carga_total * 100) if carga_total > 0 else 0
                st.metric("Autossuficiência", f"{autossuficiencia:.1f}%")
            
            # ===== DADOS DETALHADOS =====
            st.subheader("📑 Dados Detalhados")
            st.dataframe(df_resultado.style.format("{:.4f}"), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Erro durante otimização PSO: {str(e)}")
            import traceback
            st.error(traceback.format_exc())


def analise_6_pso_multi(microrredes: list):
    """
    Análise 6 PSO para múltiplas microrredes
    
    Args:
        microrredes: Lista de objetos Microrrede
    """
    st.subheader("Análise 6: Otimização PSO - Múltiplas Microrredes")
    
    # Parâmetros globais
    col1, col2 = st.columns(2)
    with col1:
        iteracoes = st.slider("Iterações PSO", 20, 100, 50, step=10, key="pso_multi_iter")
    with col2:
        tamanho_enxame = st.slider("Tamanho do Enxame", 10, 50, 20, step=5, key="pso_multi_enxame")
    
    # Processar cada microrrede
    resultados_globais = {}
    
    for microrrede in microrredes:
        st.write(f"### 🔧 Processando: {microrrede}")
        
        with st.spinner(f"Otimizando {microrrede} com PSO..."):
            try:
                df_resultado, custos, solucao = analise_pso_func(
                    microrrede, 
                    iteracoes=iteracoes,
                    tamanho_enxame=tamanho_enxame
                )
                
                if df_resultado is not None:
                    resultados_globais[str(microrrede)] = {
                        'dataframe': df_resultado,
                        'custos': custos,
                        'solucao': solucao
                    }
                    
                    st.success(f"✓ {microrrede} otimizada com custo: R$ {custos.get('Total', 0):,.2f}")
                else:
                    st.error(f"✗ Erro ao otimizar {microrrede}")
            except Exception as e:
                st.error(f"✗ Erro ao otimizar {microrrede}: {str(e)}")
    
    # Resumo comparativo
    if resultados_globais:
        st.subheader("📊 Resumo Comparativo PSO")
        
        dados_comparacao = []
        for nome_rede, resultado in resultados_globais.items():
            custos = resultado['custos']
            df = resultado['dataframe']
            carga = df['Carga'].sum()
            dados_comparacao.append({
                'Microrrede': nome_rede,
                'Custo Total (R$)': custos.get('Total', 0),
                'Carga Total (kWh)': carga,
                'Custo/kWh': (custos.get('Total', 0) / carga) if carga > 0 else 0,
                'Autossuficiência': ((carga - df['Concessionaria'].sum()) / carga * 100) if carga > 0 else 0,
            })
        
        df_comparacao = pd.DataFrame(dados_comparacao)
        st.dataframe(df_comparacao.style.format({
            'Custo Total (R$)': '{:,.2f}',
            'Carga Total (kWh)': '{:,.2f}',
            'Custo/kWh': '{:.2f}',
            'Autossuficiência': '{:.1f}%'
        }), use_container_width=True)
        
        # Gráfico comparativo
        st.write("**Comparação de Custos**")
        st.bar_chart(df_comparacao.set_index('Microrrede')['Custo Total (R$)'], 
                     color='#1f77b4')


