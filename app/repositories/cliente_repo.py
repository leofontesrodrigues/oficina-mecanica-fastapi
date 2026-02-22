from sqlalchemy.orm import Session
from app.models.cliente import Cliente

class ClienteRepository:

    @staticmethod
    def create(db: Session, cliente: Cliente):
        db.add(cliente)
        db.commit()
        db.refresh(cliente)
        return cliente

    @staticmethod
    def get_all(db: Session):
        return db.query(Cliente).all()

    @staticmethod
    def get_by_id(db: Session, cliente_id: int):
        return db.query(Cliente).filter(Cliente.id == cliente_id).first()

    @staticmethod
    def get_by_cpf_cnpj(db: Session, cpf_cnpj: str):
        return db.query(Cliente).filter(Cliente.cpf_cnpj == cpf_cnpj).first()

    @staticmethod
    def update(db: Session, cliente: Cliente):
        db.commit()
        return cliente

    @staticmethod
    def delete(db: Session, cliente: Cliente):
        db.delete(cliente)
        db.commit()
        
    @staticmethod
    def get_paginated(db: Session, search: str = None, page: int = 1, per_page: int = 10):
        query = db.query(Cliente)

        if search:
            search_digits = "".join(ch for ch in search if ch.isdigit())
            query = query.filter(
                (Cliente.nome.ilike(f"%{search}%"))
                | (Cliente.cpf_cnpj.ilike(f"%{search_digits or search}%"))
                | (Cliente.cep.ilike(f"%{search_digits or search}%"))
            )

        total = query.count()

        clientes = (
            query
            .order_by(Cliente.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return clientes, total
