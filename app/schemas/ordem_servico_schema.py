from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.servico_os_schema import ServicoOSResponse
from app.schemas.ordem_servico_peca_schema import OrdemServicoPecaResponse

class OrdemServicoCreate(BaseModel):
    cliente_id: int
    veiculo_id: int
    mecanico_id: int
    observacoes: Optional[str] = None

class OrdemServicoResponse(BaseModel):

    id: int
    cliente_id: int
    veiculo_id: int
    mecanico_id: int
    status: str
    data_abertura: datetime
    data_fechamento: Optional[datetime]
    observacoes: Optional[str]
    valor_total: float

    servicos: List[ServicoOSResponse] = []
    pecas: list[OrdemServicoPecaResponse] = []
    
    class Config:
        from_attributes = True