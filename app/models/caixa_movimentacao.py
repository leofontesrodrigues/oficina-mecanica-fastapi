from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database.base import Base


class CaixaMovimentacao(Base):
    __tablename__ = "caixa_movimentacoes"

    id = Column(Integer, primary_key=True, index=True)
    caixa_id = Column(Integer, ForeignKey("caixas.id"), nullable=False, index=True)
    ordem_servico_id = Column(Integer, ForeignKey("ordens_servico.id"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    tipo = Column(String(20), nullable=False)  # entrada | saida
    categoria = Column(String(30), nullable=False)  # abertura | pagamento_os | suprimento | sangria
    forma_pagamento = Column(String(20), nullable=True)  # dinheiro | pix | cartao
    valor = Column(Numeric(10, 2), nullable=False)
    descricao = Column(Text, nullable=True)
    data_movimentacao = Column(DateTime, nullable=False, default=datetime.utcnow)

    caixa = relationship("Caixa", back_populates="movimentos")
    ordem_servico = relationship("OrdemServico")

