from sqlalchemy.orm import Session

from app.models.caixa_movimentacao import CaixaMovimentacao


class CaixaMovimentacaoRepository:

    @staticmethod
    def create(db: Session, movimento: CaixaMovimentacao):
        db.add(movimento)
        db.flush()
        return movimento

    @staticmethod
    def listar_por_caixa(db: Session, caixa_id: int):
        return (
            db.query(CaixaMovimentacao)
            .filter(CaixaMovimentacao.caixa_id == caixa_id)
            .order_by(CaixaMovimentacao.data_movimentacao.desc())
            .all()
        )

