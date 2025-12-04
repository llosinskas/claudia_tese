from sqlalchemy import Column, Integer, String, Float, create_engine
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

class BancoBateria(Base):
    __tablename__ = "Bateria"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    potencia = Column(Float, nullable=False)
    capacidade = Column(Float, nullable=False)
    bateria = Column(String, nullable=False)
    nivel = Column(Float, nullable=False)
    eficiencia = Column(Float, nullable=False)
    capacidade_min = Column(Float, nullable=False)
    capacidade_max = Column(Float, nullable=False)
    custo_kwh = Column(Float, nullable=False)   
    def __str__(self):
        return f"Bateria: {self.bateria}, Potencia: {self.potencia}kW, Capacidade: {self.capacidade}kWh"
    
    def __repr__(self):
        return f"<Bateria(id={self.id}, potencia={self.potencia}, capacidade={self.capacidade}, nivel={self.nivel})>"
    
    def Descarrega(self, potencia_consumida):
        nivel = self.nivel
        nivel =nivel - (potencia_consumida*self.eficiencia)/60

    def Nivel(self):
        return self.nivel        
    
    def Carregar(self, potencia):
        nivel = self.nivel
        nivel = nivel + (potencia*self.eficiencia)/60

def Criar(bateria):
    session.add(bateria)
    session.commit()

def Atualizar(bateria_id, updated_data):
    bateria = session.query(BancoBateria).filter(BancoBateria.id == bateria_id).first()
    for key, value in updated_data.items():
        setattr(bateria, key, value)
    session.commit()

def Ler():
    bateria = session.query(BancoBateria).all()
    return bateria

def Deletar(bateria_id):
    session.delete(session.query(BancoBateria).filter(BancoBateria.id == bateria_id).first())
    session.commit()

def CriarBateria():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)