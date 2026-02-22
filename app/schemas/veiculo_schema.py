from pydantic import BaseModel
from typing import Optional


class VeiculoCreate(BaseModel):
    cliente_id: int
    placa: str
    marca: str
    modelo: str
    ano: Optional[int] = None
    cor: Optional[str] = None


class VeiculoResponse(BaseModel):
    id: int
    cliente_id: int
    placa: str
    marca: str
    modelo: str
    ano: Optional[int]
    cor: Optional[str]

    class Config:
        from_attributes = True
