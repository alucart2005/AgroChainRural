"""Auditoría de un ancla concreto del contrato de NEAR.

No lo usa el frontend: la ruta pública del consumidor es
``GET /api/verify/{codigo}``, que recomputa el hash del lote y contrasta su
propio ancla. Este endpoint acepta cualquier ``codigo`` + ``hash_hex`` y
dispara una consulta ``view`` al contrato, así que exige ``X-API-Key``: sin
ella sería un proxy abierto y gratuito a la red de NEAR.

Antes aceptaba un ``tx_hash`` suelta para auditar una transacción de Stellar.
Aquí eso ya no sirve: el RPC público de NEAR solo conserva ~36 horas de
histórico, mientras que el estado del contrato persiste. Se audita el código,
no la transacción.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import require_api_key
from app.services.near import NearError, verify_anchor

router = APIRouter()


class VerifyRequest(BaseModel):
    codigo: str = Field(min_length=1, max_length=16)
    hash_hex: str = Field(min_length=1, max_length=64)


@router.post("/api/verify", dependencies=[Depends(require_api_key)])
def verify(req: VerifyRequest):
    try:
        return verify_anchor(req.codigo, req.hash_hex)
    except NearError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
