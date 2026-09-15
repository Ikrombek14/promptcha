"""/api/auth — Google OAuth, sessiya, chiqish, guest promptlarni koʻchirish.

STUB: A-agent toʻldiradi (spec: docs/superpowers/specs/2026-09-15-auth-admin-design.md).
"""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])
