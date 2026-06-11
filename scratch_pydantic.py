from models.schemas import CargaFixaSchema, CargaSchema, MicrorredeSchema

carga_fixa = CargaFixaSchema(id=1, nome="Teste", tempo_liga=10, tempo_desliga=20, potencia=5.0)
carga = CargaSchema(id=1, cargaFixa=[carga_fixa])
mr = MicrorredeSchema(id=1, nome="MR", carga=carga)

# Pega a carga flexivel
cargas_flexiveis = [c for c in mr.carga.cargaFixa]

# Modifica
for c in cargas_flexiveis:
    c.tempo_liga = 100

print("Original via lista:", cargas_flexiveis[0].tempo_liga)
print("Na MR:", mr.carga.cargaFixa[0].tempo_liga)
