import sys
from models.CRUD import Ler
from models.Microrrede import Microrrede
from analises.analise3 import Analise3
from analises.config import ConfigAnalise

mr = Ler(Microrrede)[0]
config = ConfigAnalise()
res = Analise3.analise_3(mr, config)
mr_ot = res["microrrede_otimizada"]

for c_or, c_ot in zip(mr.carga.cargaFixa, mr_ot.carga.cargaFixa):
    if c_or.prioridade in [2, 4]:
        print(f"Carga {c_or.nome}: {c_or.tempo_liga}->{c_or.tempo_desliga} mudou para {c_ot.tempo_liga}->{c_ot.tempo_desliga}")
