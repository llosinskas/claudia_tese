from sqlalchemy import Column, Integer, String, create_engine, Float
from sqlalchemy.orm import relationship
from database.database_config import Configure


DATABASE_URL, engine, SessionLocal, Base = Configure()

class Microrrede(Base):
    __tablename__ = "Microrrede"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String, nullable=False)
    coordenadas_x = Column(Float, nullable=False)
    coordenadas_y = Column(Float, nullable=False)

    biogas = relationship("Biogas", back_populates="Microrrede")
    diesel = relationship("Diesel", back_populates="Microrrede")
    solar = relationship("Solar", back_populates="Microrrede")
    carga = relationship("Carga", back_populates="Microrrede")
    bateria = relationship("BancoBateria", back_populates="Microrrede")
    concessionaria = relationship("Concessionaria", back_populates="Microrrede")
    

    def __str__(self):
        return self.nome

def CriarMircrorrede():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)
