from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./atlas.db"
    atlas_admins: str = ""
    auth_header: str = "X-Forwarded-User"
    base_url: str = "http://tn"
    app_name: str = "atlas"
    debug: bool = False

    @property
    def admin_list(self) -> list[str]:
        return [e.strip() for e in self.atlas_admins.split(",") if e.strip()]

    @property
    def prefix(self) -> str:
        """Display prefix from base_url, e.g. 'http://tn' → 'tn'"""
        return self.base_url.split("//")[-1].rstrip("/")

    class Config:
        env_file = ".env"

settings = Settings()
