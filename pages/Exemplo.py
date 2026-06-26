import streamlit as st
import json
from models.Microrrede import Microrrede, Bateria, Biogas, Diesel, Carga, Solar, Concessionaria, CargaFixa
from models.CRUD import Ler, Criar, Criar_Varios, Atualizar, Deletar
from Tools.Solar.gerar_curva_solar_sazonal import gerar_curvas_sazonais

@staticmethod
def exemplo_microrredes():
    dados = {
        "MG - 01": {
                "Verão": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 100.0,
                                "custo": 0.3
                        },
                        "diesel": {
                                "potencia": 5.5,
                                "custo": 2.0
                        },
                        "bateria": {
                                "potencia": 30.0,
                                "capacidade": 80.0,
                                "custo": 0.8
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 22.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Cerca elétrica",
                                        "potencia": 0.01,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 22.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Bomba de água Manhã",
                                        "potencia": 1.0,
                                        "liga": 360,
                                        "desliga": 400,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.5,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.5,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.5,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Meio dia",
                                        "potencia": 1.0,
                                        "liga": 720,
                                        "desliga": 760,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.75,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.75,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.75,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água \"Noite\"",
                                        "potencia": 1.0,
                                        "liga": 1020,
                                        "desliga": 1060,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 3.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.5,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.5,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.5,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Base",
                                        "potencia": 0.3,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.75,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.75,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.75,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.75,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.75,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.75,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                },
                "Outono": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 100.0,
                                "custo": 0.3
                        },
                        "diesel": {
                                "potencia": 5.5,
                                "custo": 2.0
                        },
                        "bateria": {
                                "potencia": 30.0,
                                "capacidade": 80.0,
                                "custo": 0.8
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 4.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Cerca elétrica",
                                        "potencia": 0.01,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 4.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Bomba de água Manhã",
                                        "potencia": 1.0,
                                        "liga": 360,
                                        "desliga": 400,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.275,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.275,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.275,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Meio dia",
                                        "potencia": 1.0,
                                        "liga": 720,
                                        "desliga": 760,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.6375,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.6375,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.6375,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água \"Noite\"",
                                        "potencia": 1.0,
                                        "liga": 1020,
                                        "desliga": 1060,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 3.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.275,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.275,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.275,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Base",
                                        "potencia": 0.3,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.6375,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.6375,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.6375,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.6375,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.6375,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.6375,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                },
                "Inverno": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 100.0,
                                "custo": 0.3
                        },
                        "diesel": {
                                "potencia": 5.5,
                                "custo": 2.0
                        },
                        "bateria": {
                                "potencia": 30.0,
                                "capacidade": 80.0,
                                "custo": 0.8
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 0.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Cerca elétrica",
                                        "potencia": 0.01,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 22.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Bomba de água Manhã",
                                        "potencia": 1.0,
                                        "liga": 360,
                                        "desliga": 400,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.05,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.05,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.05,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Meio dia",
                                        "potencia": 1.0,
                                        "liga": 720,
                                        "desliga": 760,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.525,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.525,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.525,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água \"Noite\"",
                                        "potencia": 1.0,
                                        "liga": 1020,
                                        "desliga": 1060,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 3.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.05,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.05,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.05,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Base",
                                        "potencia": 0.3,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.525,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.525,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.525,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.525,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.525,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.525,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                },
                "Primavera": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 100.0,
                                "custo": 0.3
                        },
                        "diesel": {
                                "potencia": 5.5,
                                "custo": 2.0
                        },
                        "bateria": {
                                "potencia": 30.0,
                                "capacidade": 80.0,
                                "custo": 0.8
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 18.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Cerca elétrica",
                                        "potencia": 0.01,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 18.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Bomba de água Manhã",
                                        "potencia": 1.0,
                                        "liga": 360,
                                        "desliga": 400,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.2,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.2,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.2,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Meio dia",
                                        "potencia": 1.0,
                                        "liga": 720,
                                        "desliga": 760,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.6,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.6,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.6,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água \"Noite\"",
                                        "potencia": 1.0,
                                        "liga": 1020,
                                        "desliga": 1060,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 3.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.2,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.2,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.2,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Base",
                                        "potencia": 0.3,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.6,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.6,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.6,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.6,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.6,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.6,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                }
        },
        "MG - 02": {
                "Verão": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 300.0,
                                "custo": 0.25
                        },
                        "diesel": {
                                "potencia": 16.0,
                                "custo": 1.8
                        },
                        "bateria": {
                                "potencia": 100.0,
                                "capacidade": 80.0,
                                "custo": 0.6
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 12.5,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 66.6,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 88.8,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Cerca elétrica",
                                        "potencia": 0.01,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 4.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 12.5,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 66.6,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 88.8,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Bomba de água Manhã",
                                        "potencia": 1.0,
                                        "liga": 360,
                                        "desliga": 400,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 6.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.6,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 5.0,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Meio dia",
                                        "potencia": 1.0,
                                        "liga": 720,
                                        "desliga": 760,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 8.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.8,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 2.5,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água \"Noite\"",
                                        "potencia": 1.0,
                                        "liga": 1020,
                                        "desliga": 1060,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 3.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 5.0,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 2.5,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "resfriador pós 10",
                                        "potencia": 7.5,
                                        "liga": 37,
                                        "desliga": 155,
                                        "prioridade": 3
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 2.5,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                },
                "Outono": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 300.0,
                                "custo": 0.25
                        },
                        "diesel": {
                                "potencia": 16.0,
                                "custo": 1.8
                        },
                        "bateria": {
                                "potencia": 100.0,
                                "capacidade": 80.0,
                                "custo": 0.6
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 12.5,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 12.1,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 16.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Cerca elétrica",
                                        "potencia": 0.01,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 4.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 12.5,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 12.1,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 16.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Bomba de água Manhã",
                                        "potencia": 1.0,
                                        "liga": 360,
                                        "desliga": 400,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 6.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.6,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 4.25,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Meio dia",
                                        "potencia": 1.0,
                                        "liga": 720,
                                        "desliga": 760,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 8.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.8,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 2.125,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água \"Noite\"",
                                        "potencia": 1.0,
                                        "liga": 1020,
                                        "desliga": 1060,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 3.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 4.25,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 2.125,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "resfriador pós 8,5",
                                        "potencia": 6.375,
                                        "liga": 39,
                                        "desliga": 28,
                                        "prioridade": 3
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 2.125,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                },
                "Inverno": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 300.0,
                                "custo": 0.25
                        },
                        "diesel": {
                                "potencia": 16.0,
                                "custo": 1.8
                        },
                        "bateria": {
                                "potencia": 100.0,
                                "capacidade": 80.0,
                                "custo": 0.6
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 12.5,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 0.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 0.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Cerca elétrica",
                                        "potencia": 0.01,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 4.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 12.5,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 0.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 0.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Bomba de água Manhã",
                                        "potencia": 1.0,
                                        "liga": 360,
                                        "desliga": 400,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 6.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.6,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 3.5,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Meio dia",
                                        "potencia": 1.0,
                                        "liga": 720,
                                        "desliga": 760,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 8.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.8,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 1.75,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água \"Noite\"",
                                        "potencia": 1.0,
                                        "liga": 1020,
                                        "desliga": 1060,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 3.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 3.5,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 1.75,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "resfriador pós 7",
                                        "potencia": 5.25,
                                        "liga": 37,
                                        "desliga": 0,
                                        "prioridade": 3
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 1.75,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                },
                "Primavera": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 300.0,
                                "custo": 0.25
                        },
                        "diesel": {
                                "potencia": 16.0,
                                "custo": 1.8
                        },
                        "bateria": {
                                "potencia": 100.0,
                                "capacidade": 80.0,
                                "custo": 0.6
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 12.5,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 54.5,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 72.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Cerca elétrica",
                                        "potencia": 0.01,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 4.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 12.5,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 54.5,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 72.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Bomba de água Manhã",
                                        "potencia": 1.0,
                                        "liga": 360,
                                        "desliga": 400,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 6.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.6,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 4.0,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Meio dia",
                                        "potencia": 1.0,
                                        "liga": 720,
                                        "desliga": 760,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 8.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.8,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 2.0,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água \"Noite\"",
                                        "potencia": 1.0,
                                        "liga": 1020,
                                        "desliga": 1060,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 3.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 4.0,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 2.0,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "resfriador pós 8",
                                        "potencia": 6.0,
                                        "liga": 35,
                                        "desliga": 126,
                                        "prioridade": 3
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 2.0,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                }
        },
        "MG - 03": {
                "Verão": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 50.0,
                                "custo": 0.25
                        },
                        "diesel": {
                                "potencia": 5.0,
                                "custo": 1.8
                        },
                        "bateria": {
                                "potencia": 15.0,
                                "capacidade": 80.0,
                                "custo": 0.6
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 12.5,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Cerca elétrica",
                                        "potencia": 0.01,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 4.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 12.5,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Manhã",
                                        "potencia": 1.0,
                                        "liga": 360,
                                        "desliga": 400,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 5.0,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.5,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.5,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Meio dia",
                                        "potencia": 1.0,
                                        "liga": 720,
                                        "desliga": 760,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 2.5,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.75,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.75,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água \"Noite\"",
                                        "potencia": 1.0,
                                        "liga": 1020,
                                        "desliga": 1060,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 3.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 5.0,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.5,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.5,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 2.5,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.75,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.75,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 2.5,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.75,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.75,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                },
                "Outono": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 50.0,
                                "custo": 0.25
                        },
                        "diesel": {
                                "potencia": 5.0,
                                "custo": 1.8
                        },
                        "bateria": {
                                "potencia": 15.0,
                                "capacidade": 80.0,
                                "custo": 0.6
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 12.5,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Cerca elétrica",
                                        "potencia": 0.01,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 4.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 12.5,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Manhã",
                                        "potencia": 1.0,
                                        "liga": 360,
                                        "desliga": 400,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 4.25,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.275,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.275,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Meio dia",
                                        "potencia": 1.0,
                                        "liga": 720,
                                        "desliga": 760,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 2.125,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.6375,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.6375,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água \"Noite\"",
                                        "potencia": 1.0,
                                        "liga": 1020,
                                        "desliga": 1060,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 3.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 4.25,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.275,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.275,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 2.125,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.6375,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.6375,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 2.125,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.75,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.75,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                },
                "Inverno": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 50.0,
                                "custo": 0.25
                        },
                        "diesel": {
                                "potencia": 5.0,
                                "custo": 1.8
                        },
                        "bateria": {
                                "potencia": 15.0,
                                "capacidade": 80.0,
                                "custo": 0.6
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 12.5,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Cerca elétrica",
                                        "potencia": 0.01,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 4.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 12.5,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Manhã",
                                        "potencia": 1.0,
                                        "liga": 360,
                                        "desliga": 400,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 3.5,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.05,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.05,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Meio dia",
                                        "potencia": 1.0,
                                        "liga": 720,
                                        "desliga": 760,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 1.75,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.525,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.525,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água \"Noite\"",
                                        "potencia": 1.0,
                                        "liga": 1020,
                                        "desliga": 1060,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 3.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 3.5,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.05,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.05,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 1.75,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.525,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.525,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 1.75,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.525,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.525,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                },
                "Primavera": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 50.0,
                                "custo": 0.25
                        },
                        "diesel": {
                                "potencia": 5.0,
                                "custo": 1.8
                        },
                        "bateria": {
                                "potencia": 15.0,
                                "capacidade": 80.0,
                                "custo": 0.6
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 12.5,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Cerca elétrica",
                                        "potencia": 0.01,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 4.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 12.5,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Manhã",
                                        "potencia": 1.0,
                                        "liga": 360,
                                        "desliga": 400,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 4.0,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.2,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.2,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água Meio dia",
                                        "potencia": 1.0,
                                        "liga": 720,
                                        "desliga": 760,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 2.0,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.6,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.6,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Bomba de água \"Noite\"",
                                        "potencia": 1.0,
                                        "liga": 1020,
                                        "desliga": 1060,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 3.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 4.0,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.2,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.2,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 2.0,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.6,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.6,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 2.0,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.6,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.6,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                }
        },
        "MG - 04": {
                "Verão": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 300.0,
                                "custo": 0.3
                        },
                        "diesel": {
                                "potencia": 20.0,
                                "custo": 2.0
                        },
                        "bateria": {
                                "potencia": 50.0,
                                "capacidade": 80.0,
                                "custo": 0.8
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 12.5,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 88.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 66.6,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 88.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 4.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 12.5,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 88.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 66.6,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 88.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 5.0,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.5,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 8.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.8,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 2.5,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.75,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 6.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.6,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 5.0,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.5,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Pico",
                                        "potencia": 8.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Base",
                                        "potencia": 0.8,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 2.5,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.75,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 2.5,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.75,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                },
                "Outono": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 300.0,
                                "custo": 0.3
                        },
                        "diesel": {
                                "potencia": 20.0,
                                "custo": 2.0
                        },
                        "bateria": {
                                "potencia": 50.0,
                                "capacidade": 80.0,
                                "custo": 0.8
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 12.5,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 16.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 12.1,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 16.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 4.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 12.5,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 16.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 12.1,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 16.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 4.25,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.275,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 8.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.8,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 2.125,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.6375,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 6.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.6,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 4.25,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.275,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Pico",
                                        "potencia": 8.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Base",
                                        "potencia": 0.8,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 2.125,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.6375,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 2.125,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.6375,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                },
                "Inverno": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 300.0,
                                "custo": 0.3
                        },
                        "diesel": {
                                "potencia": 20.0,
                                "custo": 2.0
                        },
                        "bateria": {
                                "potencia": 50.0,
                                "capacidade": 80.0,
                                "custo": 0.8
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 12.5,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 0.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 0.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 0.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 4.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 12.5,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 0.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 0.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 0.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 3.5,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.05,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 8.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.8,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 1.75,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.525,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 6.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.6,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 3.5,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.05,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Pico",
                                        "potencia": 8.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Base",
                                        "potencia": 0.8,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 1.75,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.525,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 1.75,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.525,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                },
                "Primavera": {
                        "tarifa": 0.87,
                        "solar": {
                                "potencia": 300.0,
                                "custo": 0.3
                        },
                        "diesel": {
                                "potencia": 20.0,
                                "custo": 2.0
                        },
                        "bateria": {
                                "potencia": 50.0,
                                "capacidade": 80.0,
                                "custo": 0.8
                        },
                        "cargas": [
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 12.5,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Manhã",
                                        "potencia": 3.75,
                                        "liga": 300,
                                        "desliga": 420,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 72.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 54.5,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação madrugada",
                                        "potencia": 72.0,
                                        "liga": 0,
                                        "desliga": 300,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 1 - Pico",
                                        "potencia": 4.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 1 - Base",
                                        "potencia": 0.5,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 12.5,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Ordenha Tarde",
                                        "potencia": 3.75,
                                        "liga": 960,
                                        "desliga": 1080,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 72.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 54.5,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Irrigação noite",
                                        "potencia": 72.0,
                                        "liga": 1260,
                                        "desliga": 1440,
                                        "prioridade": 2
                                },
                                {
                                        "nome": "Propriedade 2 - Pico",
                                        "potencia": 2.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 2 - Base",
                                        "potencia": 0.4,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 4.0,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Manhã (3h para refrigerar até 4 graus)",
                                        "potencia": 1.2,
                                        "liga": 421,
                                        "desliga": 599,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Pico",
                                        "potencia": 8.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 3 - Base",
                                        "potencia": 0.8,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 1.75,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até ordenha tarde)",
                                        "potencia": 0.6,
                                        "liga": 600,
                                        "desliga": 959,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Pico",
                                        "potencia": 6.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 4 - Base",
                                        "potencia": 0.6,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 4.0,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador Pós Ordenha Tarde (3h para refrigerar até 4 graus)",
                                        "potencia": 1.2,
                                        "liga": 1081,
                                        "desliga": 1260,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Pico",
                                        "potencia": 8.0,
                                        "liga": 1020,
                                        "desliga": 1380,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Propriedade 5 - Base",
                                        "potencia": 0.8,
                                        "liga": 0,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 1.75,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp até meia noite)",
                                        "potencia": 0.6,
                                        "liga": 1261,
                                        "desliga": 1440,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 1.75,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                },
                                {
                                        "nome": "Resfriador (manter temp - meia noite até ordenha manhã)",
                                        "potencia": 0.6,
                                        "liga": 0,
                                        "desliga": 299,
                                        "prioridade": 1
                                }
                        ]
                }
        }
}
    
    coordenadas = {
        "MG - 01": (-31.85, -52.90),
        "MG - 02": (-31.51, -52.49),
        "MG - 03": (-31.26, -53.06),
        "MG - 04": (-31.23, -52.40)
    }

    mgs = []
    for mg_nome, mg_dados in dados.items():
        c_x, c_y = coordenadas.get(mg_nome, (-31.85, -52.90))
        
        p_sol_ref = mg_dados["Verão"]["solar"]["potencia"]
        if p_sol_ref == 0: p_sol_ref = 100
        curvas = gerar_curvas_sazonais(latitude=c_x, longitude=c_y, potencia_kw=p_sol_ref, eficiencia=0.8, estacoes=["Verão", "Outono", "Inverno", "Primavera"])
        
        for estacao, cfg in mg_dados.items():
            bateria = Bateria(
                potencia=cfg["bateria"]["potencia"], 
                capacidade=cfg["bateria"]["capacidade"], 
                bateria="LiFePO4", nivel=100, eficiencia=95, capacidade_min=10, capacidade_max=90, 
                custo_kwh=cfg["bateria"]["custo"]
            )
            solar = Solar(
                potencia=cfg["solar"]["potencia"], 
                custo_kwh=cfg["solar"]["custo"], 
                curva_geracao=json.dumps(curvas[estacao].tolist())
            )
            concessionaria = Concessionaria(
                nome="CEEE - Equatorial", 
                tarifa=cfg["tarifa"], 
                demanda=100, grupo="B"
            )
            diesel = Diesel(
                potencia=cfg["diesel"]["potencia"], 
                custo_por_kWh=cfg["diesel"]["custo"], 
                nivel=100, tanque=500, consumo_50=0.125, consumo_75=0.1875, consumo_100=0.25
            )
            
            cargas_fixas = []
            for c in cfg["cargas"]:
                cargas_fixas.append(
                    CargaFixa(nome=c["nome"][:100], potencia=c["potencia"], tempo_liga=c["liga"], tempo_desliga=c["desliga"], prioridade=c["prioridade"])
                )
            
            mg = Microrrede(
                nome=mg_nome,
                estacao=estacao,
                coordenada_x=c_x,
                coordenada_y=c_y,
                bateria=bateria,
                solar=solar,
                concessionaria=concessionaria,
                diesel=diesel,
                biogas=None,
                carga=Carga(cargaFixa=cargas_fixas)
            )
            mgs.append(mg)
    Criar_Varios(mgs)

