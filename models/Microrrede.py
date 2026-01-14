from sqlalchemy import Column, Integer, String, create_engine, Float, ForeignKey
from sqlalchemy.orm import relationship
from database.database_config import Configure
from models.Bateria import Bateria  # Garante que o modelo Bateria seja carregado
from models.Biogas import Biogas      # Garante que o modelo Biogas seja carregado
from models.Diesel import Diesel      # Garante que o modelo Diesel seja carregado
from models.Solar import Solar        # Garante que o modelo Solar seja carregado
from models.Carga import Carga      # Garante que o modelo Carga seja carregado
from models.Concessionaria import Concessionaria  # Garante que o modelo Concessionaria

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

class Microrrede(Base):
    __tablename__ = "microrrede"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)

    # Relacionamento com fontes
    coordenada_x = Column(Float, nullable=True)
    coordenada_y = Column(Float, nullable=True)

    diesel_id = Column(Integer, ForeignKey("diesel.id"), nullable=True)
    biogas_id = Column(Integer, ForeignKey("biogas.id"), nullable=True)
    solar_id = Column(Integer, ForeignKey("solar.id"), nullable=True)
    bateria_id = Column(Integer, ForeignKey("bateria.id"), nullable=True)
    carga_id = Column(Integer, ForeignKey("carga.id"), nullable=True)
    concessionaria_id = Column(Integer, ForeignKey("concessionaria.id"), nullable=True)

    concessionaria = relationship("concessionaria", backref="microrrede")
    carga = relationship("carga", backref="microrrede")
    diesel = relationship("diesel", backref="microrrede")
    biogas = relationship("biogas", backref="microrrede")
    solar = relationship("solar", backref="microrrede")
    bateria = relationship("bateria", backref="microrrede")

    def __repr__(self):
        return f"<Microrrede(id={self.id}, nome={self.nome})>"


# Funções auxiliares para manipular microrredes
def criar_microrrede(nome):
    nova_microrrede = Microrrede(nome=nome)
    session.add(nova_microrrede)
    session.commit()
    return nova_microrrede

def listar_microrredes():
    return session.query(Microrrede).all()

def listar_fontes_microrrede(microrrede_id):
    microrrede = session.query(Microrrede).filter_by(id=microrrede_id).first()
    if not microrrede:
        return None
    return {
        "Diesel": microrrede.diesel,
        "Biogás": microrrede.biogas,
        "Solar": microrrede.solar,
        "Bateria": microrrede.bateria
    }

def CriarMircrorrede():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)
