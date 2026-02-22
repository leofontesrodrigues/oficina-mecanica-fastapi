from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.ordem_servico_peca import OrdemServicoPeca

from app.repositories.ordem_servico_peca_repo import OrdemServicoPecaRepository
from app.repositories.ordem_servico_repo import OrdemServicoRepository
from app.repositories.peca_repo import PecaRepository
from app.services.estoque_service import EstoqueService


class OrdemServicoPecaService:

    @staticmethod
    def adicionar_peca(
        db: Session,
        os_id: int,
        peca_id: int,
        quantidade: int,
        usuario_id: int = None,
    ):

        # Buscar OS
        os = OrdemServicoRepository.get_by_id(db, os_id)

        if not os:
            raise ValueError("Ordem de serviço não encontrada")

        if os.status in {"finalizada", "cancelada", "reprovada"}:
            raise ValueError("Não é permitido alterar peças em OS finalizada/cancelada/reprovada")

        if quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero")

        # Buscar Peça
        peca = PecaRepository.get_by_id(db, peca_id)

        if not peca:
            raise ValueError("Peça não encontrada")

        # Validar estoque
        if peca.estoque < quantidade:
            raise ValueError("Estoque insuficiente")

        valor_unitario = peca.preco
        total = Decimal(str(valor_unitario)) * Decimal(quantidade)

        # Criar vínculo OS ↔ Peça
        os_peca = OrdemServicoPeca(
            ordem_servico_id=os_id,
            peca_id=peca_id,
            quantidade=quantidade,
            valor_unitario=valor_unitario
        )

        db.add(os_peca)
        db.flush()

        EstoqueService.registrar_saida(
            db,
            peca,
            quantidade=quantidade,
            origem="os_add_peca",
            referencia_id=os.id,
            observacao=f"Peça adicionada na OS #{os.id}",
            usuario_id=usuario_id,
        )

        # Atualizar total da OS
        os.valor_total = (os.valor_total or Decimal("0")) + total

        db.commit()
        db.refresh(os_peca)

        return os_peca

    @staticmethod
    def listar_por_os(db: Session, os_id: int):

        return OrdemServicoPecaRepository.listar_por_os(db, os_id)

    @staticmethod
    def remover_peca(
        db: Session,
        os_peca_id: int,
        usuario_id: int = None,
    ):

        os_peca = OrdemServicoPecaRepository.get_by_id(db, os_peca_id)

        if not os_peca:
            raise ValueError("Registro não encontrado")

        # Buscar OS e Peça
        os = OrdemServicoRepository.get_by_id(
            db,
            os_peca.ordem_servico_id
        )
        if not os:
            raise ValueError("Ordem de serviço não encontrada")

        if os.status in {"finalizada", "cancelada", "reprovada"}:
            raise ValueError("Não é permitido alterar peças em OS finalizada/cancelada/reprovada")

        peca = PecaRepository.get_by_id(
            db,
            os_peca.peca_id
        )
        if not peca:
            raise ValueError("Peça não encontrada")

        EstoqueService.registrar_entrada(
            db,
            peca,
            quantidade=os_peca.quantidade,
            origem="os_remove_peca",
            referencia_id=os.id,
            observacao=f"Peça removida da OS #{os.id}",
            usuario_id=usuario_id,
        )

        # Atualizar total
        total = Decimal(str(os_peca.valor_unitario)) * Decimal(os_peca.quantidade)
        os.valor_total = max((os.valor_total or Decimal("0")) - total, Decimal("0"))

        db.delete(os_peca)
        db.commit()
        return os.id
