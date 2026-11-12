"""Demostración end-to-end: hash → ancla en NEAR Testnet → verificación.

Sirve de prueba de humo del flujo completo sin pasar por la API:

    python -m scripts.anchor_demo

Ancla UN hash real en el contrato KV (una transacción real en testnet) y luego
lee el estado del contrato con `view get` para comprobar que devuelve la misma
huella. Requiere `NEAR_ACCOUNT_ID`, `NEAR_PRIVATE_KEY` y `NEAR_CONTRACT_ID`.
"""

from app.services.near import NearError, anchor_hash, verify_anchor
from app.services.sha256 import hash_lote


def main():
    datos = {
        "codigo": "HUE-2027-001",
        "fecha_cosecha": "2027-03-14",
        # Decisión de producto: ``fecha_postura`` queda FUERA del hash.
        "fecha_postura": "2027-03-13",
        "linea_productiva": "Huevos Guarumo",
        "cantidad": 10,
        "unidad": "cubetas",
        "finca": "Finca Guarumo",
        "municipio": "Cáceres, Antioquia",
        # Solo entran nombre y tamaño: las URLs de R2 pueden cambiar y
        # romperían la verificación.
        "evidencias": [
            {"nombre": "galpon-huevos.jpg", "tamano": 2481930},
            {"nombre": "cubetas-empaque.jpg", "tamano": 512000},
        ],
    }

    # ``hash_lote`` recibe UN dict e ignora los campos que no forman parte del
    # payload canónico (fecha_postura, hashes, urls...).
    h = hash_lote(datos)
    print(f"Lote    : {datos['codigo']}")
    print(f"SHA-256 : {h}")

    try:
        resultado = anchor_hash(datos["codigo"], h)
    except NearError as exc:
        print(f"Error al anclar: {exc}")
        return 1

    print(f"Anclado : tx={resultado['tx_hash']} bloque={resultado['block']}")

    try:
        verificacion = verify_anchor(datos["codigo"], h)
    except NearError as exc:
        print(f"Error al verificar: {exc}")
        return 1

    if verificacion["verified"]:
        print("Verificación on-chain: VERIFICADO")
        print(f"  contrato : {verificacion['hash_registrado']}")
        return 0

    print(f"Verificación on-chain: NO VERIFICADO → {verificacion}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
