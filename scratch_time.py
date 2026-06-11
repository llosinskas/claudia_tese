import time
from models.CRUD import Ler
from models.Microrrede import Microrrede
from analises.analise2 import Analise2
from analises.analise3 import Analise3
from analises.config import ConfigAnalise

microrrede = Ler(Microrrede)[0]
config = ConfigAnalise()

start_time = time.time()
for _ in range(150):
    mr_copy = Analise3._copiar_microrrede(microrrede)
    Analise2.executar(mr_copy, config)

end_time = time.time()
print(f"Time for 150 runs: {end_time - start_time:.4f} seconds")
