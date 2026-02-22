from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.servico_schema import ServicoCreate
from app.services.servico_service import ServicoService

router = APIRouter(prefix="/servicos", tags=["Serviços"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def listar_servicos(
    request: Request,
    search: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
):
    per_page = 10

    servicos, total = ServicoService.listar(
        db,
        search=search,
        page=page,
        per_page=per_page,
    )

    total_pages = (total + per_page - 1) // per_page

    return templates.TemplateResponse(
        "servicos/servicos.html",
        {
            "request": request,
            "servicos": servicos,
            "search": search,
            "page": page,
            "total_pages": total_pages,
            "success": request.query_params.get("success"),
            "error": request.query_params.get("error"),
        },
    )


@router.post("/novo")
def criar_servico(
    descricao: str = Form(...),
    preco_base: float = Form(...),
    search: str = Form(""),
    page: int = Form(1),
    db: Session = Depends(get_db),
):
    try:
        data = ServicoCreate(descricao=descricao, preco_base=preco_base)
        ServicoService.criar(db, data)

        msg = quote("Serviço cadastrado")
        return RedirectResponse(
            f"/servicos?page={page}&search={quote(search)}&success={msg}",
            status_code=303,
        )
    except Exception as e:
        msg = quote(str(e))
        return RedirectResponse(
            f"/servicos?page={page}&search={quote(search)}&error={msg}",
            status_code=303,
        )


@router.post("/editar/{servico_id}")
def editar_servico(
    servico_id: int,
    descricao: str = Form(...),
    preco_base: float = Form(...),
    search: str = Form(""),
    page: int = Form(1),
    db: Session = Depends(get_db),
):
    try:
        data = ServicoCreate(descricao=descricao, preco_base=preco_base)
        ServicoService.editar(db, servico_id, data)

        msg = quote("Serviço atualizado")
        return RedirectResponse(
            f"/servicos?page={page}&search={quote(search)}&success={msg}",
            status_code=303,
        )
    except Exception as e:
        msg = quote(str(e))
        return RedirectResponse(
            f"/servicos?page={page}&search={quote(search)}&error={msg}",
            status_code=303,
        )


@router.get("/excluir/{servico_id}")
def excluir_servico(
    servico_id: int,
    search: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
):
    try:
        ServicoService.excluir(db, servico_id)
        msg = quote("Serviço removido")
        return RedirectResponse(
            f"/servicos?page={page}&search={quote(search)}&success={msg}",
            status_code=303,
        )
    except Exception as e:
        msg = quote(str(e))
        return RedirectResponse(
            f"/servicos?page={page}&search={quote(search)}&error={msg}",
            status_code=303,
        )
