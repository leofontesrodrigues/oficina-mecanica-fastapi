from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.ordem_servico import OrdemServico
from app.repositories.ordem_servico_peca_repo import OrdemServicoPecaRepository
from app.repositories.ordem_servico_repo import OrdemServicoRepository
from app.repositories.pagamento_repo import PagamentoRepository
from app.repositories.peca_repo import PecaRepository
from app.repositories.servico_os_repository import ServicoOSRepository
from app.schemas.ordem_servico_schema import OrdemServicoCreate
from app.services.estoque_service import EstoqueService


class OrdemServicoService:

    STATUS_VALIDOS = {"orcamento", "aberta", "em_andamento", "finalizada", "cancelada", "reprovada"}
    TRANSICOES_VALIDAS = {
        "orcamento": {"aberta", "cancelada", "reprovada"},
        "aberta": {"em_andamento", "cancelada"},
        "em_andamento": {"finalizada", "cancelada"},
        "finalizada": set(),
        "cancelada": set(),
        "reprovada": set(),
    }

    @staticmethod
    def criar_os_menu(
        db,
        cliente_id,
        veiculo_id,
        observacoes,
        mecanico_id=None,
    ):
        os = OrdemServico(
            cliente_id=cliente_id,
            veiculo_id=veiculo_id,
            mecanico_id=mecanico_id,
            observacoes=observacoes,
            status="orcamento",
            data_abertura=datetime.utcnow(),
            valor_total=0,
        )

        return OrdemServicoRepository.create(db, os)

    @staticmethod
    def criar_os(db: Session, os_data: OrdemServicoCreate):
        os = OrdemServico(**os_data.dict())
        return OrdemServicoRepository.create(db, os)

    @staticmethod
    def listar_os(
        db: Session,
        search: str = None,
        page: int = 1,
        per_page: int = 10,
    ):
        return OrdemServicoRepository.get_paginated(db, search, page, per_page)

    @staticmethod
    def excluir_os(db: Session, os_id: int):
        os = OrdemServicoRepository.get_by_id(db, os_id)
        if not os:
            return None
        OrdemServicoRepository.delete(db, os)
        return True

    @staticmethod
    def buscar_por_id(db: Session, os_id: int):
        return OrdemServicoRepository.get_by_id(db, os_id)

    @staticmethod
    def atualizar_status(db: Session, os_id: int, novo_status: str, usuario_id: int = None):
        os = OrdemServicoRepository.get_by_id(db, os_id)

        if not os:
            raise ValueError("Ordem de serviço não encontrada")

        status_atual = (os.status or "").strip().lower()
        status_destino = (novo_status or "").strip().lower()

        if status_destino not in OrdemServicoService.STATUS_VALIDOS:
            raise ValueError("Status inválido")

        if status_destino == status_atual:
            return os

        permitidos = OrdemServicoService.TRANSICOES_VALIDAS.get(status_atual, set())
        if status_destino not in permitidos:
            raise ValueError("Transição de status não permitida")

        if status_destino == "finalizada":
            total_pago = PagamentoRepository.total_pago_por_os(db, os_id)
            saldo = float(os.valor_total) - total_pago
            if saldo > 0:
                raise ValueError("Não é possível finalizar OS com saldo pendente")

        if status_destino == "cancelada":
            os_servicos = ServicoOSRepository.listar_por_os(db, os_id)
            total_servicos = Decimal("0")

            for item in os_servicos:
                total_servicos += Decimal(str(item.valor_unitario)) * Decimal(item.quantidade)
                db.delete(item)

            os_pecas = OrdemServicoPecaRepository.listar_por_os(db, os_id)
            total_pecas = Decimal("0")

            for item in os_pecas:
                peca = PecaRepository.get_by_id(db, item.peca_id)
                if peca:
                    EstoqueService.registrar_entrada(
                        db,
                        peca,
                        quantidade=item.quantidade,
                        origem="os_cancelamento",
                        referencia_id=os.id,
                        observacao=f"Estorno de peça por cancelamento da OS #{os.id}",
                        usuario_id=usuario_id,
                    )

                total_pecas += Decimal(str(item.valor_unitario)) * Decimal(item.quantidade)
                db.delete(item)

            total_itens = total_servicos + total_pecas
            if total_itens > Decimal("0"):
                os.valor_total = max((os.valor_total or Decimal("0")) - total_itens, Decimal("0"))

        os.status = status_destino

        if status_destino in {"finalizada", "cancelada", "reprovada"}:
            os.data_fechamento = datetime.utcnow()

        return OrdemServicoRepository.update(db, os)

    @staticmethod
    def reprovar_orcamento(
        db: Session,
        os_id: int,
        motivo: str,
        usuario_id: int = None,
    ):
        os = OrdemServicoRepository.get_by_id(db, os_id)

        if not os:
            raise ValueError("Ordem de serviço não encontrada")

        if os.status != "orcamento":
            raise ValueError("Apenas orçamento pode ser reprovado")

        motivo_limpo = (motivo or "").strip()
        if len(motivo_limpo) < 5:
            raise ValueError("Informe um motivo com pelo menos 5 caracteres")

        texto_reprovacao = f"[Orçamento reprovado] {motivo_limpo}"
        if (os.observacoes or "").strip():
            os.observacoes = f"{os.observacoes}\n\n{texto_reprovacao}"
        else:
            os.observacoes = texto_reprovacao

        return OrdemServicoService.atualizar_status(
            db,
            os_id,
            "reprovada",
            usuario_id=usuario_id,
        )
