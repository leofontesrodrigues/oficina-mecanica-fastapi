from fastapi import APIRouter, Request, Depends, Form, File, UploadFile
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from urllib.parse import quote
import re

from app.core.dependencies import get_db
from app.core.uploads import remove_uploaded_file, save_image_upload
from app.services.mecanico_service import MecanicoService


router = APIRouter(prefix="/mecanicos", tags=["Mecânicos"])

templates = Jinja2Templates(directory="app/templates")


# 📌 LISTAR
@router.get("/", response_class=HTMLResponse)
def listar(
    request: Request,
    search: str = "",
    page: int = 1,
    db: Session = Depends(get_db)
):

    per_page = 10

    mecanicos, total = MecanicoService.listar(
        db,
        search=search,
        page=page,
        per_page=per_page
    )

    total_pages = (total + per_page - 1) // per_page

    success = request.query_params.get("success")
    error = request.query_params.get("error")

    return templates.TemplateResponse(
        "mecanicos/mecanicos.html",
        {
            "request": request,
            "mecanicos": mecanicos,
            "success": success,
            "error": error,
            "search": search,
            "page": page,
            "total_pages": total_pages
        }
    )


# 📌 CRIAR
@router.post("/novo")
def criar(
    nome: str = Form(...),
    telefone: str = Form(None),
    especialidade: str = Form(None),
    ativo: bool = Form(True),
    foto: UploadFile = File(None),
    search: str = "",
    page: int = 1,
    db: Session = Depends(get_db)
):

    try:
        telefone_limpo = re.sub(r"\D", "", telefone or "")
        foto_path = save_image_upload(foto, prefix="mecanico") if foto and foto.filename else None

        MecanicoService.criar(
            db,
            nome,
            telefone_limpo,
            especialidade,
            ativo,
            foto_path=foto_path,
        )

        msg = quote("Mecânico cadastrado com sucesso")

        return RedirectResponse(
            f"/mecanicos?page={page}&search={quote(search)}&success={msg}",
            status_code=303
        )

    except Exception as e:

        msg = quote(str(e) if str(e) else "Erro ao cadastrar mecânico")

        return RedirectResponse(
            f"/mecanicos?page={page}&search={quote(search)}&error={msg}",
            status_code=303
        )


# 📌 EDITAR
@router.post("/editar/{mecanico_id}")
def editar(
    mecanico_id: int,

    nome: str = Form(...),
    telefone: str = Form(None),
    especialidade: str = Form(None),
    ativo: bool = Form(True),
    foto: UploadFile = File(None),
    search: str = "",
    page: int = 1,

    db: Session = Depends(get_db)
):

    telefone_limpo = re.sub(r"\D", "", telefone or "")
    mecanico_existente = MecanicoService.buscar_por_id(db, mecanico_id)
    if not mecanico_existente:
        msg = quote("Mecânico não encontrado")
        return RedirectResponse(
            f"/mecanicos?page={page}&search={quote(search)}&error={msg}",
            status_code=303
        )

    foto_path = mecanico_existente.foto_path
    if foto and foto.filename:
        nova_foto = save_image_upload(foto, prefix="mecanico")
        remove_uploaded_file(mecanico_existente.foto_path)
        foto_path = nova_foto

    try:
        result = MecanicoService.atualizar(
            db,
            mecanico_id,
            nome,
            telefone_limpo,
            especialidade,
            ativo,
            foto_path=foto_path,
        )

        if not result:
            msg = quote("Mecânico não encontrado")
            return RedirectResponse(
                f"/mecanicos?page={page}&search={quote(search)}&error={msg}",
                status_code=303
            )

        msg = quote("Mecânico atualizado")

        return RedirectResponse(
            f"/mecanicos?page={page}&search={quote(search)}&success={msg}",
            status_code=303
        )
    except Exception as e:
        msg = quote(str(e) if str(e) else "Erro ao atualizar mecânico")
        return RedirectResponse(
            f"/mecanicos?page={page}&search={quote(search)}&error={msg}",
            status_code=303
        )


# 📌 EXCLUIR
@router.get("/excluir/{mecanico_id}")
def excluir(
    mecanico_id: int,
    search: str = "",
    page: int = 1,
    db: Session = Depends(get_db)
):
    mecanico = MecanicoService.buscar_por_id(db, mecanico_id)

    result = MecanicoService.excluir(db, mecanico_id)

    if not result:
        msg = quote("Mecânico não encontrado")
        return RedirectResponse(
            f"/mecanicos?page={page}&search={quote(search)}&error={msg}",
            status_code=303
        )

    if mecanico:
        remove_uploaded_file(mecanico.foto_path)

    msg = quote("Mecânico removido")

    return RedirectResponse(
        f"/mecanicos?page={page}&search={quote(search)}&success={msg}",
        status_code=303
    )
