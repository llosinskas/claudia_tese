from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

def Criar(model):
    session.add(model)
    session.commit()

def Ler(model_class):
    records = session.query(model_class).all()
    return records

def Ler_Objeto(model_class, model_id):
    record = session.query(model_class).filter(model_class.id == model_id).first()
    return record

def Atualizar(model_class, model_id, updated_data):
    record = session.query(model_class).filter(model_class.id == model_id).first()
    for key, value in updated_data.items():
        setattr(record, key, value)
    session.commit()

def Deletar(model_class, model_id):
    session.delete(session.query(model_class).filter(model_class.id == model_id).first())
    session.commit()

