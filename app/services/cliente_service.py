from sqlalchemy.orm import Session
from app.models.cliente import Cliente
from app.repositories.cliente_repo import ClienteRepository
from app.schemas.cliente_schema import ClienteCreate


class ClienteService:

    @staticmethod
    def criar_cliente(db: Session, cliente_data: ClienteCreate):
        cliente = Cliente(**cliente_data.dict())
        return ClienteRepository.create(db, cliente)

    @staticmethod
    def listar_clientes(db: Session, search: str = None, page: int = 1, per_page: int = 10):
        return ClienteRepository.get_paginated(db, search, page, per_page)

    @staticmethod
    def buscar_por_cpf_cnpj(db: Session, cpf_cnpj: str):
        return ClienteRepository.get_by_cpf_cnpj(db, cpf_cnpj)

    @staticmethod
    def buscar_por_id(db: Session, cliente_id: int):
        return ClienteRepository.get_by_id(db, cliente_id)

    @staticmethod
    def editar_cliente(db: Session, cliente_id: int, cliente_data: ClienteCreate):
        cliente = ClienteRepository.get_by_id(db, cliente_id)
        if not cliente:
            return None

        for campo, valor in cliente_data.dict().items():
            setattr(cliente, campo, valor)

        return ClienteRepository.update(db, cliente)

    @staticmethod
    def excluir_cliente(db: Session, cliente_id: int):
        cliente = ClienteRepository.get_by_id(db, cliente_id)
        if not cliente:
            return None

        ClienteRepository.delete(db, cliente)
        return True
