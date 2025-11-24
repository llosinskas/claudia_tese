from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os


def Configure():
    # store the SQLite file next to this config file
    db_file = os.path.join(os.path.dirname(__file__), "dados.db")
    # SQLAlchemy wants three slashes for a relative/absolute file path
    DATABASE_URL = f"sqlite:///{db_file.replace('\\', '/')}"

    engine = create_engine(DATABASE_URL, echo=True)
    SessionLocal = sessionmaker(bind=engine)
    Base = declarative_base()

    # create the database file/tables if they don't exist
    if not os.path.exists(db_file):
        Base.metadata.create_all(bind=engine)

    return DATABASE_URL, engine, SessionLocal, Base


    