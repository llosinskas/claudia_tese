from sqlalchemy import Column, Integer, Float, create_engine
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()
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
    custo_m3 = Column(Float, nullable=False, default=0.0)
    
    def Preco_biogas(self, potencia):
        valor = 0
        if potencia <= potencia*0.5:
            valor = self.consumo_50*self.custo_m3/60
        if potencia > potencia*0.5 and potencia <= potencia*0.75:
            valor = self.consumo_75*self.custo_m3/60
        if potencia > potencia*0.75 :
            valor = self.consumo_100*self.custo_m3/60
        return valor
    
    def Nivel(self):
        return self.nivel
    
    def Consumo(self, potencia):
        nivel = self.nivel
        if potencia <= potencia*0.5:
            nivel = nivel - self.consumo_50/60
        if potencia > potencia*0.5 and potencia <= potencia*0.75:
            nivel = nivel - self.consumo_75/60
        if potencia > potencia*0.75 :
            nivel = nivel - self.consumo_100/60
        self.nivel = nivel
    
    def __repr__(self):
        return f"<Biogas(id={self.id}, potencia={self.potencia}, tanque={self.tanque}, nivel={self.nivel}, geracao={self.geracao})>"    
    def __str__(self):
        return f"Potencia: {self.potencia}"

def Criar(biogas_data):
    session.add(biogas_data)
    session.commit()

def Atualizar(biogas_id, updated_data):
    biogas = session.query(Biogas).filter(Biogas.id == biogas_id).first()
    for key, value in updated_data.items():
        setattr(biogas, key, value)
    session.commit()

def Ler():
    biogases = session.query(Biogas).all()
    return biogases

def Deletar(biogas_id):
    session.delete(session.query(Biogas).filter(Biogas.id == biogas_id).first())
    session.commit()
    
def CriarBiogas():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)