from sqlalchemy.orm import Session

from app.models.caixa import Caixa


class CaixaRepository:

    @staticmethod
    def create(db: Session, caixa: Caixa):
        db.add(caixa)
        db.flush()
        return caixa

    @staticmethod
    def update(db: Session, caixa: Caixa):
        db.flush()
        return caixa

    @staticmethod
    def get_caixa_aberto(db: Session):
        return (
            db.query(Caixa)
            .filter(Caixa.status == "aberto")
            .order_by(Caixa.id.desc())
            .first()
        )

    @staticmethod
    def get_last(db: Session):
        return db.query(Caixa).order_by(Caixa.id.desc()).first()

    @staticmethod
    def get_by_id(db: Session, caixa_id: int):
        return db.query(Caixa).filter(Caixa.id == caixa_id).first()

