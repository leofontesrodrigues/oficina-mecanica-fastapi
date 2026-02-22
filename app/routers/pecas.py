from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from urllib.parse import quote

from app.core.dependencies import get_db
from app.services.estoque_service import EstoqueService
from app.services.peca_service import PecaService
from app.repositories.peca_repo import PecaRepository
from app.repositories.ordem_servico_peca_repo import OrdemServicoPecaRepository

router = APIRouter(prefix="/pecas", tags=["Peças"])

templates = Jinja2Templates(directory="app/templates")


# 📌 LISTAR
@router.get("/", response_class=HTMLResponse)
def listar_pecas(
    request: Request,
    search: str = "",
    page: int = 1,
    db: Session = Depends(get_db)
):

    per_page = 10

    pecas, total = PecaService.listar(
        db,
        search=search,
        page=page,
        per_page=per_page
    )

    total_pages = (total + per_page - 1) // per_page

    success = request.query_params.get("success")
    error = request.query_params.get("error")

    return templates.TemplateResponse(
        "pecas/pecas.html",
        {
            "request": request,
            "pecas": pecas,
            "success": success,
            "error": error,
            "search": search,
            "page": page,
            "total_pages": total_pages
        }
    )


# 📌 CRIAR
@router.post("/nova")
def criar_peca(
    request: Request,
    nome: str = Form(...),
    codigo: str = Form(...),
    preco: float = Form(...),
    estoque: int = Form(...),
    search: str = Form(""),
    page: int = Form(1),

    db: Session = Depends(get_db)
):

    try:

        existente = PecaRepository.get_by_codigo(db, codigo)

        if existente:
            raise ValueError("Código já cadastrado")

        PecaService.criar(
            db,
            nome,
            codigo,
            preco,
            estoque,
            usuario_id=request.session.get("user_id"),
        )

        msg = quote("Peça cadastrada")

        return RedirectResponse(
            f"/pecas?page={page}&search={quote(search)}&success={msg}",
            status_code=303
        )

    except Exception as e:

        msg = quote(str(e))

        return RedirectResponse(
            f"/pecas?page={page}&search={quote(search)}&error={msg}",
            status_code=303
        )


# 📌 EXCLUIR
@router.get("/excluir/{peca_id}")
def excluir_peca(
    peca_id: int,
    search: str = "",
    page: int = 1,
    db: Session = Depends(get_db)
):

    peca = PecaRepository.get_by_id(db, peca_id)

    if not peca:

        msg = quote("Peça não encontrada")

        return RedirectResponse(
            f"/pecas?page={page}&search={quote(search)}&error={msg}",
            status_code=303
        )

    # ✅ NOVO: verificar uso
    em_uso = OrdemServicoPecaRepository.existe_uso_da_peca(
        db,
        peca_id
    )

    if em_uso:

        msg = quote("Peça já utilizada em OS. Não pode excluir.")

        return RedirectResponse(
            f"/pecas?page={page}&search={quote(search)}&error={msg}",
            status_code=303
        )

    PecaRepository.delete(db, peca)

    msg = quote("Peça removida")

    return RedirectResponse(
        f"/pecas?page={page}&search={quote(search)}&success={msg}",
        status_code=303
    )

# 📌 EDITAR
@router.post("/editar/{peca_id}")
def editar_peca(
    peca_id: int,

    nome: str = Form(...),
    codigo: str = Form(...),
    preco: float = Form(...),
    search: str = Form(""),
    page: int = Form(1),

    db: Session = Depends(get_db)
):

    try:

        peca = PecaRepository.get_by_id(db, peca_id)

        if not peca:
            raise ValueError("Peça não encontrada")

        # Verificar código duplicado
        existente = PecaRepository.get_by_codigo(db, codigo)

        if existente and existente.id != peca_id:
            raise ValueError("Código já existe em outra peça")

        # Atualizar dados
        peca.nome = nome
        peca.codigo = codigo
        peca.preco = preco

        db.commit()

        msg = quote("Peça atualizada")

        return RedirectResponse(
            f"/pecas?page={page}&search={quote(search)}&success={msg}",
            status_code=303
        )

    except Exception as e:

        msg = quote(str(e))

        return RedirectResponse(
            f"/pecas?page={page}&search={quote(search)}&error={msg}",
            status_code=303
        )


@router.post("/ajustar-estoque/{peca_id}")
def ajustar_estoque_peca(
    request: Request,
    peca_id: int,
    estoque: int = Form(...),
    observacao: str = Form(None),
    search: str = Form(""),
    page: int = Form(1),
    db: Session = Depends(get_db)
):
    try:
        PecaService.definir_estoque(
            db,
            peca_id,
            estoque,
            usuario_id=request.session.get("user_id"),
            observacao=observacao,
        )

        msg = quote("Estoque ajustado com sucesso")
        return RedirectResponse(
            f"/pecas?page={page}&search={quote(search)}&success={msg}",
            status_code=303
        )
    except Exception as e:
        msg = quote(str(e))
        return RedirectResponse(
            f"/pecas?page={page}&search={quote(search)}&error={msg}",
            status_code=303
        )


@router.get("/movimentacoes", response_class=HTMLResponse)
def listar_movimentacoes_estoque(
    request: Request,
    search: str = "",
    tipo: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
):
    per_page = 20
    movimentacoes, total = EstoqueService.listar_movimentacoes(
        db,
        search=search,
        tipo=tipo,
        page=page,
        per_page=per_page,
    )
    total_pages = (total + per_page - 1) // per_page

    return templates.TemplateResponse(
        "pecas/movimentacoes.html",
        {
            "request": request,
            "movimentacoes": movimentacoes,
            "search": search,
            "tipo": tipo,
            "page": page,
            "total_pages": total_pages,
            "success": request.query_params.get("success"),
            "error": request.query_params.get("error"),
        },
    )
