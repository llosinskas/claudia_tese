from sqlalchemy import Column, Integer, Float, String, create_engine, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

class Carga(Base):
    __tablename__ = "carga"
    id = Column(Integer, primary_key=True, autoincrement=True)
    valor = Column(JSON, nullable=True)  # Armazena a curva de carga como JSON

class CurvaCarga(Base):
    __tablename__ = "curvaCarga"
    id = Column(Integer, primary_key=True)
    valor = Column(Float, nullable=False)
    minuto = Column(Integer, nullable=False)
    cargaFixa_id = relationship(Integer, ForeignKey('cargaFixa.id'))
    cargaFixa = relationship('CurvaCarga', back_populates='curvaCarga')

class CargaFixa(Base):
    __tablename__ = "cargaFixa"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    tempo_liga = Column(Integer, nullable=False)
    tempo_desliga = Column(Integer, nullable=False)
    potencia = Column(Float, nullable=False)
    prioridade = Column(Integer, nullable=False, default=1)
    # 1 - Sempre ligada sem flexibilidade de horário (ex: Resfriamento, ordenhadeira) -> Gerador diesel + bateria
    # 2 - sempre ligado com flexibilidade de horário (ex: Irrigação )<10hrs ->  bateria
    # 3 - pode ser desligada e há flexibilidade de horário (Ex: iluminação do pátio, bombas de calor) (Backups)
    # 4 - pode ser desligada sem flexibilidade de horário >(Tomadas de uso geral)
    curva = relationship("curvaCarga", back_populates="CargaFixa", cascade="all, delete-orphan")
    carga = relationship("CargaFixa", back_populates="cargaFixa'")

    def __str__(self):
        return f"Carga Fixa ID: {self.id} - Valor: {self.valor} kW"

class Carga(Base):
    __tablename__ = "carga"  # Corrigido para usar a primeira letra maiúscula
    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String, nullable=False)  # 'variavel' ou 'fixa'
    carga_fixa_id = relationship("cargaFixa", back_populates="Carga", cascade="all, delete-orphan")

    def __str__(self):
        return f"Carga Geral ID: {self.id} - Tipo: {self.tipo}"

def LerCargas():
    cargas = session.query(Carga).all()
    return cargas
def CriarCarga(carga):
    session.add(carga)
    session.commit()
def AtualizarCarga(carga_id, updated_data):
    carga = session.query(Carga).filter(Carga.id == carga_id).first()
    for key, value in updated_data.items():
        setattr(carga, key, value)
    session.commit()
def DeletarCarga(carga_id):
    session.delete(session.query(Carga).filter(Carga.id == carga_id).first())
    session.commit()

def LerCargasFixa():
    cargas = session.query(CargaFixa).all()
    return cargas
def CriarCargaFixa(carga):
    session.add(carga)
    session.commit()
def AtualizarCargaFixa(carga_id, updated_data):
    carga = session.query(CargaFixa).filter(CargaFixa.id == carga_id).first()
    for key, value in updated_data.items():
        setattr(carga, key, value)
    session.commit()
def DeletarCargaFixa(carga_id):
    session.delete(session.query(CargaFixa).filter(CargaFixa.id == carga_id).first())
    session.commit()

def LerCargasVariavel():
    cargas = session.query(CargaVariavel).all()
    return cargas

def CriarCargaVariavel(carga):
    session.add(carga)
    session.commit()
def AtualizarCargaVariavel(carga_id, updated_data):
    carga = session.query(CargaVariavel).filter(CargaVariavel.id == carga_id).first()
    for key, value in updated_data.items():
        setattr(carga, key, value)
    session.commit()
def DeletarCargaVariavel(carga_id):
    session.delete(session.query(CargaVariavel).filter(CargaVariavel.id == carga_id).first())
    session.commit()

def CriarCarga():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)