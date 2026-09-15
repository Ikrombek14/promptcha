from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_secret: str = "dev-secret"
    frontend_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"  # vergul bilan ajratilgan

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/promptcha"

    # AI — provayderlar zanjiri va umumiy limitlar (CLAUDE.md: max_tokens ≤ 1500, temperature 0.4)
    # Tartib muhim: birinchisi asosiy, kvota tugasa keyingisi. Kaliti yoʻqlar tashlab ketiladi.
    ai_providers: str = "gemini"  # gemini | groq | mistral | openrouter | custom | anthropic
    ai_max_tokens: int = 1500
    ai_temperature: float = 0.4

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.7-flash"
    gemini_thinking_level: str = "low"  # minimal | low | medium | high | "" (oʻchirilgan)
    gemini_fallback_models: str = ""  # 429/503 boʻlsa navbat bilan (vergul bilan)

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_fallback_models: str = "openai/gpt-oss-20b,qwen/qwen3.8-27b"

    mistral_api_key: str = ""
    mistral_model: str = "mistral-small-latest"
    mistral_fallback_models: str = ""

    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/free"
    openrouter_fallback_models: str = ""

    # Quyidagilar kalit kelganda /v1/models orqali model nomi tekshirib qoʻyiladi
    sambanova_api_key: str = ""
    sambanova_model: str = "Meta-Llama-3.3-70B-Instruct"
    sambanova_fallback_models: str = ""

    huggingface_api_key: str = ""
    huggingface_model: str = "meta-llama/Llama-3.3-70B-Instruct"
    huggingface_fallback_models: str = ""

    hyperbolic_api_key: str = ""
    hyperbolic_model: str = "meta-llama/Llama-3.3-70B-Instruct"
    hyperbolic_fallback_models: str = ""

    cerebras_api_key: str = ""
    cerebras_model: str = "llama-3.3-70b"
    cerebras_fallback_models: str = ""

    cohere_api_key: str = ""
    cohere_model: str = "command-a-03-2025"
    cohere_fallback_models: str = ""

    # Istalgan boshqa OpenAI-mos server (/v1/chat/completions)
    custom_base_url: str = ""
    custom_api_key: str = "no-key"
    custom_model: str = ""
    custom_fallback_models: str = ""

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    jwt_secret: str = "dev-jwt-secret"
    jwt_expire_days: int = 30
    session_cookie_name: str = "promptcha_session"
    # Admin — Google email roʻyxati (vergul bilan). Alohida parol yoʻq.
    admin_emails: str = ""
    # Faqat dev: GET /api/auth/dev-login?email=... bilan Google'siz kirish (prod'da taqiqlanadi)
    auth_dev_login: bool = False

    # Bepul limitlar — .env dagi default; admin `app_settings` orqali oʻzgartira oladi
    free_daily_generations: int = 5
    guest_total_generations: int = 3
    guest_daily_ip_generations: int = 15  # bitta IP dan kuniga (guest_id almashtirishga qarshi)

    # Xavfsizlik
    internal_api_key: str = ""  # Nginx har soʻrovga X-Internal-Key qoʻshadi; prod'da majburiy
    trust_proxy: bool = False  # true boʻlsa IP X-Forwarded-For dan olinadi (faqat Nginx orqasida)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def production_problems(self) -> list[str]:
        """Prod'da xavfli default qiymatlar — server ishga tushmaydi."""
        problems = []
        if not self.is_production:
            return problems
        if (
            self.app_secret in ("dev-secret", "change-me-long-random-string")
            or len(self.app_secret) < 32
        ):
            problems.append("APP_SECRET kamida 32 belgili tasodifiy boʻlishi kerak")
        if (
            self.jwt_secret in ("dev-jwt-secret", "change-me-another-long-random-string")
            or len(self.jwt_secret) < 32
        ):
            problems.append("JWT_SECRET kamida 32 belgili tasodifiy boʻlishi kerak")
        if len(self.internal_api_key) < 32:
            problems.append(
                "INTERNAL_API_KEY kamida 32 belgili boʻlishi kerak (Nginx bilan bir xil)"
            )
        if not self.trust_proxy:
            problems.append("TRUST_PROXY=true boʻlishi kerak (Nginx orqasida)")
        if any("localhost" in o or "127.0.0.1" in o for o in self.cors_origin_list):
            problems.append("CORS_ORIGINS da localhost boʻlmasin")
        if not self.frontend_url.startswith("https://"):
            problems.append("FRONTEND_URL https:// bilan boshlanishi kerak")
        if "postgres:postgres@" in self.database_url or ":1899@" in self.database_url:
            problems.append("DATABASE_URL da zaif parol")
        if self.auth_dev_login:
            problems.append("AUTH_DEV_LOGIN prod'da yoqilmasin")
        if self.google_client_id and not self.google_redirect_uri.startswith("https://"):
            problems.append("GOOGLE_REDIRECT_URI https:// bilan boshlanishi kerak")
        return problems

    @property
    def admin_email_list(self) -> list[str]:
        return [e.strip().lower() for e in self.admin_emails.split(",") if e.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
