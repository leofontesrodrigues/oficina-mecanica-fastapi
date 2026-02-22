from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import quote

from app.core.dependencies import get_db
from app.services.servico_os_service import ServicoOSService
from app.repositories.servico_os_repository import ServicoOSRepository
from app.schemas.servico_os_schema import ServicoOSCreate
from app.services.servico_service import ServicoService


router = APIRouter(prefix="/servicos-os")


@router.post("/novo/{os_id}")
def adicionar_servico(
    os_id: int,

    servico_id: int = Form(...),
    quantidade: int = Form(1),
    valor_unitario: str = Form(""),
    search: str = Form(""),
    page: int = Form(1),

    db: Session = Depends(get_db)
):

    try:
        servico = ServicoService.buscar_por_id(db, servico_id)
        if not servico:
            raise ValueError("Serviço de catálogo não encontrado")

        valor_unitario_convertido = (
            float(valor_unitario)
            if str(valor_unitario).strip()
            else float(servico.preco_base)
        )

        data = ServicoOSCreate(
            ordem_servico_id=os_id,
            servico_id=servico_id,
            quantidade=quantidade,
            valor_unitario=valor_unitario_convertido,
        )

        ServicoOSService.criar(db, data)

        msg = quote("Serviço adicionado")

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


@router.post("/remover/{os_servico_id}")
def remover_servico(
    os_servico_id: int,
    search: str = Form(""),
    page: int = Form(1),
    db: Session = Depends(get_db),
):
    os_servico = ServicoOSRepository.get_by_id(db, os_servico_id)

    if not os_servico:
        msg = quote("Serviço da OS não encontrado")
        return RedirectResponse(
            f"/ordens-servico?page={page}&search={quote(search)}&error={msg}",
            status_code=303,
        )

    os_id = os_servico.ordem_servico_id

    try:
        ServicoOSService.remover(db, os_servico_id)
        msg = quote("Serviço removido da OS")
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
