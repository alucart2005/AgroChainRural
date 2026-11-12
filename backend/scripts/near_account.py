"""Crear e inspeccionar cuentas de NEAR Testnet.

    python -m scripts.near_account create [cuenta.testnet]
    python -m scripts.near_account show

`create` genera una clave ed25519 con `near-kit` y la fondea con el faucet
oficial de testnet (10 NEAR). Imprime las dos líneas para pegarlas en
`backend/.env`; la clave secreta jamás se guarda en el repositorio.

El nombre por defecto sale de `NEAR_ACCOUNT_ID` si ya está configurada; si no,
se pide como argumento.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

from app.core.config import settings

FAUCET = "https://helper.nearprotocol.com/account"
FAUCET_NEAR = "10"  # lo que reparte el faucet de testnet


def _fondear(cuenta: str, clave_publica: str) -> dict:
    """Crea la cuenta en testnet con el faucet oficial."""
    peticion = urllib.request.Request(
        FAUCET,
        data=json.dumps(
            {"newAccountId": cuenta, "newAccountPublicKey": clave_publica}
        ).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=30) as respuesta:
            return json.load(respuesta)
    except urllib.error.HTTPError as exc:
        cuerpo = exc.read().decode(errors="replace")[:300]
        raise SystemExit(f"Faucet respondió {exc.code}: {cuerpo}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"No se pudo contactar el faucet: {exc}") from exc


def create(cuenta: str) -> int:
    from near import generate_key

    if not cuenta:
        print(
            "Indica la cuenta: python -m scripts.near_account create "
            "agrochain-rural.testnet"
        )
        return 1

    clave = generate_key()
    publica = str(clave.public_key)

    print(f"Creando {cuenta} con el faucet de testnet ...")
    resultado = _fondear(cuenta, publica)
    estado = resultado.get("final_execution_status")
    print(f"Faucet: {estado}")

    if estado == "FAILURE":
        # La causa típica es que la cuenta ya existía.
        print(json.dumps(resultado.get("status"), ensure_ascii=False)[:400])
        return 1

    print()
    print("Pega estas dos líneas en backend/.env (no las subas al repositorio):")
    print(f"NEAR_ACCOUNT_ID={cuenta}")
    print(f"NEAR_PRIVATE_KEY={clave.secret_key}")
    return 0


def show() -> int:
    from app.services.near import get_client

    cuenta = settings.near_account_id
    if not cuenta:
        print("NEAR_ACCOUNT_ID no está configurada en backend/.env")
        return 1

    try:
        client = get_client()
        balance = client.balance(cuenta)
        vista = client.account(cuenta)
        claves = client.access_keys(cuenta)
    except Exception as exc:
        print(f"NEAR no respondió: {exc}")
        return 1

    print(f"Cuenta   : {cuenta}")
    print(f"Balance  : {balance}")
    print(f"Uso      : {vista.storage_usage} bytes de storage")
    print(f"Contrato : {'sí (código desplegado)' if vista.code_hash not in ('1' * 32, '') else 'no'}")
    print(f"Claves   : {len(claves)}")
    for info in claves:
        print(f"  - {info.public_key} ({info.access_key.permission})")
    return 0


if __name__ == "__main__":
    comando = sys.argv[1] if len(sys.argv) > 1 else "show"
    if comando == "create":
        argumento = sys.argv[2] if len(sys.argv) > 2 else ""
        raise SystemExit(create(argumento))
    if comando == "show":
        raise SystemExit(show())
    print("Uso: python -m scripts.near_account [create <cuenta.testnet> | show]")
    sys.exit(1)
