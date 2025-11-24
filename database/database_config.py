from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os


def Configure():
    DATABASE_URL = f"sqlite:///meu_banco.db"
    engine = create_engine(DATABASE_URL, echo=True)
    SessionLocal = sessionmaker(bind=engine)
    Base = declarative_base()

    # create the database file/tables if they don't exist
    if not os.path.exists("sqlite:///meu_banco.db"):
        Base.metadata.create_all(bind=engine)

    return DATABASE_URL, engine, SessionLocal, Base


    