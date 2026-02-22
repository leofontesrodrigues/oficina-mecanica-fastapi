from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database.base import Base


class Caixa(Base):
    __tablename__ = "caixas"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(20), nullable=False, default="aberto")
    saldo_inicial = Column(Numeric(10, 2), nullable=False, default=0)
    saldo_atual = Column(Numeric(10, 2), nullable=False, default=0)
    saldo_final = Column(Numeric(10, 2), nullable=True)
    valor_contado_fechamento = Column(Numeric(10, 2), nullable=True)
    diferenca_fechamento = Column(Numeric(10, 2), nullable=True)
    observacao_abertura = Column(Text, nullable=True)
    observacao_fechamento = Column(Text, nullable=True)
    data_abertura = Column(DateTime, nullable=False, default=datetime.utcnow)
    data_fechamento = Column(DateTime, nullable=True)
    usuario_abertura_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    usuario_fechamento_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    movimentos = relationship(
        "CaixaMovimentacao",
        back_populates="caixa",
        cascade="all, delete-orphan",
        order_by="CaixaMovimentacao.data_movimentacao.desc()",
    )
