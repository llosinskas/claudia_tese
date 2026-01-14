from sqlalchemy import Column, Integer, String, Float, create_engine, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

class Solar(Base):
    __tablename__ = "solar"
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    file_path = Column(String, nullable=True)
    potencia = Column(Float, nullable=False)
    custo_kwh = Column(Float, nullable=False)
    curva_geracao = Column(JSON, nullable=False)  
    def __str__(self):
        return f"Potencia: {self.potencia} File: {self.file_path}"

def Criar(solar_data):
    session.add(solar_data)
    session.commit()

def Atualizar(solar_id, updated_data):
    solar = session.query(Solar).filter(Solar.id == solar_id).first()
    for key, value in updated_data.items():
        setattr(solar, key, value)
    session.commit()

def Ler():
    solares = session.query(Solar).all()
    return solares

def Deletar(solar_id):
    session.delete(session.query(Solar).filter(Solar.id == solar_id).first())
    session.commit()

def CriarSolar():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)