from sqlalchemy import Column, Integer, String, Float,  create_engine, JSON
from database.database_config import Configure
from sqlalchemy.ext.mutable import MutableList

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

class Solar(Base):
    __tablename__ = "Solar"
    id = Column(Integer, primary_key=True)
    potencia = Column(Float, nullable=False)
    curva = Column(MutableList.as_mutable(JSON), nullable=False, default=[])
    custo_kwh = Column(Float, nullable=False)
    
    def __str__(self):
        return f"Potencia: {self.potencia}"

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