from pydantic import BaseModel


class ServicoCreate(BaseModel):
    descricao: str
    preco_base: float


class ServicoResponse(BaseModel):
    id: int
    descricao: str
    preco_base: float

    class Config:
        from_attributes = True
