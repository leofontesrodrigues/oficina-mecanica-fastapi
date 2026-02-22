from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class OrdemServicoPeca(Base):
    __tablename__ = "ordem_servico_pecas"

    id = Column(Integer, primary_key=True, index=True)

    ordem_servico_id = Column(
        Integer,
        ForeignKey("ordens_servico.id"),
        nullable=False
    )

    peca_id = Column(
        Integer,
        ForeignKey("pecas.id"),
        nullable=False
    )

    quantidade = Column(Integer, nullable=False)
    valor_unitario = Column(Float, nullable=False)

    # Relacionamentos
    ordem_servico = relationship("OrdemServico", back_populates="pecas")
    peca = relationship("Peca")
