from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5433/certificate_generator",
        env="DATABASE_URL"
    )
    
    # JWT
    jwt_secret_key: str = Field(
        default="your-super-secret-jwt-key-change-in-production",
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours
    
    # Application
    debug: bool = Field(default=False, env="DEBUG")
    
    # Default admin credentials
    default_admin_username: str = Field(default="admin", env="DEFAULT_ADMIN_USERNAME")
    default_admin_password: str = Field(default="admin123", env="DEFAULT_ADMIN_PASSWORD")
    
    # Certificate paths
    certs_dir: str = "/app/certs"
    certs_output_dir: str = "/app/certs_output"
    
    # Certificate settings
    cert_country: str = "IN"
    cert_state: str = "Gujarat"
    cert_city: str = "Vadodara"
    cert_organization: str = "Prahari Technologies"
    cert_org_unit: str = "Prahari Technologies"
    cert_validity_days: int = 365
    cert_key_size: int = 2048
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
