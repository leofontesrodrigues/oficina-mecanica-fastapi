from sqlalchemy.orm import Session
from app.models.mecanico import Mecanico


class MecanicoRepository:

    @staticmethod
    def create(db: Session, mecanico: Mecanico):
        db.add(mecanico)
        db.commit()
        db.refresh(mecanico)
        return mecanico

    @staticmethod
    def get_all(db: Session):
        return db.query(Mecanico).all()
    
    # ✅ ADICIONE ISTO
    @staticmethod
    def update(db: Session, mecanico: Mecanico):
        db.commit()
        db.refresh(mecanico)
        return mecanico

    @staticmethod
    def get_by_id(db: Session, mecanico_id: int):
        return db.query(Mecanico).filter(Mecanico.id == mecanico_id).first()

    @staticmethod
    def delete(db: Session, mecanico: Mecanico):
        db.delete(mecanico)
        db.commit()

    @staticmethod
    def get_ativos(db: Session):
        return db.query(Mecanico).filter(Mecanico.ativo == True).all()

    @staticmethod
    def get_paginated(
        db: Session,
        search: str = None,
        page: int = 1,
        per_page: int = 10
    ):
        query = db.query(Mecanico)

        if search:
            query = query.filter(Mecanico.nome.ilike(f"%{search}%"))

        total = query.count()

        mecanicos = (
            query
            .order_by(Mecanico.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return mecanicos, total
