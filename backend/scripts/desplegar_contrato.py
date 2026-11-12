"""Despliega `contract/res/agrotrace_kv.wasm` en la cuenta de NEAR configurada.

    python -m scripts.desplegar_contrato

Requiere `NEAR_ACCOUNT_ID` y `NEAR_PRIVATE_KEY` en `backend/.env`, y que la
cuenta exista en testnet (créala antes con
`python -m scripts.near_account create <cuenta.testnet>`).

Al terminar verifica el despliegue leyendo el estado del contrato con `view get`.
"""

from __future__ import annotations

import pathlib
import sys

from app.core.config import settings

WASM = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "contract"
    / "res"
    / "agrotrace_kv.wasm"
)
CODIGO_PRUEBA = "HUE-1999-000"


def main() -> int:
    from near import deploy_contract

    from app.services.near import NearError, get_client

    if not WASM.exists():
        print(f"No existe {WASM}")
        print("Compila antes: cd contract && cargo build --release "
              "--target wasm32-unknown-unknown")
        return 1
    if not settings.near_account_id or not settings.near_private_key:
        print("NEAR_ACCOUNT_ID / NEAR_PRIVATE_KEY no configuradas en .env")
        return 1
    if not settings.near_contract_id:
        print("NEAR_CONTRACT_ID no configurada en .env")
        return 1

    wasm = WASM.read_bytes()
    print(f"WASM    : {WASM.name} ({len(wasm)} bytes)")
    print(f"Cuenta  : {settings.near_account_id}")
    print(f"Contrato: {settings.near_contract_id}")

    client = get_client()

    try:
        if not client.account_exists(settings.near_account_id):
            print(
                "La cuenta no existe en testnet. Créala primero con:\n"
                "  python -m scripts.near_account create "
                f"{settings.near_account_id}"
            )
            return 1
        balance = client.balance(settings.near_account_id)
        print(f"Balance : {balance}")

        tx = client.send_transaction(
            settings.near_account_id, actions=[deploy_contract(wasm)]
        )
    except Exception as exc:
        print(f"Error al desplegar: {exc}")
        return 1

    estado = tx.final_execution_status or ""
    print(f"Estado  : {estado} (tx {tx.transaction_hash})")
    if estado == "FAILURE":
        print(f"Detalle : {tx.status}")
        return 1

    # Prueba de humo: el contrato debe responder `get` sin explotar.
    try:
        respuesta = client.view(
            settings.near_contract_id, "get", {"codigo": CODIGO_PRUEBA}
        )
    except Exception as exc:
        print(f"El contrato no responde a `view get`: {exc}")
        return 1

    print(f"view get → {respuesta!r} (None es correcto: aún no hay anclas)")
    print("Despliegue correcto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
