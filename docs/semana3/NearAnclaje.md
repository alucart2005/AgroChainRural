# ⚓ Anclaje en NEAR: diseño y servicio

> **Proyecto:** AgroChain Rural · **Módulo:** Anclaje de huellas SHA-256 en un contrato KV de NEAR Testnet · **Código:** `backend/app/services/near.py` + `contract/`
>
> 🌐 **Historia:** hasta la versión 0.05 el ancla era un *Memo Hash* de Stellar; la migración completa se documenta en [`docs/migracion-near.md`](../migracion-near.md).

> 🌐 **Idioma / Language:** [🇪🇸 Español](#-español) · [🇺🇸 English](#-english) · [🇧🇷 Português](#-português)

---

## 🇪🇸 Español

📑 **Contenido:** [🔗 1. Diseño](#-1-diseño-del-anclaje) · [🔄 2. Flujo](#-2-flujo-de-anclaje) · [🔑 3. Cuenta y contrato](#-3-cuenta-y-contrato-en-testnet) · [🧩 4. Servicio](#-4-servicio-nearpy) · [🛠️ 5. Scripts](#-5-scripts-cli) · [🔐 6. Variables](#-6-variables-de-entorno) · [✅ 7. Verificación](#-7-verificación-on-chain) · [🧪 8. Tests](#-8-tests)

---

### 🔗 1. Diseño del anclaje

La huella SHA-256 de cada lote se guarda como **entrada de un contrato KV propio** en **NEAR Testnet**: un mapa `codigo → hash` donde el hash viaja como **cadena hexadecimal de 64 caracteres** — exactamente la misma que compara el backend, sin decodificaciones.

| Opción | Qué es | Estado |
| :--- | :--- | :--- |
| **A** | Contrato KV propio (`set`/`get` sobre el estado) | ✅ **Elegida** (v0.06) |
| **B** | Solo argumentos de la transacción, sin contrato | Descartada |

*Por qué la Opción A:* el RPC público de NEAR solo conserva el **detalle** de las transacciones ~36 horas; una verificación que dependiera de leer la transacción moriría con el archivo. El **estado del contrato no caduca**: `view get` responde hoy igual que dentro de un año. Además el contrato fija la regla de negocio del ancla: idempotencia y rechazo de hash distinto.

| Componente | Decisión |
| :--- | :--- |
| Red | NEAR **Testnet** (`testnet`) |
| Contrato | Cuenta propia (p. ej. `agrochainrural.testnet`), Rust + near-sdk 5.30 |
| Entrada on-chain | `get(codigo)` → hash hex de 64 caracteres (o `null`) |
| Método de escritura | `set(codigo, hash)` — no payable, idempotente, rechaza un hash distinto |
| Firmante | Cuenta de la Finca Guarumo (`NEAR_PRIVATE_KEY`) |
| Regla de oro | **Fotos/videos nunca van en blockchain** — solo el hash |

**Propiedades del `set` (críticas):**

- **Idempotente:** reintentar el ancla con el mismo hash es un *no-op* (los reintentos del backend son seguros).
- **Estricto:** anclar un hash *distinto* para un código ya anclado hace panic — un lote no puede cambiar de huella.
- **No payable:** el contrato no acepta NEAR; el *storage staking* lo cubre el saldo de la propia cuenta del contrato.

---

### 🔄 2. Flujo de anclaje

1. El backend calcula el hash del lote: `hash_lote(datos_lote)` (JSON canónico de 8 campos → SHA-256).
2. `anchor_hash(codigo, hash_hex)` valida el formato y llama al contrato con `near-kit` (`client.call("set", ...)`).
3. Ante fallos transitorios del RPC reintenta (máx. 3); un **panic del contrato no se reintenta** (no hay nada que arreglar).
4. Se guardan en la base de datos `near_tx_hash` y `near_block` (la altura de bloque es cosmética: si no se resuelve, se guarda `None` y el ancla sigue siendo válida).
5. El consumidor verifica con `verify_anchor(codigo, hash_hex)`, que lee el **estado** del contrato (`view get`).

---

### 🔑 3. Cuenta y contrato en Testnet

```bash
cd backend
python -m scripts.near_account create <cuenta.testnet>  # crea la cuenta (faucet oficial, 10 NEAR) e imprime las claves
python -m scripts.near_account show <cuenta.testnet>    # muestra el saldo
python -m scripts.desplegar_contrato                    # despliega contract/res/agrochain_kv.wasm en NEAR_CONTRACT_ID
```

`create` imprime `NEAR_ACCOUNT_ID` y `NEAR_PRIVATE_KEY` (`ed25519:...`) para guardarlas en `backend/.env` (nunca subirlas al repositorio). El faucet fondea la cuenta una sola vez; ese saldo paga el *gas* de los anclajes y el *storage staking* del contrato.

---

### 🧩 4. Servicio `near.py`

| Función | Responsabilidad |
| :--- | :--- |
| `get_client()` | Cliente `near-kit` (`NEAR_NETWORK`, `NEAR_RPC_URL`, cuenta y clave) |
| `_validar()` | Comprueba formato de código y hash (64 hex) antes de tocar la red |
| `_contrato()` | Resuelve la cuenta del contrato (`NEAR_CONTRACT_ID`) |
| `_bloque_de()` | Altura del bloque de la transacción (2 llamadas RPC crudas; a fallo suave → `None`) |
| `anchor_hash()` | Llama a `set` con reintentos; devuelve `{successful, tx_hash, block}` |
| `get_hash()` | Hash anclado para un código, leyendo el **estado** con `view get` |
| `verify_anchor()` | Compara el hash on-chain con el esperado → `{verified, hash_registrado}` |

Error propio: `NearError` (hash inválido, RPC caído, contrato ausente...). Nunca escapa como 500.

---

### 🛠️ 5. Scripts CLI

```bash
cd backend
python -m scripts.anchor_demo        # HUE-2027-001: hash → ancla → verifica (Testnet real)
python -m scripts.reanclar --listar  # lotes con near_tx_hash = NULL, sin escribir en la cadena
python -m scripts.reanclar           # re-ancla los lotes pendientes (idempotente)
```

Salida esperada de `anchor_demo`:

```text
Lote    : HUE-2027-001
SHA-256 : 77304c85...
Anclado : tx=EEFcqP... bloque=277310783
Verificación on-chain: VERIFICADO
```

---

### 🔐 6. Variables de entorno

```bash
NEAR_NETWORK=testnet
NEAR_RPC_URL=https://test.rpc.fastnear.com
NEAR_ACCOUNT_ID=agrochainrural.testnet
NEAR_PRIVATE_KEY=ed25519:...
NEAR_CONTRACT_ID=agrochainrural.testnet
```

---

### ✅ 7. Verificación on-chain

`POST /api/verify` con `{"codigo", "hash_hex"}`
(protegido con `X-API-Key`: sin ella sería un proxy abierto y gratuito a la red) devuelve:

```json
{"verified": true, "hash_registrado": "242301d4...20da92"}
```

La ruta del consumidor es `GET /api/verify/{codigo}`, que cierra la **triangulación**: hash recalculado en el servidor ↔ hash guardado en la base ↔ hash devuelto por el contrato. Cualquier alteración posterior de los datos del lote rompe la coincidencia.

> El explorador de la transacción es `https://explorer.testnet.near.org/transactions/<tx_hash>` (la ficha del lote enlaza directo). El bloque (`near_block`) es informativo; la verificación no depende de él.

---

### 🧪 8. Tests

```bash
cd backend
python -m pytest tests/ -v     # 84 tests, todos sin red
```

- `test_sha256.py`: determinismo, orden independiente de claves, sensibilidad a cambios.
- `test_near.py`: validación de hash, anclaje con el cliente NEAR simulado, idempotencia, verificación (ok / hash distinto / código sin ancla / RPC caído).

[⬆ Volver al inicio](#-anclaje-en-near-diseño-y-servicio)

---

## 🇺🇸 English

📑 **Contents:** [🔗 1. Design](#-1-anchoring-design) · [🔄 2. Flow](#-2-anchoring-flow) · [🔑 3. Account & contract](#-3-account-and-contract-on-testnet) · [🧩 4. Service](#-4-nearpy-service) · [🛠️ 5. Scripts](#-5-cli-scripts) · [🔐 6. Env vars](#-6-environment-variables) · [✅ 7. Verification](#-7-on-chain-verification) · [🧪 8. Tests](#-8-tests)

---

### 🔗 1. Anchoring design

Each batch's SHA-256 fingerprint is stored as **an entry of an own KV contract** on **NEAR Testnet**: a `codigo → hash` map where the hash travels as a **64-character hex string** — exactly the one the backend compares, with no decoding.

| Option | What it is | Status |
| :--- | :--- | :--- |
| **A** | Own KV contract (`set`/`get` over state) | ✅ **Chosen** (v0.06) |
| **B** | Only transaction arguments, no contract | Discarded |

*Why Option A:* NEAR's public RPC keeps transaction **detail** for only ~36 hours; a verification that depended on reading the transaction would die with the archive. **Contract state does not expire**: `view get` answers today the same as in a year. The contract also pins the anchor's business rule: idempotency and rejection of a different hash.

| Component | Decision |
| :--- | :--- |
| Network | NEAR **Testnet** (`testnet`) |
| Contract | Own account (e.g. `agrochainrural.testnet`), Rust + near-sdk 5.30 |
| On-chain entry | `get(codigo)` → 64-char hex hash (or `null`) |
| Write method | `set(codigo, hash)` — not payable, idempotent, rejects a different hash |
| Signer | Finca Guarumo account (`NEAR_PRIVATE_KEY`) |
| Golden rule | **Photos/videos never go on blockchain** — only the hash |

**`set` properties (critical):**

- **Idempotent:** retrying the anchor with the same hash is a *no-op* (backend retries are safe).
- **Strict:** anchoring a *different* hash for an already-anchored code panics — a batch cannot change its fingerprint.
- **Not payable:** the contract accepts no NEAR; storage staking is covered by the contract account's own balance.

---

### 🔄 2. Anchoring flow

1. The backend computes the batch hash: `hash_lote(batch_data)` (canonical JSON of 8 fields → SHA-256).
2. `anchor_hash(codigo, hash_hex)` validates the format and calls the contract via `near-kit` (`client.call("set", ...)`).
3. On transient RPC failures it retries (max 3); a **contract panic is not retried** (nothing to fix).
4. `near_tx_hash` and `near_block` are stored (block height is cosmetic: if unresolved, `None` is saved and the anchor stays valid).
5. The consumer verifies with `verify_anchor(codigo, hash_hex)`, which reads contract **state** (`view get`).

---

### 🔑 3. Account and contract on Testnet

```bash
cd backend
python -m scripts.near_account create <account.testnet>  # creates the account (official faucet, 10 NEAR) and prints the keys
python -m scripts.near_account show <account.testnet>    # shows the balance
python -m scripts.desplegar_contrato                     # deploys contract/res/agrochain_kv.wasm to NEAR_CONTRACT_ID
```

`create` prints `NEAR_ACCOUNT_ID` and `NEAR_PRIVATE_KEY` (`ed25519:...`) to store in `backend/.env` (never commit them). The faucet funds the account once; that balance pays anchor *gas* and the contract's *storage staking*.

---

### 🧩 4. `near.py` service

| Function | Responsibility |
| :--- | :--- |
| `get_client()` | `near-kit` client (`NEAR_NETWORK`, `NEAR_RPC_URL`, account and key) |
| `_validar()` | Checks code and hash format (64 hex) before touching the network |
| `_contrato()` | Resolves the contract account (`NEAR_CONTRACT_ID`) |
| `_bloque_de()` | Block height of the transaction (2 raw RPC calls; soft-fails to `None`) |
| `anchor_hash()` | Calls `set` with retries; returns `{successful, tx_hash, block}` |
| `get_hash()` | Anchored hash for a code, reading **state** via `view get` |
| `verify_anchor()` | Compares the on-chain hash with the expected one → `{verified, hash_registrado}` |

Custom error: `NearError`. Never escapes as a 500.

---

### 🛠️ 5. CLI scripts

```bash
cd backend
python -m scripts.anchor_demo        # HUE-2027-001: hash → anchor → verify (real Testnet)
python -m scripts.reanclar --listar  # batches with near_tx_hash = NULL, without writing on-chain
python -m scripts.reanclar          # re-anchors pending batches (idempotent)
```

Expected `anchor_demo` output:

```text
Lote    : HUE-2027-001
SHA-256 : 77304c85...
Anclado : tx=EEFcqP... block=277310783
Verificación on-chain: VERIFICADO
```

---

### 🔐 6. Environment variables

```bash
NEAR_NETWORK=testnet
NEAR_RPC_URL=https://test.rpc.fastnear.com
NEAR_ACCOUNT_ID=agrochainrural.testnet
NEAR_PRIVATE_KEY=ed25519:...
NEAR_CONTRACT_ID=agrochainrural.testnet
```

---

### ✅ 7. On-chain verification

`POST /api/verify` with `{"codigo", "hash_hex"}`
(guarded by `X-API-Key`: without it, it would be a free open proxy to the network) returns:

```json
{"verified": true, "hash_registrado": "242301d4...20da92"}
```

The consumer route is `GET /api/verify/{codigo}`, which closes the **triangulation**: hash recomputed on the server ↔ hash stored in the database ↔ hash returned by the contract. Any later modification of the batch data breaks the match.

> The transaction explorer is `https://explorer.testnet.near.org/transactions/<tx_hash>` (the batch page links straight to it). The block (`near_block`) is informational; verification does not depend on it.

---

### 🧪 8. Tests

```bash
cd backend
python -m pytest tests/ -v     # 84 tests, all without network
```

- `test_sha256.py`: determinism, key-order independence, change sensitivity.
- `test_near.py`: hash validation, anchoring with the NEAR client mocked, idempotency, verification (ok / different hash / unanchored code / RPC down).

[⬆ Back to top](#-anclaje-en-near-diseño-y-servicio)

---

## 🇧🇷 Português

📑 **Conteúdo:** [🔗 1. Design](#-1-design-da-ancoragem) · [🔄 2. Fluxo](#-2-fluxo-de-ancoragem) · [🔑 3. Conta e contrato](#-3-conta-e-contrato-na-testnet) · [🧩 4. Serviço](#-4-serviço-nearpy) · [🛠️ 5. Scripts](#-5-scripts-cli) · [🔐 6. Variáveis](#-6-variáveis-de-ambiente) · [✅ 7. Verificação](#-7-verificação-on-chain) · [🧪 8. Testes](#-8-testes)

---

### 🔗 1. Design da ancoragem

A impressão digital SHA-256 de cada lote é guardada como **entrada de um contrato KV próprio** na **NEAR Testnet**: um mapa `codigo → hash` onde a impressão viaja como **cadeia hexadecimal de 64 caracteres** — exatamente a que o backend compara, sem decodificações.

| Opção | O que é | Status |
| :--- | :--- | :--- |
| **A** | Contrato KV próprio (`set`/`get` sobre o estado) | ✅ **Escolhida** (v0.06) |
| **B** | Só argumentos da transação, sem contrato | Descartada |

*Por que a Opção A:* o RPC público da NEAR guarda o **detalhe** das transações por apenas ~36 horas; uma verificação que dependesse de ler a transação morreria com o arquivo. **O estado do contrato não caduca**: `view get` responde hoje igual como daqui a um ano. O contrato também fixa a regra de negócio da âncora: idempotência e rejeição de hash diferente.

| Componente | Decisão |
| :--- | :--- |
| Rede | NEAR **Testnet** (`testnet`) |
| Contrato | Conta própria (p. ex. `agrochainrural.testnet`), Rust + near-sdk 5.30 |
| Entrada on-chain | `get(codigo)` → hash hex de 64 caracteres (ou `null`) |
| Método de escrita | `set(codigo, hash)` — não payable, idempotente, rejeita hash diferente |
| Assinante | Conta da Finca Guarumo (`NEAR_PRIVATE_KEY`) |
| Regra de ouro | **Fotos/vídeos nunca vão para a blockchain** — apenas o hash |

**Propriedades do `set` (críticas):**

- **Idempotente:** reancorar com o mesmo hash é um *no-op* (os retries do backend são seguros).
- **Estrito:** ancorar um hash *diferente* para um código já ancorado faz panic — um lote não pode trocar de impressão.
- **Não payable:** o contrato não aceita NEAR; o *storage staking* é coberto pelo saldo da própria conta do contrato.

---

### 🔄 2. Fluxo de ancoragem

1. O backend calcula o hash do lote: `hash_lote(dados_lote)` (JSON canônico de 8 campos → SHA-256).
2. `anchor_hash(codigo, hash_hex)` valida o formato e chama o contrato via `near-kit` (`client.call("set", ...)`).
3. Em falhas transitórias do RPC tenta novamente (máx. 3); um **panic do contrato não é repetido** (não há nada a consertar).
4. Gravam-se `near_tx_hash` e `near_block` (a altura do bloco é cosmética: sem resolução, grava-se `None` e a âncora continua válida).
5. O consumidor verifica com `verify_anchor(codigo, hash_hex)`, que lê o **estado** do contrato (`view get`).

---

### 🔑 3. Conta e contrato na Testnet

```bash
cd backend
python -m scripts.near_account create <conta.testnet>  # cria a conta (faucet oficial, 10 NEAR) e imprime as chaves
python -m scripts.near_account show <conta.testnet>    # mostra o saldo
python -m scripts.desplegar_contrato                   # implanta contract/res/agrochain_kv.wasm em NEAR_CONTRACT_ID
```

`create` imprime `NEAR_ACCOUNT_ID` e `NEAR_PRIVATE_KEY` (`ed25519:...`) para guardar em `backend/.env` (nunca subir ao repositório). O faucet financia a conta uma única vez; esse saldo paga o *gas* das âncoras e o *storage staking* do contrato.

---

### 🧩 4. Serviço `near.py`

| Função | Responsabilidade |
| :--- | :--- |
| `get_client()` | Cliente `near-kit` (`NEAR_NETWORK`, `NEAR_RPC_URL`, conta e chave) |
| `_validar()` | Confere o formato de código e hash (64 hex) antes de tocar a rede |
| `_contrato()` | Resolve a conta do contrato (`NEAR_CONTRACT_ID`) |
| `_bloque_de()` | Altura do bloco da transação (2 chamadas RPC cruas; falha suave → `None`) |
| `anchor_hash()` | Chama `set` com retries; devolve `{successful, tx_hash, block}` |
| `get_hash()` | Hash ancorado para um código, lendo o **estado** com `view get` |
| `verify_anchor()` | Compara o hash on-chain com o esperado → `{verified, hash_registrado}` |

Erro próprio: `NearError`. Nunca escapa como 500.

---

### 🛠️ 5. Scripts CLI

```bash
cd backend
python -m scripts.anchor_demo        # HUE-2027-001: hash → ancora → verifica (Testnet real)
python -m scripts.reanclar --listar  # lotes com near_tx_hash = NULL, sem escrever na cadeia
python -m scripts.reanclar           # reancora os lotes pendentes (idempotente)
```

Saída esperada do `anchor_demo`:

```text
Lote    : HUE-2027-001
SHA-256 : 77304c85...
Anclado : tx=EEFcqP... bloque=277310783
Verificação on-chain: VERIFICADO
```

---

### 🔐 6. Variáveis de ambiente

```bash
NEAR_NETWORK=testnet
NEAR_RPC_URL=https://test.rpc.fastnear.com
NEAR_ACCOUNT_ID=agrochainrural.testnet
NEAR_PRIVATE_KEY=ed25519:...
NEAR_CONTRACT_ID=agrochainrural.testnet
```

---

### ✅ 7. Verificação on-chain

`POST /api/verify` com `{"codigo", "hash_hex"}`
(protegido com `X-API-Key`: sem ela seria um proxy aberto e gratuito à rede) retorna:

```json
{"verified": true, "hash_registrado": "242301d4...20da92"}
```

A rota do consumidor é `GET /api/verify/{codigo}`, que fecha a **triangulação**: hash recalculado no servidor ↔ hash guardado no banco ↔ hash devolvido pelo contrato. Qualquer alteração posterior dos dados do lote quebra a coincidência.

> O explorador da transação é `https://explorer.testnet.near.org/transactions/<tx_hash>` (a ficha do lote aponta direto para ele). O bloco (`near_block`) é informativo; a verificação não depende dele.

---

### 🧪 8. Testes

```bash
cd backend
python -m pytest tests/ -v     # 84 testes, todos sem rede
```

- `test_sha256.py`: determinismo, independência da ordem das chaves, sensibilidade a mudanças.
- `test_near.py`: validação de hash, ancoragem com o cliente NEAR simulado, idempotência, verificação (ok / hash diferente / código sem âncora / RPC caído).

[⬆ Voltar ao topo](#-anclaje-en-near-diseño-y-servicio)
