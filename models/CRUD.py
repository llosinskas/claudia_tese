from database.database_config import Configure

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

def Criar(model):
    try:
        session.add(model)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

def Ler(model_class):
    records = session.query(model_class).all()
    return records

def Ler_Objeto(model_class, model_id):
    record = session.query(model_class).filter(model_class.id == model_id).first()
    return record

def Atualizar(model_class, model_id, updated_data):
    try:
        record = session.query(model_class).filter(model_class.id == model_id).first()
        for key, value in updated_data.items():
            setattr(record, key, value)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

def Deletar(model_class, model_id):
    try:
        session.delete(session.query(model_class).filter(model_class.id == model_id).first())
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


def Criar_Varios(models):
    try:
        session.add_all(models)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
