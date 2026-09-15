import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.rate_limit import limiter
from app.routers import prompts
from app.security import SecurityMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    from app.db import engine

    await engine.dispose()


settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")

# Prod'da xavfli sozlamalar bilan ishga tushmaydi
_problems = settings.production_problems()
if _problems:
    raise RuntimeError("Xavfsiz emas, ishga tushirilmadi:\n- " + "\n- ".join(_problems))

app = FastAPI(
    title="Promptcha API",
    version="0.1.0",
    docs_url="/api/docs" if settings.is_dev else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if settings.is_dev else None,
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: faqat oʻz saytimiz, faqat kerakli metod va sarlavhalar
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Requested-With"],
    max_age=600,
)
# Eng tashqi qatlam: Origin/Referer, X-Requested-With, X-Internal-Key, tana hajmi, sarlavhalar
app.add_middleware(SecurityMiddleware, settings=settings)

app.include_router(prompts.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
