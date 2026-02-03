from database.database_config import Configure





from models.Microrrede import Microrrede, CriarMircrorrede

DATABASE_URL, engine, SessionLocal, Base = Configure()
session = SessionLocal()

def init_db():
    import models 
    CriarMircrorrede()
    #CriarBateria()
   
    
 
       
    
    Base.metadata.create_all(engine)