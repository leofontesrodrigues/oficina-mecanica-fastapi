from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from urllib.parse import quote
import re

from app.core.dependencies import get_db
from app.services.veiculo_service import VeiculoService
from app.services.cliente_service import ClienteService
from app.schemas.veiculo_schema import VeiculoCreate

router = APIRouter(prefix="/veiculos", tags=["Veículos"])
templates = Jinja2Templates(directory="app/templates")

PLACA_REGEX = r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$"

@router.get("/", response_class=HTMLResponse)
def indice_veiculos(
    request: Request,
    search: str = "",
    page: int = 1,
    db: Session = Depends(get_db)
):
    per_page = 10

    clientes, total = ClienteService.listar_clientes(
        db,
        search=search,
        page=page,
        per_page=per_page
    )

    total_pages = (total + per_page - 1) // per_page

    return templates.TemplateResponse(
        "veiculos/index.html",
        {
            "request": request,
            "clientes": clientes,
            "search": search,
            "page": page,
            "total_pages": total_pages,
            "success": request.query_params.get("success"),
            "error": request.query_params.get("error"),
        }
    )


@router.post("/novo")
def criar_veiculo(
    cliente_id: int = Form(...),
    placa: str = Form(...),
    marca: str = Form(...),
    modelo: str = Form(...),
    ano: int = Form(None),
    cor: str = Form(None),
    db: Session = Depends(get_db)
):
    placa = re.sub(r"[^A-Z0-9]", "", placa.upper())

    if not re.match(PLACA_REGEX, placa):
        msg = quote("Placa inválida")
        return RedirectResponse(
            f"/veiculos/cliente/{cliente_id}?error={msg}",
            status_code=303
        )

    veiculo_data = VeiculoCreate(
        cliente_id=cliente_id,
        placa=placa,
        marca=marca,
        modelo=modelo,
        ano=ano,
        cor=cor
    )

    resultado = VeiculoService.criar_veiculo(db, veiculo_data)

    if not resultado:
        msg = quote("Placa já cadastrada")
        return RedirectResponse(
            f"/veiculos/cliente/{cliente_id}?error={msg}",
            status_code=303
        )

    msg = quote("Veículo cadastrado com sucesso")
    return RedirectResponse(
        f"/veiculos/cliente/{cliente_id}?success={msg}",
        status_code=303
    )

@router.post("/editar/{veiculo_id}")
def editar_veiculo(
    veiculo_id: int,
    cliente_id: int = Form(...),
    placa: str = Form(None),
    marca: str = Form(None),
    modelo: str = Form(None),
    ano: int = Form(None),
    cor: str = Form(None),
    db: Session = Depends(get_db)
):
    if placa:
        placa = re.sub(r"[^A-Z0-9]", "", placa.upper())
        if not re.match(PLACA_REGEX, placa):
            msg = quote("Placa inválida")
            return RedirectResponse(
                f"/veiculos/cliente/{cliente_id}?error={msg}",
                status_code=303
            )

    # validação manual (igual cliente)
    if not marca or not modelo:
        msg = quote("Marca e modelo são obrigatórios")
        return RedirectResponse(
            f"/veiculos/cliente/{cliente_id}?error={msg}",
            status_code=303
        )

    veiculo_data = VeiculoCreate(
        cliente_id=cliente_id,
        placa=placa,
        marca=marca,
        modelo=modelo,
        ano=ano,
        cor=cor
    )

    resultado = VeiculoService.editar_veiculo(db, veiculo_id, veiculo_data)

    if not resultado:
        msg = quote("Veículo não encontrado")
        return RedirectResponse(
            f"/veiculos/cliente/{cliente_id}?error={msg}",
            status_code=303
        )

    msg = quote("Veículo atualizado com sucesso")
    return RedirectResponse(
        f"/veiculos/cliente/{cliente_id}?success={msg}",
        status_code=303
    )

@router.get("/cliente/{cliente_id}", response_class=HTMLResponse)
def listar_veiculos_cliente(
    request: Request,
    cliente_id: int,
    db: Session = Depends(get_db)
):
    veiculos = VeiculoService.listar_por_cliente(db, cliente_id)

    success = request.query_params.get("success")
    error = request.query_params.get("error")

    return templates.TemplateResponse(
        "veiculos/veiculos.html",
        {
            "request": request,
            "veiculos": veiculos,
            "cliente_id": cliente_id,
            "success": success,
            "error": error,
        }
    )

@router.post("/excluir/{veiculo_id}")
def excluir_veiculo(
    veiculo_id: int,
    cliente_id: int = Form(...),
    db: Session = Depends(get_db)
):
    resultado = VeiculoService.excluir_veiculo(db, veiculo_id)

    if not resultado:
        msg = quote("Veículo não encontrado")
        return RedirectResponse(
            f"/veiculos/cliente/{cliente_id}?error={msg}",
            status_code=303
        )

    msg = quote("Veículo excluído com sucesso")
    return RedirectResponse(
        f"/veiculos/cliente/{cliente_id}?success={msg}",
        status_code=303
    )


