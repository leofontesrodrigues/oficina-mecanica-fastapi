from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Oficina Mecânica"
    DATABASE_URL: str = "postgresql+psycopg2://oficina_user:oficina123@localhost:5432/oficina_db"
    DB_SSLMODE: str = ""

    SECRET_KEY: str = "change-me-in-production"
    SECRET_ALGORITHM: str = "HS256"
    RESET_TOKEN_EXPIRE_MINUTES: int = 30

    DEFAULT_ADMIN_NAME: str = "Administrador"
    DEFAULT_ADMIN_EMAIL: str = "admin@oficina.local"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    SHOW_DEFAULT_ADMIN_HINT: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
