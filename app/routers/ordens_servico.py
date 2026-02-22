import os as os_lib
from urllib.parse import quote
import re
from io import BytesIO

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.repositories.cliente_repo import ClienteRepository
from app.repositories.ordem_servico_peca_repo import OrdemServicoPecaRepository
from app.repositories.peca_repo import PecaRepository
from app.repositories.veiculo_repo import VeiculoRepository
from app.services.mecanico_service import MecanicoService
from app.services.ordem_servico_service import OrdemServicoService
from app.services.pagamento_service import PagamentoService
from app.services.servico_service import ServicoService
from app.services.servico_os_service import ServicoOSService

router = APIRouter(prefix="/ordens-servico", tags=["Ordens de Serviço"])
templates = Jinja2Templates(directory="app/templates")


def _normalizar_telefone_whatsapp(telefone: str) -> str:
    digits = re.sub(r"\D", "", telefone or "")
    if len(digits) in {10, 11}:
        return f"55{digits}"
    return digits


@router.get("/", response_class=HTMLResponse)
def listar_os(
    request: Request,
    search: str = "",
    page: int = 1,
    new_os: int = 0,
    cliente_id: int = None,
    veiculo_id: int = None,
    db: Session = Depends(get_db),
):
    per_page = 10

    ordens, total = OrdemServicoService.listar_os(
        db,
        search=search,
        page=page,
        per_page=per_page,
    )

    total_pages = (total + per_page - 1) // per_page

    clientes = ClienteRepository.get_all(db)
    veiculos = VeiculoRepository.get_all(db)
    mecanicos = MecanicoService.listar_ativos(db)

    success = request.query_params.get("success")
    error = request.query_params.get("error")

    return templates.TemplateResponse(
        "ordem_servicos/ordens_servico.html",
        {
            "request": request,
            "ordens": ordens,
            "clientes": clientes,
            "veiculos": veiculos,
            "mecanicos": mecanicos,
            "success": success,
            "error": error,
            "search": search,
            "page": page,
            "total_pages": total_pages,
            "new_os": new_os,
            "pre_cliente_id": cliente_id,
            "pre_veiculo_id": veiculo_id,
        },
    )


@router.post("/nova")
def criar_os(
    cliente_id: int = Form(...),
    veiculo_id: int = Form(...),
    mecanico_id: int = Form(None),
    observacoes: str = Form(None),
    search: str = Form(""),
    page: int = Form(1),
    db: Session = Depends(get_db),
):
    try:
        OrdemServicoService.criar_os_menu(
            db=db,
            cliente_id=cliente_id,
            veiculo_id=veiculo_id,
            mecanico_id=mecanico_id,
            observacoes=observacoes,
        )

        msg = quote("Orçamento criado com sucesso")

        return RedirectResponse(
            f"/ordens-servico?page={page}&search={quote(search)}&success={msg}",
            status_code=303,
        )

    except Exception:
        msg = quote("Erro ao criar OS")

        return RedirectResponse(
            f"/ordens-servico?page={page}&search={quote(search)}&error={msg}",
            status_code=303,
        )


@router.post("/{os_id}/status")
def atualizar_status_os(
    os_id: int,
    request: Request,
    status: str = Form(...),
    search: str = Form(""),
    page: int = Form(1),
    db: Session = Depends(get_db),
):
    perfil = request.session.get("user_perfil")
    status_destino = (status or "").strip().lower()

    if perfil == "mecanico" and status_destino in {"cancelada", "aberta", "reprovada"}:
        msg = quote("Mecânico não pode aprovar, reprovar ou cancelar OS")
        return RedirectResponse(
            f"/ordens-servico/{os_id}?page={page}&search={quote(search)}&error={msg}",
            status_code=303,
        )

    try:
        OrdemServicoService.atualizar_status(
            db,
            os_id,
            status,
            usuario_id=request.session.get("user_id"),
        )
        msg = quote("Status da OS atualizado")
        return RedirectResponse(
            f"/ordens-servico/{os_id}?page={page}&search={quote(search)}&success={msg}",
            status_code=303,
        )
    except Exception as e:
        msg = quote(str(e))
        return RedirectResponse(
            f"/ordens-servico/{os_id}?page={page}&search={quote(search)}&error={msg}",
            status_code=303,
        )


