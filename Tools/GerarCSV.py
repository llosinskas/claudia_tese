import csv
import pandas as pd 

def GerarCSV(data, filename):
    data.to_csv(f"{filename}.csv", index=False)
    data.to_excel(f"{filename}.xlsx", index=False)
    print(f"Arquivo {filename}.csv gerado com sucesso!")
