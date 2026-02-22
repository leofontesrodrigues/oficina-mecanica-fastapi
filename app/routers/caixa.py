import csv
import os
from datetime import date, datetime, time
from io import BytesIO, StringIO
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.services.caixa_service import CaixaService

router = APIRouter(prefix="/caixa", tags=["Caixa"])
templates = Jinja2Templates(directory="app/templates")


def _parse_date(value: str):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


@router.get("/", response_class=HTMLResponse)
def painel_caixa(
    request: Request,
    date_from: str = "",
    date_to: str = "",
    db: Session = Depends(get_db),
):
    caixa_aberto = CaixaService.obter_caixa_aberto(db)
    caixa_referencia = caixa_aberto or CaixaService.obter_ultimo_caixa(db)

    d_from = _parse_date(date_from)
    d_to = _parse_date(date_to)
    dt_inicio = datetime.combine(d_from, time.min) if d_from else None
    dt_fim = datetime.combine(d_to, time.max) if d_to else None

    if dt_inicio or dt_fim:
        movimentos = CaixaService.listar_movimentacoes_periodo(db, dt_inicio=dt_inicio, dt_fim=dt_fim)
    else:
        movimentos = CaixaService.listar_movimentacoes(db, caixa_referencia.id) if caixa_referencia else []

    total_entradas = sum(float(m.valor) for m in movimentos if m.tipo == "entrada")
    total_saidas = sum(float(m.valor) for m in movimentos if m.tipo == "saida")

    return templates.TemplateResponse(
        "caixa/caixa.html",
        {
            "request": request,
            "caixa_aberto": caixa_aberto,
            "caixa_referencia": caixa_referencia,
            "movimentos": movimentos,
            "total_entradas": total_entradas,
            "total_saidas": total_saidas,
            "date_from": date_from,
            "date_to": date_to,
            "success": request.query_params.get("success"),
            "error": request.query_params.get("error"),
        },
    )


@router.post("/abrir")
def abrir_caixa(
    request: Request,
    saldo_inicial: float = Form(0),
    observacao: str = Form(None),
    db: Session = Depends(get_db),
):
    try:
        CaixaService.abrir_caixa(
            db=db,
            saldo_inicial=saldo_inicial,
            usuario_id=request.session.get("user_id"),
            observacao=observacao,
        )
        msg = quote("Caixa aberto com sucesso")
        return RedirectResponse(f"/caixa?success={msg}", status_code=303)
    except Exception as e:
        msg = quote(str(e))
        return RedirectResponse(f"/caixa?error={msg}", status_code=303)


@router.post("/fechar")
def fechar_caixa(
    request: Request,
    valor_contado: float = Form(...),
    observacao: str = Form(None),
    db: Session = Depends(get_db),
):
    try:
        CaixaService.fechar_caixa(
            db=db,
            usuario_id=request.session.get("user_id"),
            valor_contado=valor_contado,
            observacao=observacao,
        )
        msg = quote("Caixa fechado com sucesso")
        return RedirectResponse(f"/caixa?success={msg}", status_code=303)
    except Exception as e:
        msg = quote(str(e))
        return RedirectResponse(f"/caixa?error={msg}", status_code=303)


