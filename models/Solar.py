from sqlalchemy import Column, Integer, String, Float, create_engine, ForeignKey

from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

class Solar(Base):
    __tablename__ = "Solar"
    id = Column(Integer, primary_key=True)
    file_path = Column(String, nullable=True)
    potencia = Column(Float, nullable=False)

    custo_kwh = Column(Float, nullable=False)
    
    curva = relationship("CurvaGeracaoSolar", back_populates='Solar', cascade="all, delete-orphan")
    
    def __str__(self):
        return f"Potencia: {self.potencia} File: {self.file_path}"


class SolarCurve(Base):
    __tablename__ = "CurvaGeracaoSolar"
    id = Column(Integer, primary_key=True)
    solar_id = Column(Integer, ForeignKey("Solar.id"))


    valor  = Column(Float, nullable=False)
    solar = relationship("Solar", back_populates="CurvaGeracaoSolar")


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
    #for s in solares:
    #    print(f"Solar: {s.nome}")
    #    for curva in s.curvas:
    #        print(f"Valor curva: {curva.valor}")
    return solares
def Deletar(solar_id):
    session.delete(session.query(Solar).filter(Solar.id == solar_id).first())
    session.commit()

def CriarSolar():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)