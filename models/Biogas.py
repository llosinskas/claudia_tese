from sqlalchemy import Column, Integer, Float, create_engine
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()

class Biogas(Base):
    __tablename__ = "Biogas"

    id = Column(Integer, primary_key=True)
    potencia = Column(Float, nullable=False, default=0.0)
    tanque = Column(Float, nullable=False, default=0.0)
    nivel = Column(Float, nullable=False, default=0.0)
    geracao = Column(Float, nullable=False, default=0.0)
    consumo_50 = Column(Float, nullable=False)
    consumo_75 = Column(Float, nullable=False)
    consumo_100 = Column(Float, nullable=False)

    def __repr__(self):
        return f"<Biogas(id={self.id}, potencia={self.potencia}, tanque={self.tanque}, nivel={self.nivel}, geracao={self.geracao})>"    
    def __str__(self):
        return f"Potencia: {self.potencia}"
def CriarBiogas():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)