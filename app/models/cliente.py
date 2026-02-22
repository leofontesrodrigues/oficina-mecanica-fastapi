from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database.base import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cpf_cnpj = Column(String(18), unique=True, index=True, nullable=False)
    cep = Column(String(10))
    bairro = Column(String(120))
    cidade = Column(String(120))
    uf = Column(String(2))
    telefone = Column(String(20))
    email = Column(String(100))
    endereco = Column(String(255))
    foto_path = Column(String(255))

    created_at = Column(DateTime, default=datetime.utcnow)
