# `contract/` — contrato KV de AgroChain Rural

Ancla la huella SHA-256 de cada lote de huevos en **NEAR Testnet**, como un
mapa `codigo → hash`. Reemplaza al anclaje por Memo Hash en Stellar Testnet.

## Por qué un contrato KV (y no solo argumentos de transacción)

El RPC público de NEAR solo conserva el detalle de las transacciones durante
~36 horas. Si la verificación dependiera de buscar la transacción, un lote
anclado la semana pasada quedaría inverificable. Guardando el hash **en el
estado del contrato**, `view get` lo devuelve siempre, sin importar cuánto
haya pasado.

## API

| Método | Firma | Descripción |
|---|---|---|
| `set` | `set(codigo: String, hash: String)` | Ancla el hash. **No es pagable.** |
| `get` | `get(codigo: String) → Option<String>` | Devuelve el hash hex o `None`. |

`set` es **idempotente**:

- lote nuevo → se guarda;
- mismo código con el mismo hash → no-op (los reintentos son seguros);
- mismo código con otro hash → **panic**: el dato fue alterado.

Además valida que `hash` tenga 64 caracteres y que `codigo` no esté vacío.

## Por qué hex y no `[u8; 32]`

El contrato devuelve **exactamente el string** que el backend ya compara en
`app/services/sha256.py`. No hay codificación intermedia que pueda divergir,
y la paridad de hash front↔back (HU-03) queda intacta.

`set` **no es pagable**: el *storage staking* (~100 bytes por lote ≈ 0.001
NEAR) lo cubre el saldo de la cuenta del contrato, que se fondea una vez.

## Construir y testear

Requiere `rustup` con el target `wasm32-unknown-unknown`:

```bash
rustup target add wasm32-unknown-unknown
```

```bash
cd contract
cargo test --release                                  # tests unitarios (sin red)
cargo build --release --target wasm32-unknown-unknown # → target/.../agrotrace_kv.wasm
```

Los tests usan `near_sdk::test_utils::test_env::setup_free()` (feature
`unit-testing` en `[dev-dependencies]`); no abren red ni necesitan sandbox de
Docker.

El wasm compilado se versiona en **`res/agrotrace_kv.wasm`** — es el artefacto
que se despliega, para que el deploy no dependa de la toolchain de quien
clona.

## Despliegue

Lo hace `python -m scripts.desplegar_contrato` (ver ese script). En corto:

```python
from near import Near, deploy_contract, function_call

client = Near(network="testnet", account_id=..., private_key=...)
client.send_transaction(cuenta_contrato, actions=[
    deploy_contract(wasm_bytes),
])
```

## Estructura

```
contract/
├── Cargo.toml          # near-sdk 5.30.1, edition 2024, crate-type cdylib
├── Cargo.lock          # versionado (dependencias exactas)
├── src/lib.rs          # el contrato + 7 tests unitarios
└── res/
    └── agrotrace_kv.wasm   # artefacto desplegable, versionado
```

`target/` está en `.gitignore`.
