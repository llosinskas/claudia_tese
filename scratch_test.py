import sys
from models.CRUD import Ler
from models.Microrrede import Microrrede
from analises.analise2 import Analise2
from analises.analise3 import Analise3
from analises.config import ConfigAnalise

mr = Ler(Microrrede)[0]
config = ConfigAnalise()

mr_ot = Analise3._copiar_microrrede(mr)
carga = [c for c in mr_ot.carga.cargaFixa if c.prioridade in [2, 3]][0]

print(f"Carga: {carga.nome}, duracao: {carga.tempo_desliga - carga.tempo_liga}")
for inicio in range(0, 1440 - 300 + 1, 120):
    carga.tempo_liga = inicio
    carga.tempo_desliga = inicio + 300
    res = Analise2.executar(mr_ot, config)
    print(f"Inicio: {inicio:04d}, Custo Total: {res[11]:.2f}")
