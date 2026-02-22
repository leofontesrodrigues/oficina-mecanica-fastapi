from sqlalchemy import Column, Integer, String, Float
from app.database.base import Base

class Peca(Base):
    __tablename__ = "pecas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    codigo = Column(String, unique=True, nullable=False)
    preco = Column(Float, nullable=False)
    estoque = Column(Integer, default=0)
