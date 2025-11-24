from sqlalchemy import Column, Integer, String, Float, create_engine
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
class BancoBateria(Base):
    __tablename__ = "Bateria"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    potencia = Column(Float, nullable=False)
    capacidade = Column(Float, nullable=False)
    nivel = Column(Float, nullable=False)
    eficiencia = Column(Float, nullable=False)
    capacidade_min = Column(Float, nullable=False)
    capacidade_max = Column(Float, nullable=False)
    
    
    def Descarrega(self, potencia_consumida):
        nivel = self.nivel
        nivel =nivel - (potencia_consumida*self.eficiencia)/60

    def Nivel(self):
        return self.nivel        
    
    def Carregar(self, potencia):
        nivel = self.nivel
        nivel = nivel + (potencia*self.eficiencia)/60


def CriarBateria():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)