def microrrede_artigo():
    estacoes = ["Verão", "Outono", "Inverno", "Primavera"]
    coordenada_x = -31.85
    coordenada_y = -52.9
    potencia_solar = 100
    curvas = gerar_curvas_sazonais(latitude=coordenada_x, longitude=coordenada_y, potencia_kw=potencia_solar, eficiencia=0.8, estacoes=estacoes)
   
    for est in estacoes:
        MG1 = Microrrede(
            nome="MG - 01",
            estacao=est,
            coordenada_x=coordenada_x,
            coordenada_y=coordenada_y,
            bateria=Bateria(potencia=30, capacidade=100, bateria="LiFePO4", nivel=80, eficiencia=95, capacidade_min=20, capacidade_max=80, custo_kwh=0.5),
            solar=Solar(potencia=potencia_solar, custo_kwh=0.3, curva_geracao=json.dumps(curvas[est].tolist())),
            concessionaria=Concessionaria(nome="CEEE equatorial", tarifa=0.87, demanda=100, grupo="B"),
            biogas=Biogas(potencia=0, custo_por_kWh=0.4, nivel=100, tanque=500, geracao=0, consumo_50=0.3, consumo_75=0.45, consumo_100=0.6),
            diesel=Diesel(potencia=5.5, custo_por_kWh=2.0, nivel=100, tanque=40, consumo_50=0.4, consumo_75=0.35, consumo_100=0.3),
            carga=Carga(cargaFixa=[
                CargaFixa(nome="Ordenha manha", potencia=3.75, tempo_liga=300, tempo_desliga=420, prioridade=1), 
                CargaFixa(nome="Ordenha tarde", potencia=3.75, tempo_liga=960, tempo_desliga=1080, prioridade=1),
                CargaFixa(nome="Refriador pós ordenha manhã", potencia=1.5, tempo_liga=420, tempo_desliga=600, prioridade=1),
                CargaFixa(nome="Resfriador", potencia=0.75, tempo_liga=600, tempo_desliga=960, prioridade=1),
                CargaFixa(nome="Cerca elétrica", potencia=0.01, tempo_liga=0, tempo_desliga=1439, prioridade=1)
            ])
        )
        Criar(MG1)


