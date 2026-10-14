import streamlit as st
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# ── Caminho absoluto e normalizado para o banco ───────────────
_DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_PATH = os.path.join(_DB_DIR, "meu_banco.db").replace("\\", "/")
DATABASE_URL = f"sqlite:///{_DB_PATH}"

# ── Engine única (cacheada pelo Streamlit) ─────────────────────
@st.cache_resource
def get_engine():
    eng = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    # Ativar WAL para permitir leituras e escritas simultâneas sem locks
    @event.listens_for(eng, "connect")
    def _set_sqlite_wal(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
    return eng

engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

def init_db():
    """Garante que todas as tabelas estejam criadas no banco de dados."""
    try:
        import models.Microrrede  # Registra os modelos no Base.metadata
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Aviso ao inicializar banco: {e}")

def Configure():
    """Retorna a engine e sessão centralizadas, garantindo criação do schema."""
    init_db()
    return DATABASE_URL, engine, SessionLocal, Base

init_db()