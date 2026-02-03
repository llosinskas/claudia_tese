from sqlalchemy import Column, Integer, String, Float, create_engine, JSON
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

class Balcao(Base):
    __tablename__ = "balcao"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    # Microrredes cadastradas 
    microrrede_id = Column(Integer, nullable=True)  # ID da microrrede associada
    trade = Column(JSON, nullable=False)  # Potência negociada em kW


    def __str__(self):
        return f"Balcão: {self.nome}"
    

class Trade(Base):
    __tablename__ = "trade"

    id = Column(Integer, primary_key=True, autoincrement=True)
    balcao_id = Column(Integer, nullable=False)  # ID do balcão associado
    microrrede_id = Column(Integer, nullable=False)  # ID da microrrede associada
    potencia = Column(Float, nullable=False)  # Potência negociada em kW
    preco = Column(Float, nullable=False)  # Preço da negociação
    
    def __str__(self):
        return f"Trade ID: {self.id} - Potência: {self.potencia} kW - Preço: {self.preco}"