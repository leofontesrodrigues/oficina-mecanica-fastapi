from pydantic import BaseModel

# Para criar serviço na OS
class ServicoOSCreate(BaseModel):

    ordem_servico_id: int
    servico_id: int
    quantidade: int
    valor_unitario: float


# Para resposta da API
class ServicoOSResponse(BaseModel):

    id: int
    ordem_servico_id: int
    servico_id: int
    quantidade: int
    valor_unitario: float


    class Config:
        from_attributes = True
