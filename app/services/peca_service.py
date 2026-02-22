from sqlalchemy.orm import Session

from app.models.peca import Peca
from app.repositories.peca_repo import PecaRepository
from app.services.estoque_service import EstoqueService


class PecaService:

    @staticmethod
    def criar(
        db: Session,
        nome: str,
        codigo: str,
        preco: float,
        estoque: int,
        usuario_id: int = None,
    ):
        if estoque < 0:
            raise ValueError("Estoque não pode ser negativo")

        peca = Peca(
            nome=nome,
            codigo=codigo,
            preco=preco,
            estoque=0
        )
        db.add(peca)
        db.flush()

        if estoque > 0:
            EstoqueService.registrar_entrada(
                db,
                peca,
                quantidade=estoque,
                origem="cadastro_peca",
                referencia_id=peca.id,
                observacao="Estoque inicial no cadastro da peça",
                usuario_id=usuario_id,
            )

        db.commit()
        db.refresh(peca)
        return peca

    @staticmethod
    def listar(
        db: Session,
        search: str = None,
        page: int = 1,
        per_page: int = 10
    ):
        return PecaRepository.get_paginated(db, search, page, per_page)

    @staticmethod
    def buscar_por_id(db: Session, peca_id: int):
        return PecaRepository.get_by_id(db, peca_id)

    @staticmethod
    def atualizar_estoque(
        db: Session,
        peca: Peca,
        quantidade: int
    ):

        if peca.estoque < quantidade:
            raise ValueError("Estoque insuficiente")

        peca.estoque -= quantidade

        return PecaRepository.update(db, peca)

    @staticmethod
    def definir_estoque(
        db: Session,
        peca_id: int,
        novo_estoque: int,
        usuario_id: int = None,
        observacao: str = None,
    ):
        peca = PecaRepository.get_by_id(db, peca_id)
        if not peca:
            raise ValueError("Peça não encontrada")

        EstoqueService.registrar_ajuste(
            db,
            peca,
            novo_estoque=novo_estoque,
            observacao=observacao,
            usuario_id=usuario_id,
        )
        return PecaRepository.update(db, peca)
