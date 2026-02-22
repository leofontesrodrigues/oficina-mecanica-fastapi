from pydantic import BaseModel
from typing import Optional


class MecanicoCreate(BaseModel):
    nome: str
    telefone: Optional[str] = None
    especialidade: Optional[str] = None
    ativo: Optional[bool] = True
    foto_path: Optional[str] = None


class MecanicoResponse(BaseModel):
    id: int
    nome: str
    telefone: Optional[str]
    especialidade: Optional[str]
    foto_path: Optional[str]
    ativo: bool

    class Config:
        from_attributes = True
