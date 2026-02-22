from app.models.servico_os import ServicoOS
from sqlalchemy.orm import Session

class ServicoOSRepository:

    @staticmethod
    def criar(db: Session, ordem_id, servico_id, quantidade, valor_unitario):

        servico = ServicoOS(
            ordem_servico_id=ordem_id,
            servico_id=servico_id,
            quantidade=quantidade,
            valor_unitario=valor_unitario
        )

        db.add(servico)

        return servico


    @staticmethod
    def listar_por_os(db: Session, os_id):

        return db.query(ServicoOS)\
                 .filter_by(ordem_servico_id=os_id)\
                 .all()

    @staticmethod
    def get_by_id(db: Session, os_servico_id: int):
        return (
            db.query(ServicoOS)
            .filter(ServicoOS.id == os_servico_id)
            .first()
        )
