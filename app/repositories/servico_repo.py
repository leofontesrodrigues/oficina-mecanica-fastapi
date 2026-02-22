from sqlalchemy.orm import Session

from app.models.servico import Servico


class ServicoRepository:

    @staticmethod
    def create(db: Session, servico: Servico):
        db.add(servico)
        db.commit()
        db.refresh(servico)
        return servico

    @staticmethod
    def get_by_id(db: Session, servico_id: int):
        return db.query(Servico).filter(Servico.id == servico_id).first()

    @staticmethod
    def get_by_descricao(db: Session, descricao: str):
        return db.query(Servico).filter(Servico.descricao == descricao).first()

    @staticmethod
    def update(db: Session, servico: Servico):
        db.commit()
        db.refresh(servico)
        return servico

    @staticmethod
    def delete(db: Session, servico: Servico):
        db.delete(servico)
        db.commit()

    @staticmethod
    def get_paginated(
        db: Session,
        search: str = None,
        page: int = 1,
        per_page: int = 10,
    ):
        query = db.query(Servico)

        if search:
            query = query.filter(Servico.descricao.ilike(f"%{search}%"))

        total = query.count()

        servicos = (
            query
            .order_by(Servico.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return servicos, total

    @staticmethod
    def get_all(db: Session):
        return db.query(Servico).order_by(Servico.descricao.asc()).all()
