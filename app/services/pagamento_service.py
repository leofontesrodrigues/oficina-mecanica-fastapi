from sqlalchemy.orm import Session
from decimal import Decimal, ROUND_HALF_UP

from app.models.pagamento import Pagamento
from app.repositories.ordem_servico_repo import OrdemServicoRepository
from app.repositories.pagamento_repo import PagamentoRepository
from app.services.caixa_service import CaixaService

TIPOS_PERMITIDOS = {"dinheiro", "pix", "cartao"}


class PagamentoService:

    @staticmethod
    def _to_money(value: float) -> Decimal:
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def registrar_pagamento(
        db: Session,
        ordem_servico_id: int,
        tipo: str,
        valor: float,
        usuario_id: int = None,
    ):
        os = OrdemServicoRepository.get_by_id(db, ordem_servico_id)

        if not os:
            raise ValueError("Ordem de serviço não encontrada")

        if os.status == "orcamento":
            raise ValueError("Não é permitido registrar pagamento em orçamento")

        if os.status == "cancelada":
            raise ValueError("Não é permitido registrar pagamento em OS cancelada")

        if os.status == "reprovada":
            raise ValueError("Não é permitido registrar pagamento em orçamento reprovado")

        tipo_normalizado = (tipo or "").strip().lower()
        if tipo_normalizado not in TIPOS_PERMITIDOS:
            raise ValueError("Tipo de pagamento inválido")

        if valor <= 0:
            raise ValueError("Valor do pagamento deve ser maior que zero")

        total_pago = PagamentoRepository.total_pago_por_os(db, ordem_servico_id)
        saldo = PagamentoService._to_money(float(os.valor_total) - total_pago)

        if saldo <= Decimal("0.00"):
            raise ValueError("OS já está quitada")

        valor_recebido = PagamentoService._to_money(valor)
        valor_aplicado = valor_recebido
        troco = Decimal("0.00")

        if valor_recebido > saldo:
            if tipo_normalizado != "dinheiro":
                raise ValueError("Pagamento maior que o saldo pendente")
            troco = (valor_recebido - saldo).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            valor_aplicado = saldo

        pagamento = Pagamento(
            ordem_servico_id=ordem_servico_id,
            tipo=tipo_normalizado,
            valor=float(valor_aplicado),
        )

        db.add(pagamento)
        db.flush()

        CaixaService.registrar_entrada_pagamento_os(
            db=db,
            ordem_servico_id=ordem_servico_id,
            forma_pagamento=tipo_normalizado,
            valor=valor_aplicado,
            usuario_id=usuario_id,
        )

        db.commit()
        db.refresh(pagamento)
        return {
            "pagamento": pagamento,
            "valor_recebido": float(valor_recebido),
            "valor_aplicado": float(valor_aplicado),
            "troco": float(troco),
        }

    @staticmethod
    def listar_pagamentos_por_os(db: Session, ordem_servico_id: int):
        return PagamentoRepository.listar_por_os(db, ordem_servico_id)

    @staticmethod
    def obter_total_pago(db: Session, ordem_servico_id: int) -> float:
        return PagamentoRepository.total_pago_por_os(db, ordem_servico_id)
