from database.database_config import SessionLocal, init_db
from sqlalchemy.orm import joinedload

init_db()

session = SessionLocal()

def Criar(model):
    try:
        session.add(model)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

def Ler(model_class):
    try:
        return session.query(model_class).all()
    except Exception as e:
        session.rollback()
        if "no such table" in str(e).lower():
            init_db()
            return session.query(model_class).all()
        raise e

def Ler_Objeto(model_class, model_id):
    try:
        return session.query(model_class).filter(model_class.id == model_id).first()
    except Exception as e:
        session.rollback()
        if "no such table" in str(e).lower():
            init_db()
            return session.query(model_class).filter(model_class.id == model_id).first()
        raise e

def Ler_Completo(model_class, *join_options):
    """Lê todos os registros com eager loading das relações especificadas."""
    try:
        query = session.query(model_class)
        for opt in join_options:
            query = query.options(opt)
        return query.all()
    except Exception as e:
        session.rollback()
        if "no such table" in str(e).lower():
            init_db()
            query = session.query(model_class)
            for opt in join_options:
                query = query.options(opt)
            return query.all()
        raise e

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
        session.expunge_all()
    except Exception as e:
        session.rollback()
        raise e
