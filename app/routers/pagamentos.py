from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.services.pagamento_service import PagamentoService

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])


@router.post("/novo/{os_id}")
def registrar_pagamento(
    request: Request,
    os_id: int,
    tipo: str = Form(...),
    valor: float = Form(...),
    search: str = Form(""),
    page: int = Form(1),
    db: Session = Depends(get_db),
):
    try:
        resultado = PagamentoService.registrar_pagamento(
            db=db,
            ordem_servico_id=os_id,
            tipo=tipo,
            valor=valor,
            usuario_id=request.session.get("user_id"),
        )

        troco = resultado.get("troco", 0) if isinstance(resultado, dict) else 0
        if troco > 0:
            msg = quote(f"Pagamento registrado com sucesso. Troco: R$ {troco:.2f}")
        else:
            msg = quote("Pagamento registrado com sucesso")
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
