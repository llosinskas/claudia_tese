from models.CRUD import Ler
from models.Microrrede import Microrrede
mr = Ler(Microrrede)[0]
print("Capacidade:", mr.bateria.capacidade)
print("Potencia:", mr.bateria.potencia)
