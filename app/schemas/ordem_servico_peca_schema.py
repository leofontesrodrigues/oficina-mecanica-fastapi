from pydantic import BaseModel
from typing import Optional

from app.schemas.peca_schema import PecaResponse


class OrdemServicoPecaCreate(BaseModel):

    ordem_servico_id: int
    peca_id: int
    quantidade: int
    valor_unitario: float


class OrdemServicoPecaResponse(BaseModel):

    id: int
    ordem_servico_id: int
    peca_id: int
    quantidade: int
    valor_unitario: float

    peca: Optional[PecaResponse]

    class Config:
        from_attributes = True
