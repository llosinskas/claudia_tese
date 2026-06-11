import sys
from models.CRUD import Ler
from models.Microrrede import Microrrede
from analises.analise2 import Analise2
from analises.config import ConfigAnalise
from analises.analise3 import Analise3

mr = Ler(Microrrede)[0]
config = ConfigAnalise()

# Manual execution of Analise3 logic to see what it does
microrrede_otimizada = Analise3._copiar_microrrede(mr)
cargas_flexiveis = [c for c in microrrede_otimizada.carga.cargaFixa if c.prioridade in [2, 4]]

for carga in cargas_flexiveis:
    duracao = carga.tempo_desliga - carga.tempo_liga
    melhor_inicio = carga.tempo_liga
    
    resultado_atual = Analise2.executar(microrrede_otimizada, config)
    menor_custo_total = resultado_atual[11]
    
    print(f"Buscando para {carga.nome}. Custo inicial: {menor_custo_total:.2f}")
    
    for inicio in range(0, 1440 - duracao + 1, 30):
        carga.tempo_liga = inicio
        carga.tempo_desliga = inicio + duracao
        
        resultado_teste = Analise2.executar(microrrede_otimizada, config)
        custo_teste = resultado_teste[11]
        
        if custo_teste < menor_custo_total:
            menor_custo_total = custo_teste
            melhor_inicio = inicio
            
    print(f"Melhor inicio achado: {melhor_inicio}. Custo: {menor_custo_total:.2f}")
    
    carga.tempo_liga = melhor_inicio
    carga.tempo_desliga = melhor_inicio + duracao
