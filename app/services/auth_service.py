from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.usuario import Usuario
from app.repositories.usuario_repo import UsuarioRepository


class AuthService:

    @staticmethod
    def autenticar(db: Session, email: str, senha: str):
        usuario = UsuarioRepository.get_by_email(db, email.lower().strip())

        if not usuario or not usuario.ativo:
            return None

        if not verify_password(senha, usuario.senha_hash):
            return None

        return usuario

    @staticmethod
    def listar_usuarios(db: Session):
        return UsuarioRepository.get_all(db)

    @staticmethod
    def buscar_por_email(db: Session, email: str):
        return UsuarioRepository.get_by_email(db, email.lower().strip())

    @staticmethod
    def criar_usuario(
        db: Session,
        nome: str,
        email: str,
        senha: str,
        perfil: str = "atendente",
        ativo: bool = True,
    ):
        perfil = (perfil or "").strip().lower()
        email = email.lower().strip()

        if perfil not in {"admin", "atendente", "mecanico"}:
            raise ValueError("Perfil inválido")

        if UsuarioRepository.get_by_email(db, email):
            raise ValueError("E-mail já cadastrado")

        if len(senha or "") < 6:
            raise ValueError("Senha deve ter ao menos 6 caracteres")

        usuario = Usuario(
            nome=nome.strip(),
            email=email,
            senha_hash=hash_password(senha),
            perfil=perfil,
            ativo=ativo,
        )
        return UsuarioRepository.create(db, usuario)

    @staticmethod
    def gerar_token_reset(email: str) -> str:
        exp = datetime.now(timezone.utc) + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": email.lower().strip(),
            "type": "reset",
            "exp": exp,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.SECRET_ALGORITHM)

    @staticmethod
    def validar_token_reset(token: str) -> str:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.SECRET_ALGORITHM])
            if payload.get("type") != "reset":
                return None
            return payload.get("sub")
        except JWTError:
            return None

    @staticmethod
    def redefinir_senha(db: Session, token: str, nova_senha: str):
        email = AuthService.validar_token_reset(token)
        if not email:
            raise ValueError("Token inválido ou expirado")

        usuario = UsuarioRepository.get_by_email(db, email)
        if not usuario:
            raise ValueError("Usuário não encontrado")

        if len(nova_senha or "") < 6:
            raise ValueError("Senha deve ter ao menos 6 caracteres")

        usuario.senha_hash = hash_password(nova_senha)
        UsuarioRepository.update(db, usuario)

    @staticmethod
    def inicializar_admin_padrao(db: Session):
        if UsuarioRepository.count_all(db) > 0:
            return

        AuthService.criar_usuario(
            db=db,
            nome=settings.DEFAULT_ADMIN_NAME,
            email=settings.DEFAULT_ADMIN_EMAIL,
            senha=settings.DEFAULT_ADMIN_PASSWORD,
            perfil="admin",
            ativo=True,
        )
