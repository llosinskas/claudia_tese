import pandas as pd 
import numpy as np 
from models.Microrrede import Microrrede, Balcao, Trade, Bateria, Diesel, Biogas, Solar, Carga, Concessionaria
from models.CRUD import Ler, Ler_Objeto
from Tools.GerarCurvaCarga import CurvaCarga
from Tools.Diesel.Ferramentas_diesel import Preco_tanque_diesel
from Tools.Biogas.Ferramentas_biogas import Preco_tanque_biogas
import streamlit as st 
import json


def analise5(microrredes:Microrrede):
    pass