from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

class ServicoOS(Base):

    __tablename__ = "ordem_servico_servicos"

    id = Column(Integer, primary_key=True, index=True)

    ordem_servico_id = Column(
        Integer,
        ForeignKey("ordens_servico.id"),
        nullable=False
    )

    servico_id = Column(
        Integer,
        ForeignKey("servicos.id"),
        nullable=False
    )

    quantidade = Column(Integer, nullable=False, default=1)
    valor_unitario = Column(Float, nullable=False)

    ordem_servico = relationship(
        "OrdemServico",
        back_populates="servicos"
    )
    servico = relationship("Servico")
