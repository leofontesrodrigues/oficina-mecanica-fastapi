from sqlalchemy import Column, Integer, String, Boolean
from app.database.base import Base


class Mecanico(Base):

    __tablename__ = "mecanicos"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(String(100), nullable=False)
    telefone = Column(String(20))
    especialidade = Column(String(100))
    foto_path = Column(String(255))
    ativo = Column(Boolean, default=True)
