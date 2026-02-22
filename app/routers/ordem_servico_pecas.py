from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import quote

from app.core.dependencies import get_db

from app.repositories.ordem_servico_peca_repo import OrdemServicoPecaRepository
from app.services.ordem_servico_peca_service import OrdemServicoPecaService


router = APIRouter(prefix="/os-pecas")


@router.post("/adicionar/{os_id}")
def adicionar_peca(
    request: Request,
    os_id: int,

    peca_id: int = Form(...),
    quantidade: int = Form(...),
    search: str = Form(""),
    page: int = Form(1),

    db: Session = Depends(get_db)
):

    try:

        OrdemServicoPecaService.adicionar_peca(
            db,
            os_id,
            peca_id,
            quantidade,
            usuario_id=request.session.get("user_id"),
        )

        msg = quote("Peça adicionada com sucesso")

        return RedirectResponse(
            f"/ordens-servico/{os_id}?page={page}&search={quote(search)}&success={msg}",
            status_code=303
        )

    except Exception as e:

        msg = quote(str(e))

        return RedirectResponse(
            f"/ordens-servico/{os_id}?page={page}&search={quote(search)}&error={msg}",
            status_code=303
        )


@router.post("/remover/{os_peca_id}")
def remover_peca(
    request: Request,
    os_peca_id: int,
    search: str = Form(""),
    page: int = Form(1),
    db: Session = Depends(get_db)
):
    os_peca = OrdemServicoPecaRepository.get_by_id(db, os_peca_id)

    if not os_peca:
        msg = quote("Peça da OS não encontrada")
        return RedirectResponse(
            f"/ordens-servico?page={page}&search={quote(search)}&error={msg}",
            status_code=303
        )

    os_id = os_peca.ordem_servico_id

    try:
        OrdemServicoPecaService.remover_peca(
            db,
            os_peca_id,
            usuario_id=request.session.get("user_id"),
        )
        msg = quote("Peça removida da OS e estoque estornado")
        return RedirectResponse(
            f"/ordens-servico/{os_id}?page={page}&search={quote(search)}&success={msg}",
            status_code=303
        )

    except Exception as e:
        msg = quote(str(e))
        return RedirectResponse(
            f"/ordens-servico/{os_id}?page={page}&search={quote(search)}&error={msg}",
            status_code=303
        )
