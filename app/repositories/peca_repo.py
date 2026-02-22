from sqlalchemy.orm import Session
from app.models.peca import Peca


class PecaRepository:

    @staticmethod
    def create(db: Session, peca: Peca):
        db.add(peca)
        db.commit()
        db.refresh(peca)
        return peca

    @staticmethod
    def get_all(db: Session):
        return db.query(Peca).all()

    @staticmethod
    def get_by_id(db: Session, peca_id: int):
        return db.query(Peca).filter(Peca.id == peca_id).first()

    @staticmethod
    def get_by_codigo(db: Session, codigo: str):
        return db.query(Peca).filter(Peca.codigo == codigo).first()

    @staticmethod
    def update(db: Session, peca: Peca):
        db.commit()
        db.refresh(peca)
        return peca

    @staticmethod
    def delete(db: Session, peca: Peca):
        db.delete(peca)
        db.commit()

    @staticmethod
    def get_paginated(
        db: Session,
        search: str = None,
        page: int = 1,
        per_page: int = 10
    ):
        query = db.query(Peca)

        if search:
            query = query.filter(
                (Peca.nome.ilike(f"%{search}%")) |
                (Peca.codigo.ilike(f"%{search}%"))
            )

        total = query.count()

        pecas = (
            query
            .order_by(Peca.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return pecas, total
