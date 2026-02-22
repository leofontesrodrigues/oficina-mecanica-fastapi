from sqlalchemy.orm import Session
from decimal import Decimal

from app.repositories.ordem_servico_repo import OrdemServicoRepository
from app.repositories.servico_os_repository import ServicoOSRepository
from app.repositories.servico_repo import ServicoRepository
from app.schemas.servico_os_schema import ServicoOSCreate


class ServicoOSService:

    @staticmethod
    def criar(db: Session, data: ServicoOSCreate):
        if data.quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        if data.valor_unitario <= 0:
            raise ValueError("Valor unitário deve ser maior que zero")

        os = OrdemServicoRepository.get_by_id(db, data.ordem_servico_id)
        if not os:
            raise ValueError("Ordem de serviço não encontrada")

        if os.status in {"finalizada", "cancelada", "reprovada"}:
            raise ValueError("Não é permitido alterar serviços em OS finalizada/cancelada/reprovada")

        servico_catalogo = ServicoRepository.get_by_id(db, data.servico_id)
        if not servico_catalogo:
            raise ValueError("Serviço não encontrado no catálogo")

        servico = ServicoOSRepository.criar(
            db,
            data.ordem_servico_id,
            data.servico_id,
            data.quantidade,
            data.valor_unitario
        )

        total = Decimal(str(data.valor_unitario)) * Decimal(data.quantidade)
        os.valor_total = (os.valor_total or Decimal("0")) + total

        db.commit()
        db.refresh(servico)

        return servico

    @staticmethod
    def listar(db: Session, os_id):

        return ServicoOSRepository.listar_por_os(db, os_id)

    @staticmethod
    def remover(db: Session, os_servico_id: int):
        os_servico = ServicoOSRepository.get_by_id(db, os_servico_id)
        if not os_servico:
            raise ValueError("Serviço da OS não encontrado")

        os = OrdemServicoRepository.get_by_id(db, os_servico.ordem_servico_id)
        if not os:
            raise ValueError("Ordem de serviço não encontrada")

        if os.status in {"finalizada", "cancelada", "reprovada"}:
            raise ValueError("Não é permitido alterar serviços em OS finalizada/cancelada/reprovada")

        total = Decimal(str(os_servico.valor_unitario)) * Decimal(os_servico.quantidade)
        os.valor_total = max((os.valor_total or Decimal("0")) - total, Decimal("0"))

        db.delete(os_servico)
        db.commit()

        return os.id
