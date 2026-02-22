from datetime import datetime

from pydantic import BaseModel


class PagamentoCreate(BaseModel):
    ordem_servico_id: int
    tipo: str
    valor: float


class PagamentoResponse(BaseModel):
    id: int
    ordem_servico_id: int
    tipo: str
    valor: float
    data_pagamento: datetime

    class Config:
        from_attributes = True
