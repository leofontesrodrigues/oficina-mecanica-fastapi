from sqlalchemy.orm import Session

from app.models.servico import Servico
from app.repositories.servico_repo import ServicoRepository
from app.schemas.servico_schema import ServicoCreate


class ServicoService:

    @staticmethod
    def listar(db: Session, search: str = None, page: int = 1, per_page: int = 10):
        return ServicoRepository.get_paginated(db, search, page, per_page)

    @staticmethod
    def listar_todos(db: Session):
        return ServicoRepository.get_all(db)

    @staticmethod
    def criar(db: Session, data: ServicoCreate):
        if data.preco_base <= 0:
            raise ValueError("Preço base deve ser maior que zero")

        existente = ServicoRepository.get_by_descricao(db, data.descricao.strip())
        if existente:
            raise ValueError("Já existe serviço com essa descrição")

        servico = Servico(
            descricao=data.descricao.strip(),
            preco_base=float(data.preco_base),
        )

        return ServicoRepository.create(db, servico)

    @staticmethod
    def editar(db: Session, servico_id: int, data: ServicoCreate):
        servico = ServicoRepository.get_by_id(db, servico_id)
        if not servico:
            raise ValueError("Serviço não encontrado")

        if data.preco_base <= 0:
            raise ValueError("Preço base deve ser maior que zero")

        existente = ServicoRepository.get_by_descricao(db, data.descricao.strip())
        if existente and existente.id != servico_id:
            raise ValueError("Já existe serviço com essa descrição")

        servico.descricao = data.descricao.strip()
        servico.preco_base = float(data.preco_base)

        return ServicoRepository.update(db, servico)

    @staticmethod
    def excluir(db: Session, servico_id: int):
        servico = ServicoRepository.get_by_id(db, servico_id)
        if not servico:
            raise ValueError("Serviço não encontrado")

        ServicoRepository.delete(db, servico)

    @staticmethod
    def buscar_por_id(db: Session, servico_id: int):
        return ServicoRepository.get_by_id(db, servico_id)
