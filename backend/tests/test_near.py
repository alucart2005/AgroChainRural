"""Pruebas del servicio de anclaje en NEAR (sin red, cliente simulado).

Es el espejo de la antigua `test_stellar.py`: se mockea `get_client`, nunca se
abre una conexión real al RPC de testnet.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.services.near import (
    NearError,
    anchor_hash,
    get_hash,
    verify_anchor,
)

CODIGO = "HUE-2027-001"
HASH = "1" * 64
CONTRATO = "agrochain-rural.testnet"
CUENTA = "productor.testnet"


@pytest.fixture()
def config_near(monkeypatch):
    """Claves de prueba: sin esto `_contrato()` ni `anchor_hash` levantan error."""
    monkeypatch.setattr(settings, "near_contract_id", CONTRATO)
    monkeypatch.setattr(settings, "near_account_id", CUENTA)
    monkeypatch.setattr(settings, "near_private_key", "ed25519:clave-de-prueba")
    # Los reintentos no deben dormir el suite de tests.
    monkeypatch.setattr("app.services.near.ESPERA_SEGUNDOS", 0.0)


def _tx(estado: str = "FINAL", tx_hash: str = "TxHashDePrueba123"):
    tx = MagicMock()
    tx.final_execution_status = estado
    tx.transaction_hash = tx_hash
    tx.status = {"SuccessValue": ""}
    return tx


def _rpc(method: str, params: dict):
    """Responde `tx` (bloque de la transacción) y `block` (altura)."""
    if method == "tx":
        assert params["tx_hash"]
        assert params["sender_account_id"] == CUENTA
        return {"transaction_outcome": {"block_hash": "BloqueHash"}}
    if method == "block":
        assert params["block_id"] == "BloqueHash"
        return {"header": {"height": 4242}}
    raise AssertionError(f"RPC inesperado: {method}")


def _cliente(tx=None, view=None) -> MagicMock:
    cliente = MagicMock()
    if tx is not None:
        cliente.call.return_value = tx
    cliente.view.return_value = view
    cliente.rpc.side_effect = _rpc
    return cliente


# --- anchor_hash -------------------------------------------------------------

def test_anchor_devuelve_tx_hash_y_bloque(config_near):
    cliente = _cliente(tx=_tx())
    with patch("app.services.near.get_client", return_value=cliente):
        resultado = anchor_hash(CODIGO, HASH)

    assert resultado == {
        "tx_hash": "TxHashDePrueba123",
        "block": 4242,
        "successful": True,
    }
    cliente.call.assert_called_once_with(
        CONTRATO, "set", {"codigo": CODIGO, "hash": HASH}
    )


def test_anchor_sin_clave_no_configurada_no_toca_la_red(config_near, monkeypatch):
    monkeypatch.setattr(settings, "near_private_key", "")
    cliente = _cliente()
    with patch("app.services.near.get_client", return_value=cliente):
        with pytest.raises(NearError, match="NEAR_ACCOUNT_ID"):
            anchor_hash(CODIGO, HASH)
    cliente.call.assert_not_called()


def test_anchor_sin_contrato_no_toca_la_red(config_near, monkeypatch):
    monkeypatch.setattr(settings, "near_contract_id", "")
    cliente = _cliente()
    with patch("app.services.near.get_client", return_value=cliente):
        with pytest.raises(NearError, match="NEAR_CONTRACT_ID"):
            anchor_hash(CODIGO, HASH)
    cliente.call.assert_not_called()


@pytest.mark.parametrize(
    "codigo,hash_hex,motivo",
    [
        ("", HASH, "vacío"),
        (CODIGO, "abc", "64 caracteres"),
        (CODIGO, "z" * 64, "64 caracteres"),
        (CODIGO, HASH[:63], "64 caracteres"),
    ],
)
def test_anchor_rechaza_entradas_invalidas(config_near, codigo, hash_hex, motivo):
    with pytest.raises(NearError, match=motivo):
        anchor_hash(codigo, hash_hex)


def test_anchor_reintenta_antefallo_transitorio(config_near):
    cliente = _cliente()
    cliente.call.side_effect = [RuntimeError("timeout"), _tx()]
    with patch("app.services.near.get_client", return_value=cliente):
        resultado = anchor_hash(CODIGO, HASH)

    assert resultado["tx_hash"] == "TxHashDePrueba123"
    assert cliente.call.call_count == 2


def test_anchor_agota_los_reintentos(config_near):
    cliente = _cliente()
    cliente.call.side_effect = RuntimeError("RPC caído")
    with patch("app.services.near.get_client", return_value=cliente):
        with pytest.raises(NearError, match="tras 3 intentos"):
            anchor_hash(CODIGO, HASH)
    assert cliente.call.call_count == 3


def test_anchor_no_reintenta_si_el_contrato_rechaza(config_near):
    """Un panic (hash distinto para el mismo código) no se arregla repitiendo."""
    cliente = _cliente(tx=_tx(estado="FAILURE"))
    cliente.call.return_value.status = {"Failure": "hash distinto"}
    with patch("app.services.near.get_client", return_value=cliente):
        with pytest.raises(NearError, match="rechazó"):
            anchor_hash(CODIGO, HASH)
    assert cliente.call.call_count == 1


def test_anchor_sin_bloque_no_falla(config_near):
    """El bloque es cosmético: si no se resuelve, el ancla sigue valiendo."""
    cliente = _cliente(tx=_tx())
    cliente.rpc.side_effect = RuntimeError("bloque no disponible")
    with patch("app.services.near.get_client", return_value=cliente):
        resultado = anchor_hash(CODIGO, HASH)

    assert resultado["tx_hash"] == "TxHashDePrueba123"
    assert resultado["block"] is None


# --- get_hash / verify_anchor ------------------------------------------------

def test_get_hash_devuelve_el_valor_del_contrato(config_near):
    cliente = _cliente(view=HASH)
    with patch("app.services.near.get_client", return_value=cliente):
        assert get_hash(CODIGO) == HASH
    cliente.view.assert_called_once_with(CONTRATO, "get", {"codigo": CODIGO})


def test_get_hash_devuelve_none_si_no_esta_anclado(config_near):
    cliente = _cliente(view=None)
    with patch("app.services.near.get_client", return_value=cliente):
        assert get_hash(CODIGO) is None


def test_get_hash_convierte_el_error_de_rpc_en_near_error(config_near):
    cliente = _cliente()
    cliente.view.side_effect = RuntimeError("node doesn't exist")
    with patch("app.services.near.get_client", return_value=cliente):
        with pytest.raises(NearError, match="NEAR no respondió"):
            get_hash(CODIGO)


def test_verify_confirma_cuando_el_contrato_coincide(config_near):
    cliente = _cliente(view=HASH)
    with patch("app.services.near.get_client", return_value=cliente):
        resultado = verify_anchor(CODIGO, HASH)

    assert resultado == {"verified": True, "hash_registrado": HASH}


def test_verify_detecta_hash_distinto(config_near):
    cliente = _cliente(view="2" * 64)
    with patch("app.services.near.get_client", return_value=cliente):
        resultado = verify_anchor(CODIGO, HASH)

    assert resultado["verified"] is False
    assert resultado["hash_registrado"] == "2" * 64


def test_verify_sin_ancla_devuelve_false(config_near):
    cliente = _cliente(view=None)
    with patch("app.services.near.get_client", return_value=cliente):
        resultado = verify_anchor(CODIGO, HASH)

    assert resultado["verified"] is False
    assert resultado["hash_registrado"] is None


def test_verify_rechaza_hash_invalido_sin_tocar_la_red(config_near):
    cliente = _cliente()
    with patch("app.services.near.get_client", return_value=cliente):
        with pytest.raises(NearError, match="64 caracteres"):
            verify_anchor(CODIGO, "no-es-hex")
    cliente.view.assert_not_called()


def test_verify_es_case_insensitive(config_near):
    """El contrato guarda minúsculas; un hash en mayúsculas sigue coincidiendo."""
    cliente = _cliente(view=HASH)
    with patch("app.services.near.get_client", return_value=cliente):
        assert verify_anchor(CODIGO, HASH.upper())["verified"] is True
