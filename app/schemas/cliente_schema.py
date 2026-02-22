from pydantic import BaseModel
from typing import Optional


class ClienteCreate(BaseModel):
    nome: str
    cpf_cnpj: str
    cep: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    endereco: Optional[str] = None
    foto_path: Optional[str] = None


class ClienteResponse(BaseModel):
    id: int
    nome: str
    cpf_cnpj: str
    cep: Optional[str]
    bairro: Optional[str]
    cidade: Optional[str]
    uf: Optional[str]
    telefone: Optional[str]
    email: Optional[str]
    endereco: Optional[str]
    foto_path: Optional[str]

    class Config:
        from_attributes = True
