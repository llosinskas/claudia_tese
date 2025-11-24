from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.orm import relationship
from database.database_config import Configure
import json 

DATABASE_URL, engine, SessionLocal, Base = Configure()
class Diesel(Base): 

    __tablename__ = "Diesel"
    id = Column(Integer, primary_key=True, index=True)
    potencia = Column(Float, nullable=False)
    custo = Column(Float, nullable=False)
    consumo_50 = Column(Float, nullable=False)
    consumo_75 = Column(Float, nullable=False)
    consumo_100 = Column(Float, nullable=False)
    tanque = Column(Float, nullable=False)
    nivel = Column(Float, nullable=False)
    

    def Preco_diesel(self, potencia): 
        valor = 0
        if potencia <= potencia*0.5:
            valor = self.consumo_50*self.custo/60
        if potencia > potencia*0.5 and potencia <= potencia*0.75:
            valor = self.consumo_75*self.custo/60
        if potencia > potencia*0.75 :
            valor = self.consumo_100*self.custo/60
        return valor 

    def Custo_50(self):
        custo_min = self.consumo_50 * self.custo / 60
        return custo_min
    
    def Custo_75(self):
        custo_min = self.consumo_75 * self.custo / 60
        return custo_min
    
    def Custo_100(self):
        custo_min = self.consumo_100 * self.custo / 60
        return custo_min
    
    def Nivel(self):
        return self.Nivel
    
    def Consumo(self, potencia):
        nivel = self.nivel
        if potencia <= potencia*0.5:
            nivel = nivel-self.consumo_50/60
        if potencia > potencia*0.5 and potencia <= potencia*0.75:
            nivel = nivel-self.consumo_75
        if potencia > potencia*0.75 :
            nivel = nivel-self.consumo_100
        self.nivel = nivel

def CriarDiesel():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)