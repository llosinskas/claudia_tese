from sqlalchemy import Column, Integer, Float, String, create_engine, JSON
from sqlalchemy.ext.mutable import MutableList

from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

class CargaVariavel(Base):
    __tablename__ = "CargaVariavel"
    id = Column(Integer, primary_key=True, autoincrement=True)
    curva = Column(MutableList.as_mutable(JSON), nullable=False, default=[])
    
    def __str__(self):
        return f"Carga ID: {self.id}"
    

class CargaFixa(Base):
    __tablename__ = "CargaFixa"
    id = Column(Integer, primary_key=True, autoincrement=True)
    hora_liga = Column(Integer, nullable=False)
    hora_desliga = Column(Integer, nullable=False)
    valor = Column(Float, nullable=False)
    prioridade = Column(Integer, nullable=False, default=1)
    # 1 - Sempre ligada sem flexibilidade de horário
    # 2 - sempre ligado com flexibilidade de horário
    # 3 - pode ser desligada e há flexibilidade de horário
    # 4 - pode ser desligada sem flexibilidade de horário 
    def __str__(self):
        return f"Carga Fixa ID: {self.id} - Valor: {self.valor} kW"

class Carga(Base):
    __tablename__ = "Carga"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String, nullable=False)  # 'variavel' ou 'fixa'
    carga_variavel_id = Column(Integer, nullable=True)
    carga_fixa_id = Column(Integer, nullable=True)
    
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