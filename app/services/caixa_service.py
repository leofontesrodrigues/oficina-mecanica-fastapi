from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.models.caixa import Caixa
from app.models.caixa_movimentacao import CaixaMovimentacao
from app.repositories.caixa_movimentacao_repo import CaixaMovimentacaoRepository
from app.repositories.caixa_repo import CaixaRepository


class CaixaService:

    @staticmethod
    def _to_money(value) -> Decimal:
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def obter_caixa_aberto(db: Session):
        return CaixaRepository.get_caixa_aberto(db)

    @staticmethod
    def obter_ultimo_caixa(db: Session):
        return CaixaRepository.get_last(db)

    @staticmethod
    def listar_movimentacoes(db: Session, caixa_id: int):
        return CaixaMovimentacaoRepository.listar_por_caixa(db, caixa_id)

    @staticmethod
    def listar_movimentacoes_periodo(
        db: Session,
        dt_inicio: datetime = None,
        dt_fim: datetime = None,
    ):
        query = db.query(CaixaMovimentacao)
        if dt_inicio:
            query = query.filter(CaixaMovimentacao.data_movimentacao >= dt_inicio)
        if dt_fim:
            query = query.filter(CaixaMovimentacao.data_movimentacao <= dt_fim)
        return query.order_by(CaixaMovimentacao.data_movimentacao.desc()).all()

    @staticmethod
    def abrir_caixa(
        db: Session,
        saldo_inicial: float,
        usuario_id: int = None,
        observacao: str = None,
    ):
        if CaixaRepository.get_caixa_aberto(db):
            raise ValueError("Já existe um caixa aberto")

        saldo = CaixaService._to_money(saldo_inicial)
        if saldo < Decimal("0.00"):
            raise ValueError("Saldo inicial não pode ser negativo")

        caixa = Caixa(
            status="aberto",
            saldo_inicial=saldo,
            saldo_atual=saldo,
            observacao_abertura=(observacao or "").strip() or None,
            usuario_abertura_id=usuario_id,
            data_abertura=datetime.utcnow(),
        )
        CaixaRepository.create(db, caixa)

        movimento_abertura = CaixaMovimentacao(
            caixa_id=caixa.id,
            usuario_id=usuario_id,
            tipo="entrada",
            categoria="abertura",
            valor=saldo,
            descricao="Abertura de caixa",
        )
        CaixaMovimentacaoRepository.create(db, movimento_abertura)
        db.commit()
        db.refresh(caixa)
        return caixa

    @staticmethod
    def fechar_caixa(
        db: Session,
        usuario_id: int = None,
        valor_contado: float = None,
        observacao: str = None,
    ):
        caixa = CaixaRepository.get_caixa_aberto(db)
        if not caixa:
            raise ValueError("Não há caixa aberto para fechamento")

        saldo_sistema = CaixaService._to_money(caixa.saldo_atual or 0)
        valor_contado_dec = saldo_sistema
        diferenca = Decimal("0.00")

        if valor_contado is not None:
            valor_contado_dec = CaixaService._to_money(valor_contado)
            if valor_contado_dec < Decimal("0.00"):
                raise ValueError("Valor contado não pode ser negativo")
            diferenca = valor_contado_dec - saldo_sistema

        caixa.status = "fechado"
        caixa.saldo_final = caixa.saldo_atual
        caixa.valor_contado_fechamento = valor_contado_dec
        caixa.diferenca_fechamento = diferenca
        caixa.data_fechamento = datetime.utcnow()
        caixa.usuario_fechamento_id = usuario_id
        caixa.observacao_fechamento = (observacao or "").strip() or None
        CaixaRepository.update(db, caixa)
        db.commit()
        db.refresh(caixa)
        return caixa

    @staticmethod
    def registrar_movimento_manual(
        db: Session,
        tipo: str,
        valor: float,
        descricao: str,
        usuario_id: int = None,
        categoria: str = "ajuste",
    ):
        caixa = CaixaRepository.get_caixa_aberto(db)
        if not caixa:
            raise ValueError("Abra o caixa antes de registrar movimentações")

        tipo_norm = (tipo or "").strip().lower()
        if tipo_norm not in {"entrada", "saida"}:
            raise ValueError("Tipo inválido de movimentação")

        valor_dec = CaixaService._to_money(valor)
        if valor_dec <= Decimal("0.00"):
            raise ValueError("Valor deve ser maior que zero")

        if tipo_norm == "saida" and Decimal(str(caixa.saldo_atual or 0)) < valor_dec:
            raise ValueError("Saldo insuficiente no caixa")

        if tipo_norm == "entrada":
            caixa.saldo_atual = CaixaService._to_money(caixa.saldo_atual) + valor_dec
        else:
            caixa.saldo_atual = CaixaService._to_money(caixa.saldo_atual) - valor_dec

        movimento = CaixaMovimentacao(
            caixa_id=caixa.id,
            usuario_id=usuario_id,
            tipo=tipo_norm,
            categoria=categoria,
            valor=valor_dec,
            descricao=(descricao or "").strip() or None,
        )
        CaixaMovimentacaoRepository.create(db, movimento)
        CaixaRepository.update(db, caixa)
        db.commit()
        db.refresh(caixa)
        return movimento

    @staticmethod
    def registrar_entrada_pagamento_os(
        db: Session,
        ordem_servico_id: int,
        forma_pagamento: str,
        valor: Decimal,
        usuario_id: int = None,
    ):
        caixa = CaixaRepository.get_caixa_aberto(db)
        if not caixa:
            raise ValueError("Abra o caixa antes de registrar pagamento da OS")

        valor_dec = CaixaService._to_money(valor)
        if valor_dec <= Decimal("0.00"):
            raise ValueError("Valor do pagamento inválido para caixa")

        caixa.saldo_atual = CaixaService._to_money(caixa.saldo_atual) + valor_dec

        movimento = CaixaMovimentacao(
            caixa_id=caixa.id,
            ordem_servico_id=ordem_servico_id,
            usuario_id=usuario_id,
            tipo="entrada",
            categoria="pagamento_os",
            forma_pagamento=(forma_pagamento or "").strip().lower() or None,
            valor=valor_dec,
            descricao=f"Recebimento da OS #{ordem_servico_id}",
        )
        CaixaMovimentacaoRepository.create(db, movimento)
        CaixaRepository.update(db, caixa)
        return movimento
