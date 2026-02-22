from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.base import Base

class OrdemServico(Base):
    __tablename__ = "ordens_servico"

    id = Column(Integer, primary_key=True, index=True)

    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"), nullable=False)
    mecanico_id = Column(Integer, ForeignKey("mecanicos.id"), nullable=True)

    status = Column(String(20), default="aberta")
    data_abertura = Column(DateTime, default=datetime.utcnow)
    data_fechamento = Column(DateTime, nullable=True)

    observacoes = Column(String(500))
    valor_total = Column(Numeric(10, 2), default=0)

    cliente = relationship("Cliente")
    veiculo = relationship("Veiculo")
    mecanico = relationship("Mecanico", backref="ordens_servico")
    servicos = relationship("ServicoOS", back_populates="ordem_servico", cascade="all, delete-orphan")
    pecas = relationship("OrdemServicoPeca", back_populates="ordem_servico", cascade="all, delete-orphan")
    pagamentos = relationship("Pagamento", back_populates="ordem_servico", cascade="all, delete-orphan")


