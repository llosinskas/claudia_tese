from sqlalchemy import Column, Integer, String, Float, create_engine
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()

class Solar:
    __tablename__ = "Solar"

    id = Column(Integer, primary_key=True)
    potencia = Column(Float, nullable=False)
    curva = Column(String)
   
   
def CriarSolar():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)