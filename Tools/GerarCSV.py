import csv
import pandas as pd 
import sqlite3
def GerarCSV(data, filename):
    data.to_csv(f"{filename}.csv", index=False)
    data.to_excel(f"{filename}.xlsx", index=False)
    print(f"Arquivo {filename}.csv gerado com sucesso!")

def GerarCSVDatabase():
    conn = sqlite3.connect('meu_banco.db')
    df =pd.read_sql_query("SELECT * FROM balcao", conn)
    df.to_csv("/output/balcao.csv")