from database.database_config import Configure

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

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

def init_db():
    import models 
    CriarMircrorrede()
    #CriarBateria()
    Base.metadata.create_all(engine)