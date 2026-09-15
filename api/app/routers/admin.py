"""/api/admin — statistika, foydalanuvchilar, toʻlovlar, sozlamalar (faqat ADMIN_EMAILS).

STUB: C-agent toʻldiradi (spec: docs/superpowers/specs/2026-09-15-auth-admin-design.md).
"""

from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])
