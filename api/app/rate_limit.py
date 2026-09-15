from slowapi import Limiter
from starlette.requests import Request

from app.security import client_ip


def _key(request: Request) -> str:
    return client_ip(request)


# Daqiqalik limitlar real IP boʻyicha (Nginx orqasida X-Forwarded-For, TRUST_PROXY=true bilan)
limiter = Limiter(key_func=_key)
