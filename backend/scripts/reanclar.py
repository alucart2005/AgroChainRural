"""Re-ancla en NEAR los lotes que quedaron sin anclar.

    python -m scripts.reanclar              # solo los pendientes
    python -m scripts.reanclar --listar     # sin escribir en la cadena

Un lote queda pendiente cuando el RPC de NEAR no confirmó en el momento del
registro (o cuando llegó de una base anterior a la migración). El endpoint
`POST /api/lotes/{codigo}/anclar` hace lo mismo para UN lote; este script es
para el piloto completo.

El ancla usa el ``hash_sha256`` YA GUARDADO: no se recalcula nada, el payload
canónico no cambió con la migración. Solo se recalcula para avisar si la fila
de la base divergió de su propia huella (se ancla igual: la verificación HU-03
compara contra los datos actuales, así que una alteración se detectaría igual).
"""

from __future__ import annotations

import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.models.lote import Lote
from app.services.near import NearError, anchor_hash
from app.services.sha256 import hash_lote


def main() -> int:
    solo_listar = "--listar" in sys.argv

    with SessionLocal() as db:
        pendientes = db.scalars(
            select(Lote)
            .where(Lote.near_tx_hash.is_(None))
            .order_by(Lote.codigo)
        ).all()

        if not pendientes:
            print("Todos los lotes ya están anclados en NEAR.")
            return 0

        print(f"{len(pendientes)} lote(s) sin anclar en NEAR\n")
        if solo_listar:
            for lote in pendientes:
                print(f"  {lote.codigo}  {lote.hash_sha256}")
            print("\nEjecuta sin --listar para anclarlos.")
            return 0

        anclados = 0
        for lote in pendientes:
            recalculado = hash_lote(lote.como_dict())
            if recalculado != lote.hash_sha256:
                print(
                    f"  {lote.codigo}: AVISO la fila diverge de su huella "
                    f"(guardada {lote.hash_sha256[:12]}…, "
                    f"recalculada {recalculado[:12]}…)"
                )

            try:
                resultado = anchor_hash(lote.codigo, lote.hash_sha256)
            except NearError as exc:
                print(f"  {lote.codigo}: FALLÓ — {exc}")
                continue

            lote.near_tx_hash = resultado.get("tx_hash")
            lote.near_block = resultado.get("block")
            anclados += 1
            print(
                f"  {lote.codigo}: anclado "
                f"tx={lote.near_tx_hash} bloque={lote.near_block}"
            )

        db.commit()
        print(f"\n{anclados}/{len(pendientes)} anclados.")
        return 0 if anclados == len(pendientes) else 1


if __name__ == "__main__":
    sys.exit(main())