# Configuração da Interface Streamlit
st.set_page_config(page_title="Página de exemplo de sistema de microrredes")
st.title("Exemplos de sistemas de microrredes")

col1, col2 = st.columns([3, 2])

col1.subheader("Microrrede 1 - Cerrito")
col1.write("""
- **Localização:** Coordenadas (X: -31.85, Y: -52.90)
- **Componentes:** Gerados a partir do arquivo MR 1.xlsx
    """)

col1.subheader("Microrrede 2 - Pedro Osório")
col1.write("""
- **Localização:** Coordenadas (X: -31.51, Y: -52.49)
- **Componentes:** Gerados a partir do arquivo MR 2.xlsx
    """)

col1.subheader("Microrrede 3 - Piratini")
col1.write("""
- **Localização:** Coordenadas (X: -31.26, Y: -53.06)
- **Componentes:** Gerados a partir do arquivo MR 3.xlsx
    """)

col1.subheader("Microrrede 4 - Canguçu")
col1.write("""
- **Localização:** Coordenadas (X: -31.23, Y: -52.40)
- **Componentes:** Gerados a partir do arquivo MR 4.xlsx
    """)

if col2.button("Gerar Geração Solar (Teste)"):
    curvas = gerar_curvas_sazonais(latitude=-31.85, longitude=-52.90, potencia_kw=100, eficiencia=0.8, estacoes=["Verão"])
    print("Geração solar de exemplo gerada para a microrrede 1 (Verão)")
    col2.line_chart(curvas["Verão"])
    
if col2.button("Gerar Exemplo"):
    with st.spinner("Gerando exemplos carregados das planilhas para Verão, Outono, Inverno e Primavera..."):
        exemplo_microrredes()
    st.success("Exemplos criados com sucesso! Verifique a aba Microrredes ou Mercado 2.")
