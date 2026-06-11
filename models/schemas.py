from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional, Union
import json

class CargaFixaSchema(BaseModel):
    id: Optional[int] = None
    nome: str
    tempo_liga: int
    tempo_desliga: int
    potencia: float
    prioridade: int = 1
    carga_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class CargaSchema(BaseModel):
    id: Optional[int] = None
    cargaFixa: List[CargaFixaSchema] = []

    model_config = ConfigDict(from_attributes=True)

class ConcessionariaSchema(BaseModel):
    id: Optional[int] = None
    tarifa: float
    nome: str
    demanda: float
    grupo: str

    model_config = ConfigDict(from_attributes=True)

class DieselSchema(BaseModel):
    id: Optional[int] = None
    potencia: float
    consumo_50: float
    consumo_75: float
    consumo_100: float
    tanque: float
    nivel: float
    custo_por_kWh: float = 0.0

    model_config = ConfigDict(from_attributes=True)

class BiogasSchema(BaseModel):
    id: Optional[int] = None
    potencia: float = 0.0
    tanque: float = 0.0
    nivel: float = 0.0
    geracao: float = 0.0
    consumo_50: float
    consumo_75: float
    consumo_100: float
    custo_por_kWh: float = 0.0

    model_config = ConfigDict(from_attributes=True)

class SolarSchema(BaseModel):
    id: Optional[int] = None
    file_path: Optional[str] = None
    potencia: float
    custo_kwh: float
    curva_geracao: Union[str, List[float], dict]

    @field_validator('curva_geracao', mode='before')
    def parse_curva(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("curva_geracao deve ser um JSON válido se for string")
        return v

    model_config = ConfigDict(from_attributes=True)

class BateriaSchema(BaseModel):
    id: Optional[int] = None
    potencia: float
    capacidade: float
    bateria: str
    nivel: Optional[float] = None
    eficiencia: float
    capacidade_min: float
    capacidade_max: float
    custo_kwh: float

    model_config = ConfigDict(from_attributes=True)

class MicrorredeSchema(BaseModel):
    id: Optional[int] = None
    nome: str
    coordenada_x: Optional[float] = None
    coordenada_y: Optional[float] = None
    
    bateria: Optional[BateriaSchema] = None
    biogas: Optional[BiogasSchema] = None
    concessionaria: Optional[ConcessionariaSchema] = None
    carga: Optional[CargaSchema] = None
    diesel: Optional[DieselSchema] = None
    solar: Optional[SolarSchema] = None

    model_config = ConfigDict(from_attributes=True)

class TradeSchema(BaseModel):
    id: Optional[int] = None
    potencia: float
    preco: float
    microrrede_venda_id: Optional[int] = None
    microrrede_compra_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class BalcaoSchema(BaseModel):
    id: Optional[int] = None
    nome: str
    trade_id: Optional[int] = None
    trade: Optional[TradeSchema] = None

    model_config = ConfigDict(from_attributes=True)