@router.post("/{os_id}/reprovar-orcamento")
def reprovar_orcamento(
    os_id: int,
    request: Request,
    motivo: str = Form(...),
    search: str = Form(""),
    page: int = Form(1),
    db: Session = Depends(get_db),
):
    perfil = request.session.get("user_perfil")
    if perfil == "mecanico":
        msg = quote("Mecânico não pode reprovar orçamento")
        return RedirectResponse(
            f"/ordens-servico/{os_id}?page={page}&search={quote(search)}&error={msg}",
            status_code=303,
        )

    try:
        OrdemServicoService.reprovar_orcamento(
            db,
            os_id,
            motivo=motivo,
            usuario_id=request.session.get("user_id"),
        )
        msg = quote("Orçamento reprovado com sucesso")
        return RedirectResponse(
            f"/ordens-servico/{os_id}?page={page}&search={quote(search)}&success={msg}",
            status_code=303,
        )
    except Exception as e:
        msg = quote(str(e))
        return RedirectResponse(
            f"/ordens-servico/{os_id}?page={page}&search={quote(search)}&error={msg}",
            status_code=303,
        )


@router.get("/{os_id}", response_class=HTMLResponse)
def detalhe_os(
    os_id: int,
    request: Request,
    search: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
):
    os = OrdemServicoService.buscar_por_id(db, os_id)

    if not os:
        msg = quote("Ordem de serviço não encontrada")
        return RedirectResponse(
            f"/ordens-servico?page={page}&search={quote(search)}&error={msg}",
            status_code=303,
        )

    servicos_os = ServicoOSService.listar(db, os_id)
    servicos_catalogo = ServicoService.listar_todos(db)
    pecas = PecaRepository.get_all(db)
    pecas_os = OrdemServicoPecaRepository.listar_por_os(db, os_id)

    pagamentos = PagamentoService.listar_pagamentos_por_os(db, os_id)
    total_pago = PagamentoService.obter_total_pago(db, os_id)
    saldo_pendente = float(os.valor_total) - total_pago

    success = request.query_params.get("success")
    error = request.query_params.get("error")

    return templates.TemplateResponse(
        "ordem_servicos/detalhe_os.html",
        {
            "request": request,
            "os": os,
            "servicos_os": servicos_os,
            "servicos_catalogo": servicos_catalogo,
            "pecas": pecas,
            "pecas_os": pecas_os,
            "pagamentos": pagamentos,
            "total_pago": total_pago,
            "saldo_pendente": saldo_pendente,
            "success": success,
            "error": error,
            "search": search,
            "page": page,
        },
    )


