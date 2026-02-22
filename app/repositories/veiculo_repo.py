from sqlalchemy.orm import Session
from app.models.veiculo import Veiculo

class VeiculoRepository:

    @staticmethod
    def create(db: Session, veiculo: Veiculo):
        db.add(veiculo)
        db.commit()
        db.refresh(veiculo)
        return veiculo

    @staticmethod
    def get_all(db: Session):
        return db.query(Veiculo).all()

    @staticmethod
    def get_by_id(db: Session, veiculo_id: int):
        return db.query(Veiculo).filter(Veiculo.id == veiculo_id).first()

    @staticmethod
    def get_by_cliente(db: Session, cliente_id: int):
        return db.query(Veiculo).filter(Veiculo.cliente_id == cliente_id).all()

    @staticmethod
    def get_by_placa(db: Session, placa: str):
        return db.query(Veiculo).filter(Veiculo.placa == placa).first()

    @staticmethod
    def update(db: Session, veiculo: Veiculo):
        db.add(veiculo)
        db.commit()
        db.refresh(veiculo)
        return veiculo

    @staticmethod
    def delete(db: Session, veiculo: Veiculo):
        db.delete(veiculo)
        db.commit()
