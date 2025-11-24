from sqlalchemy.orm import Session
from database.database_config import Configure
import json 

DATABASE_URL, engine, SessionLocal, Base = Configure()
def criar(session: Session, model_class, dados:dict):
    
    with engine.connect() as conn:
        res = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='banco_bateria';")
        tabela_existe = res.fetchone() is not None

    if not tabela_existe:
        Base.metadata.create_all(engine)
        
    obj = model_class(**dados)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj

def atualizar(session:Session, model_class, id, novos_dados:dict):
    obj = session.query(model_class).get(id)
    if not obj:
        return None
    for chave, valor in novos_dados.items():
        setattr(obj, chave, valor)
    session.commit()
    session.refresh(obj)
    return obj

def listar(session: Session, model_class, filtros:dict=None):
    query = session.query(model_class)
    if filtros:
        query = query.filter_by(**filtros)
    return query.all()

def delete(session:Session, model_class, id):
    obj = session.query(model_class).get(id)
    if not obj:
        return False
    session.delete(obj)
    session.commit()
    return True