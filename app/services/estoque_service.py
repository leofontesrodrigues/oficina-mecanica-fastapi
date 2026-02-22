from sqlalchemy.orm import Session

from app.models.estoque_movimentacao import EstoqueMovimentacao
from app.models.peca import Peca
from app.repositories.estoque_movimentacao_repo import EstoqueMovimentacaoRepository


class EstoqueService:

    @staticmethod
    def registrar_saida(
        db: Session,
        peca: Peca,
        quantidade: int,
        origem: str,
        referencia_id: int = None,
        observacao: str = None,
        usuario_id: int = None,
    ):
        if quantidade <= 0:
            raise ValueError("Quantidade inválida para saída de estoque")

        estoque_anterior = int(peca.estoque or 0)
        estoque_posterior = estoque_anterior - quantidade

        if estoque_posterior < 0:
            raise ValueError("Estoque insuficiente")

        peca.estoque = estoque_posterior

        movimentacao = EstoqueMovimentacao(
            peca_id=peca.id,
            usuario_id=usuario_id,
            tipo="saida",
            origem=origem,
            referencia_id=referencia_id,
            quantidade=quantidade,
            estoque_anterior=estoque_anterior,
            estoque_posterior=estoque_posterior,
            observacao=observacao,
        )
        EstoqueMovimentacaoRepository.create(db, movimentacao)
        return movimentacao

    @staticmethod
    def registrar_entrada(
        db: Session,
        peca: Peca,
        quantidade: int,
        origem: str,
        referencia_id: int = None,
        observacao: str = None,
        usuario_id: int = None,
    ):
        if quantidade <= 0:
            raise ValueError("Quantidade inválida para entrada de estoque")

        estoque_anterior = int(peca.estoque or 0)
        estoque_posterior = estoque_anterior + quantidade

        peca.estoque = estoque_posterior

        movimentacao = EstoqueMovimentacao(
            peca_id=peca.id,
            usuario_id=usuario_id,
            tipo="entrada",
            origem=origem,
            referencia_id=referencia_id,
            quantidade=quantidade,
            estoque_anterior=estoque_anterior,
            estoque_posterior=estoque_posterior,
            observacao=observacao,
        )
        EstoqueMovimentacaoRepository.create(db, movimentacao)
        return movimentacao

    @staticmethod
    def registrar_ajuste(
        db: Session,
        peca: Peca,
        novo_estoque: int,
        observacao: str = None,
        usuario_id: int = None,
    ):
        if novo_estoque < 0:
            raise ValueError("Estoque não pode ser negativo")

        estoque_anterior = int(peca.estoque or 0)

        if novo_estoque == estoque_anterior:
            return None

        tipo = "entrada" if novo_estoque > estoque_anterior else "saida"
        quantidade = abs(novo_estoque - estoque_anterior)

        peca.estoque = int(novo_estoque)

        movimentacao = EstoqueMovimentacao(
            peca_id=peca.id,
            usuario_id=usuario_id,
            tipo=tipo,
            origem="ajuste_manual",
            referencia_id=None,
            quantidade=quantidade,
            estoque_anterior=estoque_anterior,
            estoque_posterior=int(novo_estoque),
            observacao=observacao or "Ajuste manual de estoque",
        )
        EstoqueMovimentacaoRepository.create(db, movimentacao)
        return movimentacao

    @staticmethod
    def listar_movimentacoes(
        db: Session,
        search: str = None,
        tipo: str = None,
        page: int = 1,
        per_page: int = 20,
    ):
        return EstoqueMovimentacaoRepository.get_paginated(
            db,
            search=search,
            tipo=tipo,
            page=page,
            per_page=per_page,
        )
