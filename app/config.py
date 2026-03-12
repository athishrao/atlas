from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./tnlinks.db"
    tnlinks_admins: str = ""
    auth_header: str = "X-Forwarded-User"
    base_url: str = "http://tn"
    debug: bool = False

    @property
    def admin_list(self) -> list[str]:
        return [e.strip() for e in self.tnlinks_admins.split(",") if e.strip()]

    class Config:
        env_file = ".env"

settings = Settings()
