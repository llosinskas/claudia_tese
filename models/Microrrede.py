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

    # reference the mapped class names (capitalized) so SQLAlchemy can resolve them
    biogas = relationship("Biogas", back_populates="microrrede", cascade="all, delete-orphan")
    diesel = relationship("Diesel", back_populates="microrrede", cascade="all, delete-orphan")
    solar = relationship("Solar", back_populates="microrrede", cascade="all, delete-orphan")
    carga = relationship("Carga", back_populates="microrrede", cascade="all, delete-orphan")
    bateria = relationship("BancoBateria", back_populates="microrrede", cascade="all, delete-orphan")
    concessionaria = relationship("Concessionaria", back_populates="microrrede", cascade="all, delete-orphan")
    

    def __str__(self):
        return self.nome

def CriarMircrorrede():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)
