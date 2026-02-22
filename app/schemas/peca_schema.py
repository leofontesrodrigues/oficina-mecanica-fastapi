from pydantic import BaseModel
from typing import Optional


class PecaBase(BaseModel):
    nome: str
    codigo: str
    preco: float
    estoque: int


class PecaCreate(PecaBase):
    pass


class PecaResponse(PecaBase):
    id: int

    class Config:
        from_attributes = True
