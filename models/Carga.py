from sqlalchemy import Column, Integer, Float, String, create_engine
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()

class Carga(Base):
    __tablename__ = "Carga"
    id = Column(Integer, primary_key=True)
    curva = Column(String, nullable=False)
    
    def __init__(self, curva):
        self.curva = curva

def CriarCarga():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)