@router.get("/movimentacoes.csv")
def exportar_movimentacoes_csv(
    date_from: str = "",
    date_to: str = "",
    db: Session = Depends(get_db),
):
    d_from = _parse_date(date_from)
    d_to = _parse_date(date_to)
    dt_inicio = datetime.combine(d_from, time.min) if d_from else None
    dt_fim = datetime.combine(d_to, time.max) if d_to else None

    movimentos = CaixaService.listar_movimentacoes_periodo(db, dt_inicio=dt_inicio, dt_fim=dt_fim)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "data_movimentacao",
            "tipo",
            "categoria",
            "forma_pagamento",
            "ordem_servico_id",
            "descricao",
            "valor",
        ]
    )

    for mov in movimentos:
        writer.writerow(
            [
                mov.id,
                mov.data_movimentacao.isoformat() if mov.data_movimentacao else "",
                mov.tipo,
                mov.categoria,
                mov.forma_pagamento or "",
                mov.ordem_servico_id or "",
                mov.descricao or "",
                float(mov.valor or 0),
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=relatorio_caixa_movimentacoes.csv"},
    )


@router.get("/movimentacoes.pdf")
def exportar_movimentacoes_pdf(
    date_from: str = "",
    date_to: str = "",
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

    d_from = _parse_date(date_from)
    d_to = _parse_date(date_to)
    dt_inicio = datetime.combine(d_from, time.min) if d_from else None
    dt_fim = datetime.combine(d_to, time.max) if d_to else None

    movimentos = CaixaService.listar_movimentacoes_periodo(db, dt_inicio=dt_inicio, dt_fim=dt_fim)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
        title="Relatorio de Caixa",
    )
    styles = getSampleStyleSheet()
    story = []

    logo_path = os.path.join("app", "static", "img", "logo.jpeg")
    if os.path.exists(logo_path):
        logo = RLImage(logo_path, width=2.1 * cm, height=2.1 * cm)
        head = Table(
            [[logo, Paragraph("<b>Relatorio de Caixa - Movimentacoes</b><br/>Garagem 90 - Oficina Mecanica", styles["Title"])]],
            colWidths=[2.5 * cm, 23.0 * cm],
        )
        head.setStyle(
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
        story.append(head)
    else:
        story.append(Paragraph("<b>Relatorio de Caixa - Movimentacoes</b>", styles["Title"]))

    story.append(Spacer(1, 0.3 * cm))
    filtro_texto = []
    if d_from:
        filtro_texto.append(f"De: {d_from.strftime('%d/%m/%Y')}")
    if d_to:
        filtro_texto.append(f"Até: {d_to.strftime('%d/%m/%Y')}")
    if filtro_texto:
        story.append(Paragraph(" | ".join(filtro_texto), styles["Normal"]))
        story.append(Spacer(1, 0.2 * cm))

    if not movimentos:
        story.append(Paragraph("Nenhuma movimentacao no periodo informado.", styles["Normal"]))
        doc.build(story)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=relatorio_caixa_movimentacoes.pdf"},
        )

    total_entradas = sum(float(m.valor or 0) for m in movimentos if m.tipo == "entrada")
    total_saidas = sum(float(m.valor or 0) for m in movimentos if m.tipo == "saida")
    saldo = total_entradas - total_saidas
    story.append(Paragraph(f"Entradas: R$ {total_entradas:.2f} | Saidas: R$ {total_saidas:.2f} | Saldo: R$ {saldo:.2f}", styles["Normal"]))
    story.append(Spacer(1, 0.25 * cm))

    table_data = [["Data", "Tipo", "Categoria", "Forma", "OS", "Descricao", "Valor"]]
    for mov in movimentos:
        table_data.append(
            [
                mov.data_movimentacao.strftime("%d/%m/%Y %H:%M") if mov.data_movimentacao else "-",
                mov.tipo,
                mov.categoria,
                mov.forma_pagamento or "-",
                f"#{mov.ordem_servico_id}" if mov.ordem_servico_id else "-",
                (mov.descricao or "-")[:80],
                f"R$ {float(mov.valor or 0):.2f}",
            ]
        )

    table = Table(
        table_data,
        repeatRows=1,
        colWidths=[3.2 * cm, 2.2 * cm, 3.2 * cm, 2.0 * cm, 1.6 * cm, 9.8 * cm, 2.4 * cm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#9ca3af")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
            ]
        )
    )
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=relatorio_caixa_movimentacoes.pdf"},
    )


@router.post("/suprimento")
def registrar_suprimento(
    request: Request,
    valor: float = Form(...),
    descricao: str = Form(None),
    db: Session = Depends(get_db),
):
    try:
        CaixaService.registrar_movimento_manual(
            db=db,
            tipo="entrada",
            valor=valor,
            descricao=descricao or "Suprimento de caixa",
            usuario_id=request.session.get("user_id"),
            categoria="suprimento",
        )
        msg = quote("Suprimento registrado")
        return RedirectResponse(f"/caixa?success={msg}", status_code=303)
    except Exception as e:
        msg = quote(str(e))
        return RedirectResponse(f"/caixa?error={msg}", status_code=303)


@router.post("/sangria")
def registrar_sangria(
    request: Request,
    valor: float = Form(...),
    descricao: str = Form(None),
    db: Session = Depends(get_db),
):
    try:
        CaixaService.registrar_movimento_manual(
            db=db,
            tipo="saida",
            valor=valor,
            descricao=descricao or "Sangria de caixa",
            usuario_id=request.session.get("user_id"),
            categoria="sangria",
        )
        msg = quote("Sangria registrada")
        return RedirectResponse(f"/caixa?success={msg}", status_code=303)
    except Exception as e:
        msg = quote(str(e))
        return RedirectResponse(f"/caixa?error={msg}", status_code=303)
