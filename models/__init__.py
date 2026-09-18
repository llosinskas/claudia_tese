from database.database_config import engine, SessionLocal, Base

from models.Microrrede import Microrrede, CriarMircrorrede
from models.schemas import (
    CargaFixaSchema,
    CargaSchema,
    ConcessionariaSchema,
    DieselSchema,
    BiogasSchema,
    SolarSchema,
    BateriaSchema,
    MicrorredeSchema,
    TradeSchema,
    BalcaoSchema
)

session = SessionLocal()

def init_db():
    import models 
    CriarMircrorrede()
    Base.metadata.create_all(engine)