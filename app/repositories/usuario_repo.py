from sqlalchemy.orm import Session

from app.models.usuario import Usuario


class UsuarioRepository:

    @staticmethod
    def get_by_email(db: Session, email: str):
        return db.query(Usuario).filter(Usuario.email == email).first()

    @staticmethod
    def get_by_id(db: Session, usuario_id: int):
        return db.query(Usuario).filter(Usuario.id == usuario_id).first()

    @staticmethod
    def get_all(db: Session):
        return db.query(Usuario).order_by(Usuario.id.desc()).all()

    @staticmethod
    def create(db: Session, usuario: Usuario):
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario

    @staticmethod
    def update(db: Session, usuario: Usuario):
        db.commit()
        db.refresh(usuario)
        return usuario

    @staticmethod
    def count_all(db: Session) -> int:
        return db.query(Usuario).count()
