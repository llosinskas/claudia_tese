from sqlalchemy import Column, Integer, String, Float, create_engine
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()

class Concessionaria(Base):
    __tablename__ = "Concessionaria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tarifa = Column(Float, nullable=False)
    nome = Column(String, nullable=False)
    demanda = Column(Float, nullable=False)
    grupo = Column(String, nullable=False)
    

    def __str__(self):
        return f"Tarifa: {self.tarifa}"

    def Preco_concessionaria(self, potencia):
        valor = potencia*self.tarifa/60
        return valor
    def Vende(self, potencia):
        valor = potencia*self.tarifa/60
        return valor
    
def CriarConcessionaria():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)