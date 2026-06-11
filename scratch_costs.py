from models.CRUD import Ler
from models.Microrrede import Microrrede

mr = Ler(Microrrede)[0]
print("Solar custo:", mr.solar.custo_kwh if mr.solar else "N/A")
print("Bateria custo:", mr.bateria.custo_kwh if mr.bateria else "N/A")
print("Diesel custo:", mr.diesel.custo_por_kWh if mr.diesel else "N/A")
print("Concessionaria tarifa:", mr.concessionaria.tarifa if mr.concessionaria else "N/A")
