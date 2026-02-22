from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.caixa import Caixa
from app.models.cliente import Cliente
from app.models.ordem_servico import OrdemServico
from app.models.peca import Peca
from app.models.veiculo import Veiculo

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    db: Session = Depends(get_db),
):
    total_clientes = db.query(func.count(Cliente.id)).scalar() or 0
    total_veiculos = db.query(func.count(Veiculo.id)).scalar() or 0

    os_abertas = (
        db.query(func.count(OrdemServico.id))
        .filter(OrdemServico.status.in_(["orcamento", "aberta", "em_andamento"]))
        .scalar()
        or 0
    )

    inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    faturamento_mes = (
        db.query(func.coalesce(func.sum(OrdemServico.valor_total), 0))
        .filter(OrdemServico.status == "finalizada")
        .filter(OrdemServico.data_fechamento >= inicio_mes)
        .scalar()
        or 0
    )

    caixa_aberto = (
        db.query(Caixa)
        .filter(Caixa.status == "aberto")
        .order_by(Caixa.id.desc())
        .first()
    )

    pecas_estoque_baixo = (
        db.query(Peca)
        .filter(Peca.estoque <= 5)
        .order_by(Peca.estoque.asc(), Peca.nome.asc())
        .limit(8)
        .all()
    )

    ultimas_os = (
        db.query(OrdemServico)
        .order_by(OrdemServico.id.desc())
        .limit(8)
        .all()
    )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "total_clientes": total_clientes,
            "total_veiculos": total_veiculos,
            "os_abertas": os_abertas,
            "faturamento_mes": float(faturamento_mes or 0),
            "caixa_aberto": caixa_aberto,
            "pecas_estoque_baixo": pecas_estoque_baixo,
            "ultimas_os": ultimas_os,
            "success": request.query_params.get("success"),
            "error": request.query_params.get("error"),
        },
    )

