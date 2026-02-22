from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import inspect, text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.database.session import SessionLocal, engine
from app.database.base import Base
import app.models  # noqa: F401
from app.routers import (
    auth,
    caixa,
    clientes,
    dashboard,
    mecanicos,
    ordem_servico_pecas,
    ordens_servico,
    pagamentos,
    pecas,
    relatorios,
    servicos,
    servicos_os,
    veiculos,
)
from app.services.auth_service import AuthService

app = FastAPI(title=settings.PROJECT_NAME)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if is_public_path(path):
            return await call_next(request)

        user_id = request.session.get("user_id")
        perfil = request.session.get("user_perfil")

        if not user_id:
            return RedirectResponse(url="/auth/login", status_code=303)

        if not has_permission(path, perfil):
            msg = quote("Você não tem permissão para acessar esta área")
            destino = "/ordens-servico" if perfil == "mecanico" else "/dashboard"
            return RedirectResponse(url=f"{destino}?error={msg}", status_code=303)

        return await call_next(request)


app.add_middleware(AuthMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="oficina_session",
    max_age=60 * 60 * 8,
)

app.include_router(auth.router)
app.include_router(caixa.router)
app.include_router(clientes.router)
app.include_router(dashboard.router)
app.include_router(veiculos.router)
app.include_router(ordens_servico.router)
app.include_router(mecanicos.router)
app.include_router(servicos_os.router)
app.include_router(ordem_servico_pecas.router)
app.include_router(pagamentos.router)
app.include_router(servicos.router)
app.include_router(pecas.router)
app.include_router(relatorios.router)

templates = Jinja2Templates(directory="app/templates")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

PUBLIC_PATH_PREFIXES = (
    "/auth/login",
    "/auth/esqueci-senha",
    "/auth/redefinir-senha",
    "/static",
    "/openapi.json",
    "/docs",
    "/redoc",
    "/favicon.ico",
)


def is_public_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES)


def has_permission(path: str, perfil: str) -> bool:
    if perfil == "admin":
        return True

    if perfil == "atendente":
        return not path.startswith("/mecanicos")

    if perfil == "mecanico":
        return (
            path == "/"
            or path.startswith("/ordens-servico")
            or path.startswith("/servicos-os")
            or path.startswith("/os-pecas")
            or path.startswith("/auth/logout")
        )

    return False


def ensure_schema_compatibility():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    if "caixas" in table_names:
        columns = {c["name"] for c in inspector.get_columns("caixas")}
        with engine.begin() as conn:
            if "valor_contado_fechamento" not in columns:
                conn.execute(text("ALTER TABLE caixas ADD COLUMN valor_contado_fechamento NUMERIC(10,2)"))
            if "diferenca_fechamento" not in columns:
                conn.execute(text("ALTER TABLE caixas ADD COLUMN diferenca_fechamento NUMERIC(10,2)"))

    if "clientes" in table_names:
        columns = {c["name"] for c in inspector.get_columns("clientes")}

        with engine.begin() as conn:
            if "cpf_cnpj" not in columns:
                conn.execute(text("ALTER TABLE clientes ADD COLUMN cpf_cnpj VARCHAR(18)"))
            if "cep" not in columns:
                conn.execute(text("ALTER TABLE clientes ADD COLUMN cep VARCHAR(10)"))
            if "bairro" not in columns:
                conn.execute(text("ALTER TABLE clientes ADD COLUMN bairro VARCHAR(120)"))
            if "cidade" not in columns:
                conn.execute(text("ALTER TABLE clientes ADD COLUMN cidade VARCHAR(120)"))
            if "uf" not in columns:
                conn.execute(text("ALTER TABLE clientes ADD COLUMN uf VARCHAR(2)"))
            if "foto_path" not in columns:
                conn.execute(text("ALTER TABLE clientes ADD COLUMN foto_path VARCHAR(255)"))

            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ux_clientes_cpf_cnpj "
                    "ON clientes (cpf_cnpj) WHERE cpf_cnpj IS NOT NULL"
                )
            )

    if "mecanicos" in table_names:
        columns = {c["name"] for c in inspector.get_columns("mecanicos")}
        with engine.begin() as conn:
            if "foto_path" not in columns:
                conn.execute(text("ALTER TABLE mecanicos ADD COLUMN foto_path VARCHAR(255)"))

    # Migração de estrutura antiga de serviços em OS para modelo N:N
    table_names = inspector.get_table_names()
    if "servicos_os" not in table_names or "ordem_servico_servicos" not in table_names:
        return

    with engine.begin() as conn:
        total_novo = conn.execute(
            text("SELECT COUNT(*) FROM ordem_servico_servicos")
        ).scalar() or 0

        if total_novo > 0:
            return

        legacy_rows = conn.execute(
            text(
                "SELECT ordem_servico_id, descricao, valor "
                "FROM servicos_os"
            )
        ).fetchall()

        for row in legacy_rows:
            servico_id = conn.execute(
                text(
                    "SELECT id FROM servicos WHERE descricao = :descricao LIMIT 1"
                ),
                {"descricao": row.descricao},
            ).scalar()

            if not servico_id:
                conn.execute(
                    text(
                        "INSERT INTO servicos (descricao, preco_base) "
                        "VALUES (:descricao, :preco_base)"
                    ),
                    {
                        "descricao": row.descricao,
                        "preco_base": float(row.valor or 0),
                    },
                )
                servico_id = conn.execute(
                    text(
                        "SELECT id FROM servicos WHERE descricao = :descricao LIMIT 1"
                    ),
                    {"descricao": row.descricao},
                ).scalar()

            conn.execute(
                text(
                    "INSERT INTO ordem_servico_servicos "
                    "(ordem_servico_id, servico_id, quantidade, valor_unitario) "
                    "VALUES (:ordem_servico_id, :servico_id, :quantidade, :valor_unitario)"
                ),
                {
                    "ordem_servico_id": row.ordem_servico_id,
                    "servico_id": servico_id,
                    "quantidade": 1,
                    "valor_unitario": float(row.valor or 0),
                },
            )


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility()

    db = SessionLocal()
    try:
        AuthService.inicializar_admin_padrao(db)
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/auth/login", status_code=303)

    perfil = request.session.get("user_perfil")

    if perfil == "mecanico":
        return RedirectResponse(url="/ordens-servico", status_code=303)

    return RedirectResponse(url="/dashboard", status_code=303)
