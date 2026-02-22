import csv
import os
from datetime import date, datetime, time
from io import BytesIO, StringIO
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.cliente import Cliente
from app.models.ordem_servico import OrdemServico
from app.models.pagamento import Pagamento

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])
templates = Jinja2Templates(directory="app/templates")


def _parse_date(value: str):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _filtrar_os(query, date_from: str = "", date_to: str = "", status: str = ""):
    d_from = _parse_date(date_from)
    d_to = _parse_date(date_to)

    if d_from:
        query = query.filter(OrdemServico.data_abertura >= datetime.combine(d_from, time.min))
    if d_to:
        query = query.filter(OrdemServico.data_abertura <= datetime.combine(d_to, time.max))
    if status:
        query = query.filter(OrdemServico.status == status)

    return query


@router.get("/", response_class=HTMLResponse)
def dashboard_relatorios(
    request: Request,
    date_from: str = "",
    date_to: str = "",
    status: str = "",
    db: Session = Depends(get_db),
):
    base_query = db.query(OrdemServico)
    base_query = _filtrar_os(base_query, date_from=date_from, date_to=date_to, status=status)

    ordens = base_query.order_by(OrdemServico.id.desc()).all()

    total_os = len(ordens)
    total_orcamentos = sum(1 for os in ordens if os.status == "orcamento")
    total_reprovadas = sum(1 for os in ordens if os.status == "reprovada")
    total_abertas = sum(1 for os in ordens if os.status in {"aberta", "em_andamento"})
    total_finalizadas = sum(1 for os in ordens if os.status == "finalizada")
    total_canceladas = sum(1 for os in ordens if os.status == "cancelada")
    total_faturado = float(sum(float(os.valor_total or 0) for os in ordens if os.status == "finalizada"))

    pagamentos_query = db.query(Pagamento).join(
        OrdemServico, Pagamento.ordem_servico_id == OrdemServico.id
    )
    pagamentos_query = _filtrar_os(pagamentos_query, date_from=date_from, date_to=date_to, status=status)
    total_pago = float(pagamentos_query.with_entities(func.coalesce(func.sum(Pagamento.valor), 0)).scalar() or 0)

    top_clientes_query = (
        db.query(
            Cliente.nome.label("cliente_nome"),
            func.count(OrdemServico.id).label("qtd_os"),
            func.coalesce(func.sum(OrdemServico.valor_total), 0).label("valor_os"),
        )
        .join(OrdemServico, OrdemServico.cliente_id == Cliente.id)
    )
    top_clientes_query = _filtrar_os(top_clientes_query, date_from=date_from, date_to=date_to, status=status)
    top_clientes = (
        top_clientes_query
        .group_by(Cliente.id, Cliente.nome)
        .order_by(func.count(OrdemServico.id).desc())
        .limit(10)
        .all()
    )

    return templates.TemplateResponse(
        "relatorios/dashboard.html",
        {
            "request": request,
            "ordens": ordens[:15],
            "date_from": date_from,
            "date_to": date_to,
            "status": status,
            "total_os": total_os,
            "total_orcamentos": total_orcamentos,
            "total_reprovadas": total_reprovadas,
            "total_abertas": total_abertas,
            "total_finalizadas": total_finalizadas,
            "total_canceladas": total_canceladas,
            "total_faturado": total_faturado,
            "total_pago": total_pago,
            "top_clientes": top_clientes,
            "success": request.query_params.get("success"),
            "error": request.query_params.get("error"),
        },
    )


@router.get("/ordens-servico.csv")
def exportar_csv_os(
    date_from: str = "",
    date_to: str = "",
    status: str = "",
    db: Session = Depends(get_db),
):
    query = db.query(OrdemServico).order_by(OrdemServico.id.desc())
    query = _filtrar_os(query, date_from=date_from, date_to=date_to, status=status)
    ordens = query.all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "cliente",
            "veiculo_placa",
            "mecanico",
            "status",
            "data_abertura",
            "data_fechamento",
            "valor_total",
        ]
    )

    for os in ordens:
        writer.writerow(
            [
                os.id,
                os.cliente.nome if os.cliente else "",
                os.veiculo.placa if os.veiculo else "",
                os.mecanico.nome if os.mecanico else "",
                os.status,
                os.data_abertura.isoformat() if os.data_abertura else "",
                os.data_fechamento.isoformat() if os.data_fechamento else "",
                float(os.valor_total or 0),
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=relatorio_ordens_servico.csv"},
    )


@router.get("/ordens-servico.pdf")
def exportar_pdf_os(
    date_from: str = "",
    date_to: str = "",
    status: str = "",
    db: Session = Depends(get_db),
):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
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

    query = db.query(OrdemServico).order_by(OrdemServico.id.desc())
    query = _filtrar_os(query, date_from=date_from, date_to=date_to, status=status)
    ordens = query.all()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
        title="Relatorio de Ordens de Servico",
    )

    styles = getSampleStyleSheet()
    story = []

    logo_path = os.path.join("app", "static", "img", "logo.jpeg")
    if os.path.exists(logo_path):
        logo = RLImage(logo_path, width=2.2 * cm, height=2.2 * cm)
        header_table = Table(
            [
                [
                    logo,
                    Paragraph(
                        "<b>Relatorio de Ordens de Servico</b><br/>"
                        "Garagem 90 - Oficina Mecanica",
                        styles["Title"],
                    ),
                ]
            ],
            colWidths=[2.6 * cm, 23.5 * cm],
        )
        header_table.setStyle(
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
        story.append(header_table)
    else:
        story.append(Paragraph("<b>Relatorio de Ordens de Servico</b>", styles["Title"]))

    story.append(Spacer(1, 0.2 * cm))
    story.append(Spacer(1, 0.35 * cm))

    total_registros = len(ordens)
    story.append(Paragraph(f"Total de registros: <b>{total_registros}</b>", styles["Normal"]))
    story.append(Spacer(1, 0.3 * cm))

    if not ordens:
        story.append(Paragraph("Nenhuma ordem de servico encontrada para os filtros informados.", styles["Normal"]))
        doc.build(story)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=relatorio_ordens_servico.pdf"},
        )

    table_data = [
        [
            "ID",
            "Cliente",
            "CPF",
            "Telefone",
            "Veiculo",
            "Status",
            "Abertura",
            "Fechamento",
            "Total",
        ]
    ]

    for item in ordens:
        cliente_nome = item.cliente.nome if item.cliente else "-"
        cliente_cpf = item.cliente.cpf_cnpj if item.cliente else "-"
        cliente_fone = item.cliente.telefone if item.cliente else "-"
        veiculo = f"{item.veiculo.placa} - {item.veiculo.modelo}" if item.veiculo else "-"
        abertura = item.data_abertura.strftime("%d/%m/%Y %H:%M") if item.data_abertura else "-"
        fechamento = item.data_fechamento.strftime("%d/%m/%Y %H:%M") if item.data_fechamento else "-"
        total = f"R$ {float(item.valor_total or 0):.2f}"

        table_data.append(
            [
                str(item.id),
                cliente_nome,
                cliente_cpf,
                cliente_fone or "-",
                veiculo,
                item.status,
                abertura,
                fechamento,
                total,
            ]
        )

    report_table = Table(
        table_data,
        repeatRows=1,
        colWidths=[1.2 * cm, 4.8 * cm, 3.0 * cm, 3.0 * cm, 5.4 * cm, 2.4 * cm, 3.2 * cm, 3.2 * cm, 2.5 * cm],
    )
    report_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 7.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#9ca3af")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    story.append(report_table)
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=relatorio_ordens_servico.pdf"},
    )
