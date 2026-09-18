from database.database_config import SessionLocal
from sqlalchemy.orm import joinedload

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

def Ler_Completo(model_class, *join_options):
    """Lê todos os registros com eager loading das relações especificadas."""
    query = session.query(model_class)
    for opt in join_options:
        query = query.options(opt)
    return query.all()

def Atualizar(model_class, model_id, updated_data):
    try:
        record = session.query(model_class).filter(model_class.id == model_id).first()
        for key, value in updated_data.items():
            setattr(record, key, value)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

def Atualizar_Objeto(obj, **campos):
    """Atualiza campos de um objeto já carregado pela sessão do CRUD."""
    try:
        for key, value in campos.items():
            setattr(obj, key, value)
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

def Deletar_Tudo(model_class):
    try:
        session.query(model_class).delete()
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
