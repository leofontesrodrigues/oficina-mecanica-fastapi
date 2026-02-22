from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.pagamento import Pagamento


class PagamentoRepository:

    @staticmethod
    def create(db: Session, pagamento: Pagamento):
        db.add(pagamento)
        db.commit()
        db.refresh(pagamento)
        return pagamento

    @staticmethod
    def listar_por_os(db: Session, os_id: int):
        return (
            db.query(Pagamento)
            .filter(Pagamento.ordem_servico_id == os_id)
            .order_by(Pagamento.data_pagamento.desc())
            .all()
        )

    @staticmethod
    def total_pago_por_os(db: Session, os_id: int) -> float:
        total = (
            db.query(func.coalesce(func.sum(Pagamento.valor), 0))
            .filter(Pagamento.ordem_servico_id == os_id)
            .scalar()
        )
        return float(total or 0)
