from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.config import settings
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])
templates = Jinja2Templates(directory="app/templates")


def _is_admin(request: Request) -> bool:
    return request.session.get("user_perfil") == "admin"


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("user_id"):
        perfil = request.session.get("user_perfil")
        destino = "/ordens-servico" if perfil == "mecanico" else "/dashboard"
        return RedirectResponse(url=destino, status_code=303)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": request.query_params.get("error"),
            "success": request.query_params.get("success"),
            "show_default_admin_hint": settings.SHOW_DEFAULT_ADMIN_HINT,
        },
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
):
    usuario = AuthService.autenticar(db, email=email, senha=senha)

    if not usuario:
        msg = quote("Credenciais inválidas ou usuário inativo")
        return RedirectResponse(url=f"/auth/login?error={msg}", status_code=303)

    request.session["user_id"] = usuario.id
    request.session["user_nome"] = usuario.nome
    request.session["user_email"] = usuario.email
    request.session["user_perfil"] = usuario.perfil

    destino = "/ordens-servico" if usuario.perfil == "mecanico" else "/dashboard"
    return RedirectResponse(url=destino, status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    msg = quote("Sessão encerrada")
    return RedirectResponse(url=f"/auth/login?success={msg}", status_code=303)


@router.get("/usuarios", response_class=HTMLResponse)
def usuarios_page(request: Request, db: Session = Depends(get_db)):
    if not _is_admin(request):
        msg = quote("Apenas admin pode gerenciar usuários")
        return RedirectResponse(url=f"/dashboard?error={msg}", status_code=303)

    usuarios = AuthService.listar_usuarios(db)

    return templates.TemplateResponse(
        "auth/usuarios.html",
        {
            "request": request,
            "usuarios": usuarios,
            "success": request.query_params.get("success"),
            "error": request.query_params.get("error"),
        },
    )


@router.post("/usuarios/novo")
def criar_usuario(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    perfil: str = Form("atendente"),
    senha: str = Form(...),
    confirmar_senha: str = Form(...),
    ativo: bool = Form(False),
    db: Session = Depends(get_db),
):
    if not _is_admin(request):
        msg = quote("Apenas admin pode criar usuários")
        return RedirectResponse(url=f"/dashboard?error={msg}", status_code=303)

    if senha != confirmar_senha:
        msg = quote("Senha e confirmação estão diferentes")
        return RedirectResponse(url=f"/auth/usuarios?error={msg}", status_code=303)

    try:
        AuthService.criar_usuario(
            db=db,
            nome=nome,
            email=email,
            senha=senha,
            perfil=perfil,
            ativo=ativo,
        )

        msg = quote("Usuário cadastrado com sucesso")
        return RedirectResponse(url=f"/auth/usuarios?success={msg}", status_code=303)
    except Exception as e:
        msg = quote(str(e))
        return RedirectResponse(url=f"/auth/usuarios?error={msg}", status_code=303)


@router.get("/esqueci-senha", response_class=HTMLResponse)
def esqueci_senha_page(request: Request):
    return templates.TemplateResponse(
        "auth/esqueci_senha.html",
        {
            "request": request,
            "error": request.query_params.get("error"),
            "success": request.query_params.get("success"),
        },
    )


@router.post("/esqueci-senha")
def esqueci_senha(
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    usuario = AuthService.buscar_por_email(db, email)

    if not usuario:
        msg = quote("E-mail não cadastrado")
        return RedirectResponse(url=f"/auth/esqueci-senha?error={msg}", status_code=303)

    token = AuthService.gerar_token_reset(usuario.email)

    return RedirectResponse(
        url=f"/auth/redefinir-senha?token={quote(token)}",
        status_code=303,
    )


@router.get("/redefinir-senha", response_class=HTMLResponse)
def redefinir_senha_page(request: Request, token: str = ""):
    email = AuthService.validar_token_reset(token) if token else None

    if not email:
        msg = "Link inválido ou expirado. Solicite novamente."
        return templates.TemplateResponse(
            "auth/redefinir_senha.html",
            {
                "request": request,
                "error": msg,
                "success": None,
                "token": None,
            },
        )

    return templates.TemplateResponse(
        "auth/redefinir_senha.html",
        {
            "request": request,
            "error": request.query_params.get("error"),
            "success": request.query_params.get("success"),
            "token": token,
        },
    )


@router.post("/redefinir-senha")
def redefinir_senha(
    token: str = Form(...),
    senha: str = Form(...),
    confirmar_senha: str = Form(...),
    db: Session = Depends(get_db),
):
    if senha != confirmar_senha:
        msg = quote("Senha e confirmação estão diferentes")
        return RedirectResponse(url=f"/auth/redefinir-senha?token={quote(token)}&error={msg}", status_code=303)

    try:
        AuthService.redefinir_senha(db, token, senha)
        msg = quote("Senha redefinida com sucesso")
        return RedirectResponse(url=f"/auth/login?success={msg}", status_code=303)
    except Exception as e:
        msg = quote(str(e))
        return RedirectResponse(url=f"/auth/redefinir-senha?token={quote(token)}&error={msg}", status_code=303)