@router.get("/{os_id}/orcamento.pdf")
def baixar_orcamento_pdf(
    os_id: int,
    search: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Image as RLImage,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    ordem = OrdemServicoService.buscar_por_id(db, os_id)
    if not ordem:
        msg = quote("Ordem de serviço não encontrada")
        return RedirectResponse(
            f"/ordens-servico?page={page}&search={quote(search)}&error={msg}",
            status_code=303,
        )

    servicos_os = ServicoOSService.listar(db, os_id)
    pecas_os = OrdemServicoPecaRepository.listar_por_os(db, os_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.4 * cm,
        rightMargin=1.4 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        title=f"Orcamento OS {ordem.id}",
    )

    styles = getSampleStyleSheet()
    story = []

    logo_path = os_lib.path.join("app", "static", "img", "logo.jpeg")
    if os_lib.path.exists(logo_path):
        logo = RLImage(logo_path, width=2.0 * cm, height=2.0 * cm)
        cabecalho = Table(
            [
                [
                    logo,
                    Paragraph(
                        f"<b>Orçamento - Ordem de Serviço #{ordem.id}</b><br/>Garagem 90 - Oficina Mecânica",
                        styles["Title"],
                    ),
                ]
            ],
            colWidths=[2.4 * cm, 14.4 * cm],
        )
        cabecalho.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(cabecalho)
    else:
        story.append(Paragraph(f"<b>Orçamento - Ordem de Serviço #{ordem.id}</b>", styles["Title"]))

    story.append(Spacer(1, 0.5 * cm))

    abertura = ordem.data_abertura.strftime("%d/%m/%Y %H:%M") if ordem.data_abertura else "-"
    cliente_nome = ordem.cliente.nome if ordem.cliente else "-"
    cliente_cpf = ordem.cliente.cpf_cnpj if ordem.cliente else "-"
    cliente_fone = ordem.cliente.telefone if ordem.cliente else "-"
    veiculo_desc = (
        f"{ordem.veiculo.placa} - {ordem.veiculo.marca} {ordem.veiculo.modelo}"
        if ordem.veiculo
        else "-"
    )
    mecanico_nome = ordem.mecanico.nome if ordem.mecanico else "-"

    dados_cliente = Table(
        [
            ["Cliente", cliente_nome, "CPF/CNPJ", cliente_cpf or "-"],
            ["Telefone", cliente_fone or "-", "Veículo", veiculo_desc],
            ["Mecânico", mecanico_nome, "Abertura", abertura],
        ],
        colWidths=[2.6 * cm, 6.2 * cm, 2.8 * cm, 5.2 * cm],
    )
    dados_cliente.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(dados_cliente)
    story.append(Spacer(1, 0.35 * cm))

    story.append(Paragraph("<b>Serviços</b>", styles["Heading4"]))
    tabela_servicos = [["Descrição", "Qtd", "Valor Unit.", "Total"]]
    total_servicos = 0.0
    for item in servicos_os:
        subtotal = float(item.quantidade * item.valor_unitario)
        total_servicos += subtotal
        tabela_servicos.append(
            [
                item.servico.descricao if item.servico else "-",
                str(item.quantidade),
                f"R$ {float(item.valor_unitario):.2f}",
                f"R$ {subtotal:.2f}",
            ]
        )
    if len(tabela_servicos) == 1:
        tabela_servicos.append(["Nenhum serviço informado", "-", "-", "-"])

    tabela_servicos_obj = Table(tabela_servicos, colWidths=[9.0 * cm, 1.8 * cm, 2.8 * cm, 2.8 * cm], repeatRows=1)
    tabela_servicos_obj.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(tabela_servicos_obj)
    story.append(Spacer(1, 0.35 * cm))

    story.append(Paragraph("<b>Peças</b>", styles["Heading4"]))
    tabela_pecas = [["Peça", "Qtd", "Valor Unit.", "Total"]]
    total_pecas = 0.0
    for item in pecas_os:
        subtotal = float(item.quantidade * item.valor_unitario)
        total_pecas += subtotal
        tabela_pecas.append(
            [
                item.peca.nome if item.peca else "-",
                str(item.quantidade),
                f"R$ {float(item.valor_unitario):.2f}",
                f"R$ {subtotal:.2f}",
            ]
        )
    if len(tabela_pecas) == 1:
        tabela_pecas.append(["Nenhuma peça informada", "-", "-", "-"])

    tabela_pecas_obj = Table(tabela_pecas, colWidths=[9.0 * cm, 1.8 * cm, 2.8 * cm, 2.8 * cm], repeatRows=1)
    tabela_pecas_obj.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(tabela_pecas_obj)
    story.append(Spacer(1, 0.35 * cm))

    total_geral = float(ordem.valor_total or 0)
    resumo = Table(
        [
            ["Subtotal serviços", f"R$ {total_servicos:.2f}"],
            ["Subtotal peças", f"R$ {total_pecas:.2f}"],
            ["Total do orçamento", f"R$ {total_geral:.2f}"],
        ],
        colWidths=[12.2 * cm, 4.2 * cm],
    )
    resumo.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e2e8f0")),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ]
        )
    )
    story.append(resumo)

    if (ordem.observacoes or "").strip():
        story.append(Spacer(1, 0.35 * cm))
        story.append(Paragraph("<b>Observações</b>", styles["Heading4"]))
        story.append(Paragraph(ordem.observacoes.replace("\n", "<br/>"), styles["Normal"]))

    doc.build(story)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=orcamento_os_{ordem.id}.pdf"},
    )


@router.get("/{os_id}/whatsapp")
def enviar_os_whatsapp(
    os_id: int,
    search: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
):
    os = OrdemServicoService.buscar_por_id(db, os_id)
    if not os:
        msg = quote("Ordem de serviço não encontrada")
        return RedirectResponse(
            f"/ordens-servico?page={page}&search={quote(search)}&error={msg}",
            status_code=303,
        )

    telefone = _normalizar_telefone_whatsapp(os.cliente.telefone if os.cliente else "")
    if len(telefone) < 12:
        msg = quote("Cliente sem telefone válido para WhatsApp")
        return RedirectResponse(
            f"/ordens-servico/{os_id}?page={page}&search={quote(search)}&error={msg}",
            status_code=303,
        )

    abertura = os.data_abertura.strftime("%d/%m/%Y %H:%M") if os.data_abertura else "-"
    fechamento = os.data_fechamento.strftime("%d/%m/%Y %H:%M") if os.data_fechamento else "-"

    texto = (
        f"Olá, {os.cliente.nome}!\n"
        f"Sua Ordem de Serviço #{os.id}:\n"
        f"- Veículo: {os.veiculo.placa} ({os.veiculo.modelo})\n"
        f"- Status: {os.status}\n"
        f"- Abertura: {abertura}\n"
        f"- Fechamento: {fechamento}\n"
        f"- Valor total: R$ {float(os.valor_total or 0):.2f}\n"
        f"- Observações: {os.observacoes or '-'}"
    )

    return RedirectResponse(
        f"https://wa.me/{telefone}?text={quote(texto)}",
        status_code=303,
    )
