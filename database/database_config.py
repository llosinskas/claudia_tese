import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

@st.cache_resource
def get_engine():
    return create_engine("sqlite:///meu_banco.db", echo=True)

engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit = False, future=True)
Base = declarative_base()

def Configure():
    DATABASE_URL = f"sqlite:///meu_banco.db"
    engine = create_engine(DATABASE_URL, echo=True)
    SessionLocal = sessionmaker(bind=engine)
    Base = declarative_base()

    # create the database file/tables if they don't exist
    if not os.path.exists("sqlite:///meu_banco.db"):
        Base.metadata.create_all(bind=engine)

    return DATABASE_URL, engine, SessionLocal, Base

def init_db():
    import models 
    Base.metadata.create_all(bind=engine)   