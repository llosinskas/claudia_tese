from sqlalchemy import Column, Integer, String, create_engine, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database.database_config import Configure, Base

DATABASE_URL, engine, SessionLocal, Base1 = Configure()
session = SessionLocal()

class CargaFixa(Base):
    __tablename__ = "cargaFixa"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    tempo_liga = Column(Integer, nullable=False)
    tempo_desliga = Column(Integer, nullable=False)
    potencia = Column(Float, nullable=False)
    # 1 - Sempre ligada sem flexibilidade de horário (ex: Resfriamento, ordenhadeira) -> Gerador diesel + bateria
    # 2 - sempre ligado com flexibilidade de horário (ex: Irrigação ) < 10hrs ->  bateria
    # 3 - pode ser desligada e há flexibilidade de horário (Ex: iluminação do pátio, bombas de calor) (Backups)
    # 4 - pode ser desligada sem flexibilidade de horário > (Tomadas de uso geral)    
    prioridade = Column(Integer, nullable=False, default=1)
    
    #valor = Column(JSON, nullable=True)  # Valor total da carga fixa em kW
    #carga_id = Column(Integer, ForeignKey("carga.id"), nullable=True)
    #carga = relationship("Carga", backref="cargaFixa", foreign_keys=[carga_id])
    
    def __str__(self):
        return f"Carga Fixa ID: {self.id} - Potência: {self.potencia} kW"

class Carga(Base):
    __tablename__ = "carga"
    id = Column(Integer, primary_key=True, autoincrement=True)
    #microrrede_id = Column(Integer, ForeignKey("microrrede.id"), nullable=True)
    #microrrede = relationship("Microrrede", back_populates="carga")  # Usando string para evitar erro de importação circular
    demanda = Column(JSON, nullable=True)  # Demanda total da carga em kW ao longo do tempo
    microrrede = relationship("Microrrede", back_populates="carga")
    def __str__(self):
        return f"Carga ID: {self.id} - Demanda: {self.demanda} kW"

class Concessionaria(Base):
    __tablename__ = "concessionaria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tarifa = Column(Float, nullable=False)
    nome = Column(String, nullable=False)
    demanda = Column(Float, nullable=False)
    grupo = Column(String, nullable=False)   
    microrrede = relationship("Microrrede", back_populates="concessionaria")
    def __str__(self):
        return f"Tarifa: {self.tarifa}"

    def Preco_concessionaria(self, potencia):
        valor = potencia*self.tarifa/60
        return valor
    def Vende(self, potencia):
        valor = potencia*self.tarifa/60
        return valor

class Diesel(Base): 
    __tablename__ = "diesel"
    id = Column(Integer, primary_key=True, index=True)
    potencia = Column(Float, nullable=False)
    custo = Column(Float, nullable=False)
    consumo_50 = Column(Float, nullable=False)
    consumo_75 = Column(Float, nullable=False)
    consumo_100 = Column(Float, nullable=False)
    tanque = Column(Float, nullable=False)
    nivel = Column(Float, nullable=False)
    custo_por_kWh = Column(Float, nullable=False, default=0.0)
    microrrede = relationship("Microrrede", back_populates="diesel")

    def __str__(self):
        return f"Potencia: {self.potencia}kW, capacidade do tanque: {self.tanque}l"

    def Preco_diesel(self, potencia): 
        valor = 0
        if potencia <= potencia*0.5:
            valor = self.consumo_50*self.custo/60
        if potencia > potencia*0.5 and potencia <= potencia*0.75:
            valor = self.consumo_75*self.custo/60
        if potencia > potencia*0.75 :
            valor = self.consumo_100*self.custo/60
        return valor 

    def Custo_50(self):
        custo_min = self.consumo_50 * self.custo / 60
        return custo_min
    
    def Custo_75(self):
        custo_min = self.consumo_75 * self.custo / 60
        return custo_min
    
    def Custo_100(self):
        custo_min = self.consumo_100 * self.custo / 60
        return custo_min
    
    def Nivel(self):
        return self.Nivel
    
    def Consumo(self, potencia):
        nivel = self.nivel
        if potencia <= potencia*0.5:
            nivel = nivel-self.consumo_50/60
        if potencia > potencia*0.5 and potencia <= potencia*0.75:
            nivel = nivel-self.consumo_75
        if potencia > potencia*0.75 :
            nivel = nivel-self.consumo_100
        self.nivel = nivel

class Solar(Base):
    __tablename__ = "solar"
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    file_path = Column(String, nullable=True)
    potencia = Column(Float, nullable=False)
    custo_kwh = Column(Float, nullable=False)
    curva_geracao = Column(JSON, nullable=False)
    microrrede = relationship("Microrrede", back_populates="solar")

    def __str__(self):
        return f"Potencia: {self.potencia} File: {self.file_path}"

