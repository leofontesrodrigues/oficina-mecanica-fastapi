from sqlalchemy.orm import Session

from app.models.estoque_movimentacao import EstoqueMovimentacao
from app.models.peca import Peca


class EstoqueMovimentacaoRepository:

    @staticmethod
    def create(db: Session, movimentacao: EstoqueMovimentacao):
        db.add(movimentacao)
        return movimentacao

    @staticmethod
    def get_paginated(
        db: Session,
        search: str = None,
        tipo: str = None,
        page: int = 1,
        per_page: int = 20,
    ):
        query = db.query(EstoqueMovimentacao).join(Peca, EstoqueMovimentacao.peca_id == Peca.id)

        if search:
            query = query.filter(
                (Peca.nome.ilike(f"%{search}%")) |
                (Peca.codigo.ilike(f"%{search}%"))
            )

        if tipo in {"entrada", "saida"}:
            query = query.filter(EstoqueMovimentacao.tipo == tipo)

        total = query.count()

        movimentacoes = (
            query
            .order_by(EstoqueMovimentacao.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return movimentacoes, total
