from sqlalchemy import Column, Integer, String, Float, create_engine
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()
class Concessionaria(Base):
    __tablename__ = "concessionaria"

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

def Criar(concessionaria_data):
    session.add(concessionaria_data)
    session.commit()
def Atualizar(concessionaria_id, updated_data):
    concessionaria = session.query(Concessionaria).filter(Concessionaria.id == concessionaria_id).first()
    for key, value in updated_data.items():
        setattr(concessionaria, key, value)
    session.commit()
def Ler():
    concessionarias = session.query(Concessionaria).all()
    return concessionarias
def Deletar(concessionaria_id):
    session.delete(session.query(Concessionaria).filter(Concessionaria.id == concessionaria_id).first())
    session.commit()

def CriarConcessionaria():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)