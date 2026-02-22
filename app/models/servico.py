from sqlalchemy import Column, Float, Integer, String

from app.database.base import Base


class Servico(Base):
    __tablename__ = "servicos"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(150), nullable=False, unique=True)
    preco_base = Column(Float, nullable=False)