class Biogas(Base):
    __tablename__ = "biogas"

    id = Column(Integer, primary_key=True)
    potencia = Column(Float, nullable=False, default=0.0)
    tanque = Column(Float, nullable=False, default=0.0)
    nivel = Column(Float, nullable=False, default=0.0)
    geracao = Column(Float, nullable=False, default=0.0)
    consumo_50 = Column(Float, nullable=False)
    consumo_75 = Column(Float, nullable=False)
    consumo_100 = Column(Float, nullable=False)
    custo_por_kWh = Column(Float, nullable=False, default=0.0)
    microrrede = relationship("Microrrede", back_populates="biogas")

    def Preco_biogas(self, potencia):
        valor = 0
        if potencia <= potencia*0.5:
            valor = self.consumo_50*self.custo_por_kWh/60
        if potencia > potencia*0.5 and potencia <= potencia*0.75:
            valor = self.consumo_75*self.custo_por_kWh/60
        if potencia > potencia*0.75 :
            valor = self.consumo_100*self.custo_por_kWh/60
        return valor
    
    def Nivel(self):
        return self.nivel
    
    def Consumo(self, potencia):
        nivel = self.nivel
        if potencia <= potencia*0.5:
            nivel = nivel - self.consumo_50/60
        if potencia > potencia*0.5 and potencia <= potencia*0.75:
            nivel = nivel - self.consumo_75/60
        if potencia > potencia*0.75 :
            nivel = nivel - self.consumo_100/60
        self.nivel = nivel
    
    def __repr__(self):
        return f"<Biogas(id={self.id}, potencia={self.potencia}, tanque={self.tanque}, nivel={self.nivel}, geracao={self.geracao})>"    
    def __str__(self):
        return f"Potencia: {self.potencia}"

class Bateria(Base):
    __tablename__ = "bateria"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    potencia = Column(Float, nullable=False)
    capacidade = Column(Float, nullable=False)
    bateria = Column(String, nullable=False)
    nivel = Column(Float, nullable=False)
    eficiencia = Column(Float, nullable=False)
    capacidade_min = Column(Float, nullable=False)
    capacidade_max = Column(Float, nullable=False)
    custo_kwh = Column(Float, nullable=False)   
    microrrede = relationship("Microrrede", back_populates="bateria")

    def __str__(self):
        return f"Bateria: {self.bateria}, Potencia: {self.potencia}kW, Capacidade: {self.capacidade}kWh"
    
    def __repr__(self):
        return f"<Bateria(id={self.id}, potencia={self.potencia}, capacidade={self.capacidade}, nivel={self.nivel})>"
    
    def Descarrega(self, potencia_consumida):
        nivel = self.nivel
        nivel =nivel - (potencia_consumida*self.eficiencia)/60

    def Nivel(self):
        return self.nivel        
    
    def Carregar(self, potencia):
        nivel = self.nivel
        nivel = nivel + (potencia*self.eficiencia)/60

class Microrrede(Base):
    __tablename__ = "microrrede"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)

    # Relacionamento com fontes
    coordenada_x = Column(Float, nullable=True)
    coordenada_y = Column(Float, nullable=True)
    bateria_id = Column(Integer, ForeignKey("bateria.id"), nullable=True)
    biogas_id = Column(Integer, ForeignKey("biogas.id"), nullable=True)
    bateria = relationship("Bateria", back_populates="microrrede", lazy="joined")
    biogas = relationship("Biogas", back_populates="microrrede", lazy="joined")

    concessionaria = relationship("concessionaria", back_populates="microrrede", lazy="joined")
    carga = relationship("Carga", back_populates="microrrede", lazy="joined")
    diesel = relationship("Diesel", back_populates="microrrede", lazy="joined")
    solar = relationship("Solar", back_populates="microrrede", lazy="joined")
    
    #balanco_energia = Column(JSON, nullable=True)  # Balanço   de energia da microrrede ao longo do tempo
    #tempo = Column(JSON, nullable=True)  # Tempo correspondente ao balanço de energia

    def __str__(self):  
        return f"Microrrede: {self.nome}"
    
    def __repr__(self):
        return f"<Microrrede(id={self.id}, nome={self.nome})>"

# Funções auxiliares para manipular microrredes
def criar_microrrede(nome):
    nova_microrrede = Microrrede(nome=nome)
    session.add(nova_microrrede)
    session.commit()
    return nova_microrrede

def listar_microrredes():
    return session.query(Microrrede).all()

def listar_fontes_microrrede(microrrede_id):
    microrrede = session.query(Microrrede).filter_by(id=microrrede_id).first()
    if not microrrede:
        return None
    return {
        "Diesel": microrrede.diesel,
        "Biogás": microrrede.biogas,
        "Solar": microrrede.solar,
        "Bateria": microrrede.bateria, 
        "Concessionária": microrrede.concessionaria,
    }

def CriarMircrorrede():    
    engine = create_engine("sqlite:///meu_banco.db")
    Base.metadata.create_all(engine)
