from sqlalchemy.orm import Session

from app.models.mecanico import Mecanico
from app.repositories.mecanico_repo import MecanicoRepository


class MecanicoService:

    @staticmethod
    def criar(db: Session, nome, telefone, especialidade, ativo=True, foto_path=None):

        mecanico = Mecanico(
            nome=nome,
            telefone=telefone,
            especialidade=especialidade,
            ativo=ativo,
            foto_path=foto_path,
        )

        return MecanicoRepository.create(db, mecanico)

    @staticmethod
    def listar(db: Session, search: str = None, page: int = 1, per_page: int = 10):
        return MecanicoRepository.get_paginated(db, search, page, per_page)

    @staticmethod
    def buscar_por_id(db: Session, mecanico_id: int):
        return MecanicoRepository.get_by_id(db, mecanico_id)

    @staticmethod
    def atualizar(db: Session, mecanico_id, nome, telefone, especialidade, ativo, foto_path=None):

        mecanico = MecanicoRepository.get_by_id(db, mecanico_id)

        if not mecanico:
            return None

        mecanico.nome = nome
        mecanico.telefone = telefone
        mecanico.especialidade = especialidade
        mecanico.ativo = ativo
        if foto_path is not None:
            mecanico.foto_path = foto_path

        return MecanicoRepository.update(db, mecanico)

    @staticmethod
    def excluir(db: Session, mecanico_id: int):

        mecanico = MecanicoRepository.get_by_id(db, mecanico_id)

        if not mecanico:
            return False

        MecanicoRepository.delete(db, mecanico)
        return True
    
    @staticmethod
    def listar_ativos(db: Session):
        return MecanicoRepository.get_ativos(db)
