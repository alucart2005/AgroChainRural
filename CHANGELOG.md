# 📌 Changelog — AgroChain Rural

> Historial de versiones por rama (`Version-0.01` … `Version-0.06`; el detalle de 0.03–0.05 vive en la app, Ayuda → Novedades) · Formato de commits: `feat:`, `fix:`, `docs:`, `chore:`

> 🌐 **Idioma / Language:** [🇪🇸 Español](#-español) · [🇺🇸 English](#-english) · [🇧🇷 Português](#-português)

---

## 🇪🇸 Español

### Versión 0.06 — 2026-11-11 · rama `Version-0.06`

El ancla pasa de **Stellar Testnet** a un **contrato KV propio en NEAR Testnet**. Esta versión nace en el repositorio nuevo [`AgroChainRural`](https://github.com/alucart2005/AgroChainRural); el histórico 0.01–0.05 queda en [`AgroTraceRural`](https://github.com/alucart2005/AgroTraceRural).

- **`feat(contract)`** Contrato KV en Rust (near-sdk 5.30): `set(codigo, hash)` — idempotente: reanclar con el mismo hash es un no-op y un hash distinto para el mismo lote se rechaza — y `get` de solo lectura. 7 tests; wasm versionado en `contract/res/agrochain_kv.wasm`.
- **`feat(backend)`** `app/services/near.py` sustituye a `stellar.py`: el SHA-256 viaja como hex de 64 caracteres y la verificación lee el **estado** del contrato (`view get`), porque el RPC público solo retiene el detalle de transacciones ~36 h. Migración `0003_near` añade `near_tx_hash`/`near_block`; `stellar_*` queda como archivo histórico. `POST /api/verify` audita un hash suelto contra el contrato (con `X-API-Key`).
- **`feat(scripts)`** `near_account` (faucet oficial), `desplegar_contrato` y `reanclar`; `stellar_account` se retira. `requests` pasa a declararse explícito en `requirements.txt` (antes llegaba vía `stellar-sdk`).
- **`feat(frontend)`** `Lote.near_tx_hash`/`near_block`, `Verificacion.ledger` → `block`, enlace al explorador de NEAR y revisión de textos es/en/pt. El lote demo se re-siembra (v4) con la transacción NEAR real de `HUE-2026-008`.
- La suite pasa a **84 tests** (backend) — `stellar-sdk` desinstalado — y el contrato suma 7 propios.

### Versión 0.02 — 2026-11-05 · rama `Version-0.02`

Mantenimiento y sincronización de la plataforma.

- **`fix(backend)`** Se reemplaza la clase interna `Config` de Pydantic por `SettingsConfigDict` en `app/core/config.py`: desaparece el aviso `PydanticDeprecatedSince20` en cada arranque.
- **`chore(deps)`** Se añade `httpx2` a `requirements.txt` para el `TestClient` de Starlette 1.7 (el uso de `httpx` quedó deprecado). La suite pasa de **71 tests con 2 avisos a 71 tests sin avisos**.
- **`chore(db)`** La SQLite local de desarrollo se realinea con las migraciones: sello `alembic_version` en `0002_usuarios` y reconstrucción de `lotes` (índice `ix_lotes_usuario_id` + FK `SET NULL`, creados por `asegurar_columnas_sqlite` sin quedar registrados). Los 8 lotes locales se conservan y `alembic check` queda en verde.
- **`chore(github)`** Los issues **#1..#8 (HU-01..HU-08)** se cierran con `completed`, alineados con el `Status=Done` del tablero del proyecto #14.
- **`docs`** Se publica este changelog.

### Versión 0.01 — 2026-10-30 · rama `Version-0.01`

Primera entrega documental cerrada.

- **`docs`** El enlace del video demo en `README.md` se actualiza a `https://www.youtube.com/watch?v=stVQCivrmCg`.
- **`docs`** `docs/semana1/ProblemBrief.md` se renombra de «Agro Cassis» a «AgroChain Rural» y se añade su PDF.

### Base `main` — HU-01..HU-08 entregadas (2026-10-30, `aec1a36`)

- **`feat(auth)`** Ingreso de productores con Google, datos del primer ingreso y registro de lotes con sesión (HU-06, HU-07, HU-08), con JWT y verificación del ID token.
- **`fix(auth)`** Endurecimiento del registro: espacios en blanco rechazados y carrera de `google_sub` respondida con 409.
- **`docs(backlog)`** Backlog de autenticación con 51 tareas cerradas y tablero #14 con las 8 historias en `Done`.

---

## 🇺🇸 English

### Version 0.06 — 2026-11-11 · branch `Version-0.06`

The anchor moves from **Stellar Testnet** to an **own KV contract on NEAR Testnet**. This version is born in the new repo [`AgroChainRural`](https://github.com/alucart2005/AgroChainRural); history 0.01–0.05 stays in [`AgroTraceRural`](https://github.com/alucart2005/AgroTraceRural).

- **`feat(contract)`** KV contract in Rust (near-sdk 5.30): `set(codigo, hash)` — idempotent: re-anchoring the same hash is a no-op and a different hash for the same batch is rejected — and the read-only `get`. 7 tests; wasm versioned at `contract/res/agrochain_kv.wasm`.
- **`feat(backend)`** `app/services/near.py` replaces `stellar.py`: the SHA-256 travels as 64 hex characters and verification reads the contract **state** (`view get`), because the public RPC keeps transaction detail for only ~36 h. Migration `0003_near` adds `near_tx_hash`/`near_block`; `stellar_*` remains as a historical archive. `POST /api/verify` audits a loose hash against the contract (with `X-API-Key`).
- **`feat(scripts)`** `near_account` (official faucet), `desplegar_contrato` and `reanclar`; `stellar_account` removed. `requests` becomes explicitly declared in `requirements.txt` (it used to arrive via `stellar-sdk`).
- **`feat(frontend)`** `Lote.near_tx_hash`/`near_block`, `Verificacion.ledger` → `block`, link to the NEAR explorer and copy review in es/en/pt. The demo batch is reseeded (v4) with the real NEAR transaction of `HUE-2026-008`.
- The suite goes up to **84 tests** (backend) — `stellar-sdk` uninstalled — plus 7 in the contract.

### Version 0.02 — 2026-11-05 · branch `Version-0.02`

Platform maintenance and synchronization.

- **`fix(backend)`** Pydantic's inner `Config` class replaced with `SettingsConfigDict` in `app/core/config.py`, removing the `PydanticDeprecatedSince20` warning on every startup.
- **`chore(deps)`** `httpx2` added to `requirements.txt` for Starlette 1.7's `TestClient` (`httpx` is deprecated there). The suite goes from **71 tests with 2 warnings to 71 tests with none**.
- **`chore(db)`** The local development SQLite is realigned with the migrations: `alembic_version` stamped at `0002_usuarios` and `lotes` rebuilt (index `ix_lotes_usuario_id` + `SET NULL` FK, previously added by `asegurar_columnas_sqlite` without being recorded). The 8 local batches are preserved and `alembic check` passes.
- **`chore(github)`** Issues **#1..#8 (HU-01..HU-08)** closed as `completed`, matching the `Status=Done` on project board #14.
- **`docs`** This changelog published.

### Version 0.01 — 2026-10-30 · branch `Version-0.01`

First closed documentation delivery.

- **`docs`** Demo video link in `README.md` updated to `https://www.youtube.com/watch?v=stVQCivrmCg`.
- **`docs`** `docs/semana1/ProblemBrief.md` renamed from «Agro Cassis» to «AgroChain Rural», with its PDF added.

### `main` baseline — HU-01..HU-08 delivered (2026-10-30, `aec1a36`)

- **`feat(auth)`** Farmer Google sign-in, first-login data capture and authenticated batch registration (HU-06, HU-07, HU-08) with JWT and ID-token verification.
- **`fix(auth)`** Registration hardening: whitespace-only fields rejected and `google_sub` races answered with 409.
- **`docs(backlog)`** Auth backlog with 51 tasks closed and board #14 showing all 8 stories as `Done`.

---

## 🇧🇷 Português

### Versão 0.06 — 2026-11-11 · branch `Version-0.06`

A âncora passa da **Stellar Testnet** para um **contrato KV próprio na NEAR Testnet**. Esta versão nasce no repositório novo [`AgroChainRural`](https://github.com/alucart2005/AgroChainRural); o histórico 0.01–0.05 fica no [`AgroTraceRural`](https://github.com/alucart2005/AgroTraceRural).

- **`feat(contract)`** Contrato KV em Rust (near-sdk 5.30): `set(codigo, hash)` — idempotente: reancorar o mesmo hash é um no-op e um hash diferente para o mesmo lote é rejeitado — e o `get` de leitura. 7 testes; wasm versionado em `contract/res/agrochain_kv.wasm`.
- **`feat(backend)`** `app/services/near.py` substitui `stellar.py`: o SHA-256 viaja como 64 caracteres hex e a verificação lê o **estado** do contrato (`view get`), porque o RPC público guarda o detalhe das transações por apenas ~36 h. A migração `0003_near` adiciona `near_tx_hash`/`near_block`; `stellar_*` fica como arquivo histórico. `POST /api/verify` audita um hash avulso contra o contrato (com `X-API-Key`).
- **`feat(scripts)`** `near_account` (faucet oficial), `desplegar_contrato` e `reanclar`; `stellar_account` sai. `requests` passa a ser declarado explicitamente em `requirements.txt` (antes vinha via `stellar-sdk`).
- **`feat(frontend)`** `Lote.near_tx_hash`/`near_block`, `Verificacion.ledger` → `block`, link para o explorador da NEAR e revisão de textos es/en/pt. O lote demo é refeito (v4) com a transação NEAR real de `HUE-2026-008`.
- A suíte sobe para **84 testes** (backend) — `stellar-sdk` desinstalado — e o contrato soma 7 próprios.

### Versão 0.02 — 2026-11-05 · branch `Version-0.02`

Manutenção e sincronização da plataforma.

- **`fix(backend)`** A classe interna `Config` do Pydantic foi substituída por `SettingsConfigDict` em `app/core/config.py`, eliminando o aviso `PydanticDeprecatedSince20` em cada inicialização.
- **`chore(deps)`** `httpx2` adicionado ao `requirements.txt` para o `TestClient` do Starlette 1.7 (o uso de `httpx` ficou deprecado). A suíte passou de **71 testes com 2 avisos para 71 testes sem avisos**.
- **`chore(db)`** O SQLite local de desenvolvimento foi realinhado com as migrações: `alembic_version` carimbado em `0002_usuarios` e `lotes` reconstruída (índice `ix_lotes_usuario_id` + FK `SET NULL`, antes criados por `asegurar_columnas_sqlite` sem registro). Os 8 lotes locais foram preservados e `alembic check` ficou verde.
- **`chore(github)`** Issues **#1..#8 (HU-01..HU-08)** fechados como `completed`, alinhados com o `Status=Done` no quadro do projeto #14.
- **`docs`** Este changelog publicado.

### Versão 0.01 — 2026-10-30 · branch `Version-0.01`

Primeira entrega documental encerrada.

- **`docs`** O link do vídeo demo no `README.md` foi atualizado para `https://www.youtube.com/watch?v=stVQCivrmCg`.
- **`docs`** `docs/semana1/ProblemBrief.md` renomeado de «Agro Cassis» para «AgroChain Rural», com o seu PDF adicionado.

### Base `main` — HU-01..HU-08 entregues (2026-10-30, `aec1a36`)

- **`feat(auth)`** Entrada de produtores com Google, dados do primeiro acesso e registro de lotes com sessão (HU-06, HU-07, HU-08), com JWT e verificação do ID token.
- **`fix(auth)`** Endurecimento do registro: campos só com espaços rejeitados e corrida de `google_sub` respondida com 409.
- **`docs(backlog)`** Backlog de autenticação com 51 tarefas encerradas e quadro #14 com as 8 histórias em `Done`.
