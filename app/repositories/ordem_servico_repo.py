from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.mecanico import Mecanico
from app.models.ordem_servico import OrdemServico
from app.models.veiculo import Veiculo


class OrdemServicoRepository:

    @staticmethod
    def create(db: Session, os: OrdemServico):
        db.add(os)
        db.commit()
        db.refresh(os)
        return os

    @staticmethod
    def update(db: Session, os: OrdemServico):
        db.commit()
        db.refresh(os)
        return os

    @staticmethod
    def get_all(db: Session):
        return db.query(OrdemServico).all()

    @staticmethod
    def get_by_id(db: Session, os_id: int):
        return db.query(OrdemServico).filter(OrdemServico.id == os_id).first()

    @staticmethod
    def delete(db: Session, os: OrdemServico):
        db.delete(os)
        db.commit()

    @staticmethod
    def get_paginated(
        db: Session,
        search: str = None,
        page: int = 1,
        per_page: int = 10,
    ):
        query = (
            db.query(OrdemServico)
            .join(Cliente, OrdemServico.cliente_id == Cliente.id)
            .join(Veiculo, OrdemServico.veiculo_id == Veiculo.id)
            .outerjoin(Mecanico, OrdemServico.mecanico_id == Mecanico.id)
        )

        if search:
            query = query.filter(
                or_(
                    Cliente.nome.ilike(f"%{search}%"),
                    Veiculo.placa.ilike(f"%{search}%"),
                    Mecanico.nome.ilike(f"%{search}%"),
                    OrdemServico.status.ilike(f"%{search}%"),
                )
            )

        total = query.count()

        ordens = (
            query.order_by(OrdemServico.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return ordens, total
