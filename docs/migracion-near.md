# 🔄 Migración del anclaje: Stellar → NEAR — AgroChain Rural

> **Versión 0.06** (`Version-0.06`, 2026-11-11) · Reemplaza el *Memo Hash* de Stellar Testnet por un **contrato KV propio en NEAR Testnet**.
> 🌐 **Idioma / Language:** [🇪🇸 Español](#-español) · [🇺🇸 English](#-english) · [🇧🇷 Português](#-português)

---

## 🇪🇸 Español

### ¿Por qué migrar?

El anclaje original guardaba el SHA-256 de cada lote como **Memo Hash** de un pago de 1 XLM en Stellar Testnet, y la verificación (HU-03) buscaba esa transacción en Horizon. El problema: la verificación dependía del **histórico de transacciones**, que es un dato efímero — los nodos públicos expuran el detalle de las transacciones antiguas — y el modelo (pago a uno mismo con el hash en el memo) guarda el dato *junto a la transacción*, no *en un lugar consultable*.

NEAR resuelve las dos cosas con un **contrato con estado**: el hash vive en un mapa `codigo → hash` dentro del contrato y se lee con una llamada de solo lectura (`view get`). El estado del contrato **no caduca**: un lote anclado hoy se puede verificar dentro de un año sin depender de que ningún archivo haya retenido el detalle de la transacción.

| Aspecto | Stellar (≤ 0.05) | NEAR (0.06) |
|---|---|---|
| Mechanismo | Memo Hash de un pago de 1 XLM | Entrada `codigo → hash` en un contrato KV |
| Dato on-chain | 32 bytes (memo) | 64 caracteres hex (valor de la entrada) |
| Verificación | Buscar la transacción en Horizon | Leer el estado del contrato (`view get`) |
| Durabilidad | Ligada al archivo de transacciones | Estado del contrato: no caduca |
| Confirmación | 3–5 s | 1–3 s |
| Coste por ancla | 1 XLM de operación (0,00001 XLM de tarifa) | ≈0,001 NEAR |

### El contrato (`contract/`)

- Rust + **near-sdk 5.30**, edition 2024. Código en `contract/src/lib.rs`; artefacto desplegable versionado en `contract/res/agrochain_kv.wasm`.
- **`set(codigo, hash)`** (método de escritura, no payable):
  - **Idempotente:** si el código ya está anclado con el mismo hash, no hace nada (reintentos seguros);
  - **Estricto:** si el código ya está anclado con *otro* hash, hace panic — un lote no puede cambiar de huella;
  - El *storage staking* lo cubre el saldo de la cuenta del contrato (la fondea el faucet, 10 NEAR).
- **`get(codigo)`** (view): devuelve el hash anclado o `null`.
- 7 tests unitarios (sin red) con `cargo test --release`.

### Qué cambió en el código

| Pieza | Cambio |
|---|---|
| `backend/app/services/near.py` | Nuevo servicio: `anchor_hash`, `verify_anchor` (por estado), reintentos ante fallos transitorios del RPC |
| `backend/app/services/stellar.py` | **Eliminado** (igual que `scripts/stellar_account.py`) |
| Modelo `Lote` | Añade `near_tx_hash` y `near_block`; `stellar_tx_hash`/`stellar_ledger` quedan como **archivo histórico** (no se leen ni se escriben) |
| Alembic | `0003_near` añade las dos columnas (`op.add_column`: SQLite lo soporta y `batch` recrearía `lotes`) |
| `GET /api/verify/{codigo}` | Misma forma, pero `ledger` pasa a **`block`** y la verificación contrasta el estado del contrato |
| `POST /api/verify` | Nueva forma: `{codigo, hash_hex}` audita un hash suelto contra el contrato (protegido con `X-API-Key`; sin clave sería un proxy gratuito a la red) |
| Frontend | `Lote.near_tx_hash`/`near_block`, `Verificacion.block`, enlace a `explorer.testnet.near.org`, textos es/en/pt |
| Variables de entorno | `STELLAR_NETWORK`/`HORIZON_URL`/`STELLAR_PUBLIC_KEY`/`STELLAR_SECRET_KEY` → `NEAR_NETWORK`/`NEAR_RPC_URL`/`NEAR_ACCOUNT_ID`/`NEAR_PRIVATE_KEY`/`NEAR_CONTRACT_ID` |
| `render.yaml` | Bloque NEAR_* (secretos con `sync: false`) |
| Paquetes | Fuera `stellar-sdk`; entra `near-kit` (1.3); `requests` pasa a declararse explícito |

> ⚠️ **Rompiendo (API pública):** el campo `ledger` de `Verificacion` pasa a llamarse `block` y `Lote` expone `near_tx_hash`/`near_block` en lugar de `stellar_*`. Los clientes antiguos que leyeran `ledger` deben actualizarse.

`Settings` usa `extra="ignore"`, así que un `.env` heredado con las `STELLAR_*` viejas no tumba el arranque mientras se renombra.

### Despliegue en testnet (receta)

```bash
cd backend
python -m scripts.near_account create <cuenta.testnet>   # faucet: crea la cuenta (10 NEAR) e imprime las claves para .env
python -m scripts.desplegar_contrato                     # despliega contract/res/agrochain_kv.wasm en NEAR_CONTRACT_ID
python -m scripts.anchor_demo                            # ancla el lote demo y verifica de verdad
python -m scripts.reanclar --listar                      # ¿qué lotes quedan sin ancla NEAR?
python -m scripts.reanclar                               # re-ancla los lotes con near_tx_hash = None
```

- **Cuenta y contrato del piloto:** `agrochainrural.testnet` ([explorador](https://explorer.testnet.near.org/accounts/agrochainrural.testnet)).
- **Explorador de transacciones:** `https://explorer.testnet.near.org/transactions/<hash>`.
- **RPC por defecto:** `https://test.rpc.fastnear.com` (configurable con `NEAR_RPC_URL`).

### Re-anclaje de los lotes históricos

Los 8 lotes del piloto quedaron anclados en Stellar en su momento y **conservan esa ancla** en `stellar_tx_hash`/`stellar_ledger` como archivo. La migración no la borra: añade la columna `near_*` y la deja `NULL` («pendiente de anclar en NEAR»). Hasta ejecutar `scripts.reanclar`, `GET /api/verify/{codigo}` responde `verificado: false` con el aviso correspondiente. Re-anclar es seguro e idempotente: el contrato rechaza un hash distinto y no hace nada con el mismo.

---

## 🇺🇸 English

### Why migrate?

The original anchor stored each batch's SHA-256 as the **Memo Hash** of a 1 XLM payment on Stellar Testnet, and verification (HU-03) looked up that transaction on Horizon. The problem: verification depended on the **transaction history**, an ephemeral record — public nodes prune old transaction detail — and the model (a self-payment with the hash in the memo) keeps the data *next to the transaction*, not *in a queryable place*.

NEAR solves both with a **stateful contract**: the hash lives in a `codigo → hash` map inside the contract and is read with a read-only call (`view get`). Contract state **does not expire**: a batch anchored today can still be verified a year from now, regardless of whether any archive kept the transaction detail.

| Aspect | Stellar (≤ 0.05) | NEAR (0.06) |
|---|---|---|
| Mechanism | Memo Hash of a 1 XLM payment | `codigo → hash` entry in a KV contract |
| On-chain data | 32 bytes (memo) | 64 hex characters (entry value) |
| Verification | Look up the transaction on Horizon | Read contract state (`view get`) |
| Durability | Tied to the transaction archive | Contract state: no expiry |
| Confirmation | 3–5 s | 1–3 s |
| Cost per anchor | 1 XLM of operation (0.00001 XLM fee) | ≈0.001 NEAR |

### The contract (`contract/`)

- Rust + **near-sdk 5.30**, edition 2024. Code in `contract/src/lib.rs`; the deployable artifact is versioned at `contract/res/agrochain_kv.wasm`.
- **`set(codigo, hash)`** (write method, not payable):
  - **Idempotent:** if the code is already anchored with the same hash, it does nothing (safe retries);
  - **Strict:** if the code is already anchored with a *different* hash, it panics — a batch cannot change its fingerprint;
  - Storage staking is covered by the contract account's balance (funded by the faucet, 10 NEAR).
- **`get(codigo)`** (view): returns the anchored hash or `null`.
- 7 unit tests (no network) with `cargo test --release`.

### What changed in the code

| Piece | Change |
|---|---|
| `backend/app/services/near.py` | New service: `anchor_hash`, state-based `verify_anchor`, retries on transient RPC failures |
| `backend/app/services/stellar.py` | **Removed** (same as `scripts/stellar_account.py`) |
| `Lote` model | Adds `near_tx_hash` and `near_block`; `stellar_tx_hash`/`stellar_ledger` stay as a **historical archive** (neither read nor written) |
| Alembic | `0003_near` adds the two columns (`op.add_column`: SQLite supports it and `batch` would recreate `lotes`) |
| `GET /api/verify/{codigo}` | Same shape, but `ledger` becomes **`block`** and verification contract state is checked |
| `POST /api/verify` | New shape: `{codigo, hash_hex}` audits a loose hash against the contract (guarded by `X-API-Key`; without it, it would be a free open proxy to the network) |
| Frontend | `Lote.near_tx_hash`/`near_block`, `Verificacion.block`, link to `explorer.testnet.near.org`, es/en/pt copy |
| Environment variables | `STELLAR_NETWORK`/`HORIZON_URL`/`STELLAR_PUBLIC_KEY`/`STELLAR_SECRET_KEY` → `NEAR_NETWORK`/`NEAR_RPC_URL`/`NEAR_ACCOUNT_ID`/`NEAR_PRIVATE_KEY`/`NEAR_CONTRACT_ID` |
| `render.yaml` | NEAR_* block (secrets with `sync: false`) |
| Packages | Out `stellar-sdk`; in `near-kit` (1.3); `requests` becomes explicitly declared |

> ⚠️ **Breaking (public API):** `Verificacion.ledger` is renamed to `block`, and `Lote` exposes `near_tx_hash`/`near_block` instead of `stellar_*`. Old clients reading `ledger` must update.

`Settings` uses `extra="ignore"`, so a legacy `.env` with the old `STELLAR_*` keys does not break startup.

### Testnet deployment (recipe)

```bash
cd backend
python -m scripts.near_account create <account.testnet>   # faucet: creates the account (10 NEAR) and prints the keys for .env
python -m scripts.desplegar_contrato                     # deploys contract/res/agrochain_kv.wasm to NEAR_CONTRACT_ID
python -m scripts.anchor_demo                            # anchors the demo batch and verifies for real
python -m scripts.reanclar --listar                      # which batches lack a NEAR anchor?
python -m scripts.reanclar                               # re-anchors batches with near_tx_hash = None
```

- **Pilot account/contract:** `agrochainrural.testnet` ([explorer](https://explorer.testnet.near.org/accounts/agrochainrural.testnet)).
- **Transaction explorer:** `https://explorer.testnet.near.org/transactions/<hash>`.
- **Default RPC:** `https://test.rpc.fastnear.com` (configurable via `NEAR_RPC_URL`).

### Re-anchoring historical batches

The pilot's 8 batches were anchored on Stellar at the time and **keep that anchor** in `stellar_tx_hash`/`stellar_ledger` as an archive. The migration does not delete it: it adds the `near_*` columns and leaves them `NULL` ("pending NEAR anchor"). Until `scripts.reanclar` runs, `GET /api/verify/{codigo}` answers `verificado: false` with the matching notice. Re-anchoring is safe and idempotent: the contract rejects a different hash and does nothing with the same one.

---

## 🇧🇷 Português

### Por que migrar?

A âncora original guardava o SHA-256 de cada lote como **Memo Hash** de um pagamento de 1 XLM na Stellar Testnet, e a verificação (HU-03) buscava essa transação no Horizon. O problema: a verificação dependia do **histórico de transações**, um registro efêmero — os nós públicos expurgam o detalhe das transações antigas — e o modelo (um pagamento a si mesmo com o hash no memo) guarda o dado *junto à transação*, não *em um lugar consultável*.

A NEAR resolve as duas coisas com um **contrato com estado**: o hash vive em um mapa `codigo → hash` dentro do contrato e é lido com uma chamada de leitura (`view get`). O estado do contrato **não caduca**: um lote ancorado hoje ainda pode ser verificado daqui a um ano, independente de algum arquivo ter guardado o detalhe da transação.

| Aspecto | Stellar (≤ 0.05) | NEAR (0.06) |
|---|---|---|
| Mecanismo | Memo Hash de um pagamento de 1 XLM | Entrada `codigo → hash` em um contrato KV |
| Dado on-chain | 32 bytes (memo) | 64 caracteres hex (valor da entrada) |
| Verificação | Buscar a transação no Horizon | Ler o estado do contrato (`view get`) |
| Durabilidade | Ligada ao arquivo de transações | Estado do contrato: sem prazo |
| Confirmação | 3–5 s | 1–3 s |
| Custo por âncora | 1 XLM de operação (0,00001 XLM de tarifa) | ≈0,001 NEAR |

### O contrato (`contract/`)

- Rust + **near-sdk 5.30**, edition 2024. Código em `contract/src/lib.rs`; o artefato implantável está versionado em `contract/res/agrochain_kv.wasm`.
- **`set(codigo, hash)`** (método de escrita, não payable):
  - **Idempotente:** se o código já está ancorado com o mesmo hash, não faz nada (retries seguros);
  - **Estrito:** se o código já está ancorado com *outro* hash, faz panic — um lote não pode trocar de impressão digital;
  - O *storage staking* é coberto pelo saldo da conta do contrato (financiada pelo faucet, 10 NEAR).
- **`get(codigo)`** (view): devolve o hash ancorado ou `null`.
- 7 testes unitários (sem rede) com `cargo test --release`.

### O que mudou no código

| Peça | Mudança |
|---|---|
| `backend/app/services/near.py` | Novo serviço: `anchor_hash`, `verify_anchor` por estado, retries em falhas transitórias do RPC |
| `backend/app/services/stellar.py` | **Removido** (igual que `scripts/stellar_account.py`) |
| Modelo `Lote` | Adiciona `near_tx_hash` e `near_block`; `stellar_tx_hash`/`stellar_ledger` ficam como **arquivo histórico** (nem lidos, nem escritos) |
| Alembic | `0003_near` adiciona as duas colunas (`op.add_column`: o SQLite suporta e o `batch` recriaria `lotes`) |
| `GET /api/verify/{codigo}` | Mesma forma, mas `ledger` passa a **`block`** e a verificação consulta o estado do contrato |
| `POST /api/verify` | Nova forma: `{codigo, hash_hex}` audita um hash avulso contra o contrato (protegido com `X-API-Key`; sem a chave seria um proxy gratuito à rede) |
| Frontend | `Lote.near_tx_hash`/`near_block`, `Verificacion.block`, link para `explorer.testnet.near.org`, textos es/en/pt |
| Variáveis de ambiente | `STELLAR_NETWORK`/`HORIZON_URL`/`STELLAR_PUBLIC_KEY`/`STELLAR_SECRET_KEY` → `NEAR_NETWORK`/`NEAR_RPC_URL`/`NEAR_ACCOUNT_ID`/`NEAR_PRIVATE_KEY`/`NEAR_CONTRACT_ID` |
| `render.yaml` | Bloco NEAR_* (segredos com `sync: false`) |
| Pacotes | Sai `stellar-sdk`; entra `near-kit` (1.3); `requests` passa a ser declarado explicitamente |

> ⚠️ **Rompendo (API pública):** o campo `ledger` de `Verificacion` passa a se chamar `block` e `Lote` expõe `near_tx_hash`/`near_block` em vez de `stellar_*`. Clientes antigos que liam `ledger` precisam atualizar.

`Settings` usa `extra="ignore"`, então um `.env` herdado com as `STELLAR_*` antigas não derruba a inicialização enquanto é renomeado.

### Implantação na testnet (receita)

```bash
cd backend
python -m scripts.near_account create <conta.testnet>    # faucet: cria a conta (10 NEAR) e imprime as chaves para o .env
python -m scripts.desplegar_contrato                     # implanta contract/res/agrochain_kv.wasm em NEAR_CONTRACT_ID
python -m scripts.anchor_demo                            # ancora o lote demo e verifica de verdade
python -m scripts.reanclar --listar                      # quais lotes estão sem âncora NEAR?
python -m scripts.reanclar                               # reancora os lotes com near_tx_hash = None
```

- **Conta/contrato do piloto:** `agrochainrural.testnet` ([explorador](https://explorer.testnet.near.org/accounts/agrochainrural.testnet)).
- **Explorador de transações:** `https://explorer.testnet.near.org/transactions/<hash>`.
- **RPC padrão:** `https://test.rpc.fastnear.com` (configurável com `NEAR_RPC_URL`).

### Reancoragem dos lotes históricos

Os 8 lotes do piloto foram ancorados na Stellar em seu momento e **conservam essa âncora** em `stellar_tx_hash`/`stellar_ledger` como arquivo. A migração não a apaga: adiciona as colunas `near_*` e as deixa `NULL` («pendente de ancorar na NEAR»). Até executar `scripts.reanclar`, `GET /api/verify/{codigo}` responde `verificado: false` com o aviso correspondente. Reancorar é seguro e idempotente: o contrato rejeita um hash diferente e não faz nada com o mesmo.
