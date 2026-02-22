from sqlalchemy.orm import Session

from app.models.ordem_servico_peca import OrdemServicoPeca


class OrdemServicoPecaRepository:

    @staticmethod
    def create(db: Session, os_peca: OrdemServicoPeca):
        db.add(os_peca)
        db.commit()
        db.refresh(os_peca)
        return os_peca

    @staticmethod
    def listar_por_os(db: Session, os_id: int):
        return (
            db.query(OrdemServicoPeca)
            .filter(OrdemServicoPeca.ordem_servico_id == os_id)
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, os_peca_id: int):
        return (
            db.query(OrdemServicoPeca)
            .filter(OrdemServicoPeca.id == os_peca_id)
            .first()
        )

    @staticmethod
    def delete(db: Session, os_peca: OrdemServicoPeca):
        db.delete(os_peca)
        db.commit()

    @staticmethod
    def existe_uso_da_peca(db: Session, peca_id: int):

        return (
            db.query(OrdemServicoPeca)
            .filter(OrdemServicoPeca.peca_id == peca_id)
            .first()
            is not None
        )
