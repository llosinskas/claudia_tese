import streamlit as st
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# ── Caminho absoluto para o banco ──────────────────────────────
_DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_PATH = os.path.join(_DB_DIR, "meu_banco.db")
DATABASE_URL = f"sqlite:///{_DB_PATH}"

# ── Engine única (cacheada pelo Streamlit) ─────────────────────
@st.cache_resource
def get_engine():
    eng = create_engine(
        DATABASE_URL,
        echo=True,
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    # Ativar WAL para permitir leituras e escritas simultâneas
    @event.listens_for(eng, "connect")
    def _set_sqlite_wal(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
    return eng

engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

def Configure():
    """Retorna a engine e sessão centralizadas (não cria novas)."""
    return DATABASE_URL, engine, SessionLocal, Base

def init_db():
    import models 
    Base.metadata.create_all(bind=engine)