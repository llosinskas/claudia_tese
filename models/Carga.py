from sqlalchemy import Column, Integer, Float, String, create_engine, JSON
from sqlalchemy.ext.mutable import MutableList

from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()

class Carga(Base):
    __tablename__ = "Carga"
    id = Column(Integer, primary_key=True, autoincrement=True)
    curva = Column(MutableList.as_mutable(JSON), nullable=False, default=[])
    
    def __init__(self, curva):
        self.curva = curva

def CriarCarga():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)