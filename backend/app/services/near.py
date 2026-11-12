"""Anclaje en NEAR Testnet: guarda la huella SHA-256 en un contrato KV.

Solo viaja el hash en **hex de 64 caracteres**; fotos y evidencias siguen
fuera de la cadena (en R2), igual que con Stellar.

La gran diferencia con Stellar: allí el hash viajaba en el *memo* de una
transacción y había que buscar la transacción para leerlo. Aquí el hash vive en
el **estado del contrato**, así que la verificación usa ``view get`` y no
depende del histórico de transacciones, que el RPC público solo conserva
~36 horas.
"""

from __future__ import annotations

import logging
import time

from near import Near

from app.core.config import settings

log = logging.getLogger(__name__)

# near-kit ya reintenta internamente los nonces; estos intentos cubren fallos
# transitorios del RPC (nodo saturado, timeout, bloque obsoleto).
INTENTOS = 3
ESPERA_SEGUNDOS = 1.0

_HEX = frozenset("0123456789abcdefABCDEF")
LEN_HASH = 64  # SHA-256 en hex


class NearError(Exception):
    """Fallo de infraestructura NEAR (nunca debe escapar como 500)."""


def get_client() -> Near:
    """Cliente near-kit con la configuración de ``.env``.

    ``view`` no necesita firmante, así que con las claves vacías la lectura
    sigue funcionando; escribir sin ``NEAR_PRIVATE_KEY`` falla al firmar.
    """
    kwargs: dict = {
        "network": settings.near_network,
        "rpc_url": settings.near_rpc_url or None,
    }
    if settings.near_account_id and settings.near_private_key:
        kwargs["account_id"] = settings.near_account_id
        kwargs["private_key"] = settings.near_private_key
    try:
        return Near(**kwargs)
    except Exception as exc:
        raise NearError(f"No se pudo crear el cliente NEAR: {exc}") from exc


def _validar(codigo: str, hash_hex: str) -> None:
    if not codigo:
        raise NearError("El código del lote no puede estar vacío")
    if len(hash_hex) != LEN_HASH or any(c not in _HEX for c in hash_hex):
        raise NearError(
            f"El hash debe ser {LEN_HASH} caracteres hex (SHA-256)"
        )


def _contrato() -> str:
    if not settings.near_contract_id:
        raise NearError("NEAR_CONTRACT_ID no configurada")
    return settings.near_contract_id


def _bloque_de(client: Near, tx_hash: str | None) -> int | None:
    """Altura del bloque que incluyó la transacción.

    Es un dato presentacional: si no se puede resolver, el ancla sigue siendo
    válido y se devuelve ``None`` en lugar de fallar.
    """
    if not tx_hash:
        return None
    try:
        crudo = client.rpc(
            "tx",
            {"tx_hash": tx_hash, "sender_account_id": settings.near_account_id},
        )
        hash_bloque = (crudo.get("transaction_outcome") or {}).get("block_hash")
        if not hash_bloque:
            return None
        bloque = client.rpc("block", {"block_id": hash_bloque})
        return int((bloque.get("header") or {}).get("height"))
    except Exception as exc:
        log.debug("No se pudo resolver el bloque de %s: %s", tx_hash, exc)
        return None


def anchor_hash(codigo: str, hash_hex: str) -> dict:
    """Ancla el hash de un lote con ``set(codigo, hash)`` en el contrato.

    Idempotente en la cadena: repetir el mismo hash no hace nada y un hash
    distinto para el mismo código revienta (el dato fue alterado), así que un
    reintento nunca corrompe nada.

    Devuelve ``tx_hash``, ``block`` y ``successful``.
    """
    _validar(codigo, hash_hex)
    contrato = _contrato()
    if not settings.near_account_id or not settings.near_private_key:
        raise NearError("NEAR_ACCOUNT_ID / NEAR_PRIVATE_KEY no configuradas")

    client = get_client()
    ultimo: Exception | None = None

    for intento in range(INTENTOS):
        try:
            tx = client.call(
                contrato, "set", {"codigo": codigo, "hash": hash_hex}
            )
        except Exception as exc:
            ultimo = exc
            log.warning(
                "Anclaje NEAR falló (intento %s/%s) para %s: %s",
                intento + 1,
                INTENTOS,
                codigo,
                exc,
            )
            if intento < INTENTOS - 1:
                time.sleep(ESPERA_SEGUNDOS)
            continue

        estado = tx.final_execution_status or ""
        if estado == "FAILURE":
            # Panic del contrato (p. ej. un hash distinto para el mismo
            # código): reintentar no lo arregla.
            raise NearError(f"El contrato rechazó la transacción: {tx.status}")
        if estado in ("", "NONE"):
            ultimo = RuntimeError(f"transacción sin ejecutar (estado {estado!r})")
            if intento < INTENTOS - 1:
                time.sleep(ESPERA_SEGUNDOS)
            continue

        return {
            "tx_hash": tx.transaction_hash,
            "block": _bloque_de(client, tx.transaction_hash),
            "successful": True,
        }

    raise NearError(f"No se pudo anclar tras {INTENTOS} intentos: {ultimo}")


def get_hash(codigo: str) -> str | None:
    """Hash anclado para un código, leyendo el **estado** del contrato.

    Devuelve ``None`` si el lote aún no está anclado.
    """
    contrato = _contrato()
    client = get_client()
    try:
        resultado = client.view(contrato, "get", {"codigo": codigo})
    except Exception as exc:
        # Capturado como NearError para responder 400/502 en vez de un 500
        # sin diagnóstico cuando el RPC está caído.
        raise NearError(f"NEAR no respondió: {exc}") from exc
    if resultado is None:
        return None
    return str(resultado)


def verify_anchor(codigo: str, hash_hex: str) -> dict:
    """Compara el hash on-chain con el esperado (HU-03).

    Consulta el estado del contrato, no la transacción: el detalle de las
    transacciones caduca en el RPC público, el estado no.

    El llamador debe contrastar además ``hash_calculado == hash_hex`` para
    cerrar la triangulación navegador → base de datos → cadena.
    """
    _validar(codigo, hash_hex)
    registrado = get_hash(codigo)
    return {
        "verified": registrado is not None
        and registrado.lower() == hash_hex.lower(),
        "hash_registrado": registrado,
    }
