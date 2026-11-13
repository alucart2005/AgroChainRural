# ⚓ Contratos inteligentes en NEAR: por qué NEAR y cómo funciona el nuestro

> **Proyecto:** AgroChain Rural · **Tema:** el contrato KV de AgroChain (`contract/`) y por qué el ecosistema NEAR encaja con un piloto rural
>
> 🌐 **Historia:** el MVP original anclaba sin contrato (Memo Hash en Stellar); la versión 0.06 pasa a este contrato KV — ver [`docs/migracion-near.md`](../migracion-near.md).

> 🌐 **Idioma / Language:** [🇪🇸 Español](#-español) · [🇺🇸 English](#-english) · [🇧🇷 Português](#-português)

---

## 🇪🇸 Español

📑 **Contenido:** [🧩 1. Qué ofrece](#-1-qué-ofrece-el-ecosistema-near) · [✅ 2. Ventajas](#-2-ventajas-de-near-para-agrochain) · [🥚 3. El contrato de AgroChain](#-3-el-contrato-de-agrochain-rural) · [🚀 4. Escalación](#-4-ruta-de-escalación)

---

### 🧩 1. Qué ofrece el ecosistema NEAR

NEAR ejecuta contratos inteligentes escritos en **Rust** (o AS/JS) y compilados a **WebAssembly (Wasm)**, sobre cuentas con nombre legible (no direcciones opacas). El ecosistema entrega herramientas oficiales listas para usar:

| Herramienta | Para qué sirve |
| :--- | :--- |
| **near-sdk (Rust)** | Escribir, probar y depurar contratos; macros `#[near]` |
| **cargo + rustup** | Build y tests unitarios con el mismo flujo de Rust (`wasm32-unknown-unknown`) |
| **JSON-RPC** | Invocar métodos (`query` / `call_function`), leer estado y enviar transacciones |
| **near-kit (Python)** | Cliente de alto nivel con el que el backend FastAPI firma `set` y lee `get` |
| **Faucet de Testnet** | Crea y fondea cuentas de prueba (10 NEAR) mediante `helper.nearprotocol.com` |
| **Explorador** | `explorer.testnet.near.org`: transacciones, contrato y estado legible |

---

### ✅ 2. Ventajas de NEAR para AgroChain

1. **Estado persistente, no solo transacciones.** Un contrato NEAR tiene *storage* propio: `view get` responde sin depender del histórico del RPC (que retiene el detalle de transacciones ~36 h). Para una huella que debe verificarse meses después, es la diferencia clave.
2. **Finalidad rápida (1–3 s).** Ideal para el punto de venta rural: el productor ancla al registrar y el consumidor verifica al escanear.
3. **Costos bajos y predecibles.** Anclar cuesta ≈0,001 NEAR de *gas* + *storage staking* (~100 bytes por lote); el plan de la cuenta del contrato (faucet) lo cubre de sobra en un piloto.
4. **Seguridad por diseño (Rust + Wasm).** Rust elimina clases enteras de bugs (memoria, hilos) antes de compilar; Wasm acota lo que un contrato puede ejecutar.
5. **Cuentas con nombre.** `agrochainrural.testnet` es legible y verificable en el explorador: el piloto puede *mostrar* su contrato a un auditor sin explicar direcciones.
6. **Tests sin red.** Los 7 tests del contrato corren con `cargo test` en segundos, sin tocar Testnet ni gastar NEAR.
7. **Bajo consumo energético.** NEAR usa PoS con finalidad rápida; sin proof-of-work.

---

### 🥚 3. El contrato de AgroChain Rural

El contrato vive en `contract/src/lib.rs` (near-sdk 5.30, edition 2024) y su artefacto desplegable está versionado en `contract/res/agrochain_kv.wasm`. Es deliberadamente pequeño — dos métodos:

```rust
pub struct AgroChainKv {
    /// codigo_de_lote → hash SHA-256 en hex.
    lotes: LookupMap<String, String>,
}

#[near]
impl AgroChainKv {
    /// Ancla el hash de un lote. Idempotente y no payable.
    pub fn set(&mut self, codigo: String, hash: String) { /* ... */ }

    /// Devuelve el hash anclado para un código, o `None` si aún no existe.
    pub fn get(&self, codigo: String) -> Option<String> { /* ... */ }
}
```

**Decisiones de diseño:**

| Decisión | Por qué |
| :--- | :--- |
| Hash como **hex de 64 caracteres** (no `[u8; 32]`) | El `view get` devuelve exactamente el string que el backend ya compara; la paridad `sha256.py` ↔ `hash.ts` no cambia |
| `set` **idempotente** (mismo hash → no-op) | Los reintentos del backend son seguros; reanclar no rompe nada |
| `set` **estricto** (hash distinto → panic) | Un lote no puede cambiar de huella: esa es la prueba de integridad |
| `set` **no payable** | El contrato no maneja dinero; el *storage staking* lo cubre el saldo de la cuenta del contrato |
| `LookupMap` (no `UnorderedMap`) | Solo se consulta por clave exacta; el prefijo de storage es más barato |

Los 7 tests (`cargo test --release`) cubren: guardar/leer, código desconocido → `None`, idempotencia, rechazo de hash mal formado, código vacío, hash distinto para el mismo código y aislamiento entre lotes.

---

### 🚀 4. Ruta de escalación

1. **Hoy (v0.06):** contrato KV `codigo → hash` — una huella por lote, verificación por estado.
2. **Etapa 2:** eventos de la línea de tiempo (cosecha → clasificación → empaque → despacho) como entradas ancladas por índice, sin tocar el hash del lote.
3. **Etapa 3:** representación de cubetas/lotes con tokens (NEAR FT/NFT) y pagos programados al productor.

[⬆ Volver al inicio](#-contratos-inteligentes-en-near-por-qué-near-y-cómo-funciona-el-nuestro)

---

## 🇺🇸 English

📑 **Contents:** [🧩 1. What the ecosystem offers](#-1-what-the-near-ecosystem-offers) · [✅ 2. Advantages](#-2-advantages-of-near-for-agrochain) · [🥚 3. AgroChain's contract](#-3-agrochain-rurals-contract) · [🚀 4. Scaling path](#-4-scaling-path)

---

### 🧩 1. What the NEAR ecosystem offers

NEAR runs smart contracts written in **Rust** (or AS/JS) and compiled to **WebAssembly (Wasm)**, on human-readable named accounts. The ecosystem ships ready-to-use official tooling:

| Tool | What it is for |
| :--- | :--- |
| **near-sdk (Rust)** | Write, test and debug contracts; `#[near]` macros |
| **cargo + rustup** | Build and unit tests with the regular Rust flow (`wasm32-unknown-unknown`) |
| **JSON-RPC** | Invoke methods (`query` / `call_function`), read state and send transactions |
| **near-kit (Python)** | High-level client the FastAPI backend uses to sign `set` and read `get` |
| **Testnet faucet** | Creates and funds test accounts (10 NEAR) via `helper.nearprotocol.com` |
| **Explorer** | `explorer.testnet.near.org`: transactions, contract and readable state |

---

### ✅ 2. Advantages of NEAR for AgroChain

1. **Persistent state, not just transactions.** A NEAR contract has its own *storage*: `view get` answers without depending on the RPC history (which keeps transaction detail for only ~36 h). For a fingerprint that must be verifiable months later, that is the key difference.
2. **Fast finality (1–3 s).** Ideal at the rural point of sale: the producer anchors when registering and the consumer verifies when scanning.
3. **Low, predictable costs.** Anchoring costs ≈0.001 NEAR of *gas* + storage staking (~100 bytes per batch); the contract account's faucet funding easily covers a pilot.
4. **Secure by design (Rust + Wasm).** Rust eliminates entire bug classes (memory, threads) before compiling; Wasm constrains what a contract can execute.
5. **Named accounts.** `agrochainrural.testnet` is readable and verifiable in the explorer: the pilot can *show* its contract to an auditor without explaining hex addresses.
6. **Networkless tests.** The contract's 7 tests run with `cargo test` in seconds, without touching Testnet or spending NEAR.
7. **Low energy use.** NEAR is PoS with fast finality; no proof-of-work.

---

### 🥚 3. AgroChain Rural's contract

The contract lives in `contract/src/lib.rs` (near-sdk 5.30, edition 2024) and its deployable artifact is versioned at `contract/res/agrochain_kv.wasm`. It is deliberately small — two methods:

```rust
pub struct AgroChainKv {
    /// batch_code → SHA-256 hash in hex.
    lotes: LookupMap<String, String>,
}

#[near]
impl AgroChainKv {
    /// Anchors a batch's hash. Idempotent and not payable.
    pub fn set(&mut self, codigo: String, hash: String) { /* ... */ }

    /// Returns the anchored hash for a code, or `None` if it does not exist yet.
    pub fn get(&self, codigo: String) -> Option<String> { /* ... */ }
}
```

**Design decisions:**

| Decision | Why |
| :--- | :--- |
| Hash as **64-char hex** (not `[u8; 32]`) | `view get` returns exactly the string the backend compares; the `sha256.py` ↔ `hash.ts` parity is untouched |
| `set` **idempotent** (same hash → no-op) | Backend retries are safe; re-anchoring breaks nothing |
| `set` **strict** (different hash → panic) | A batch cannot change its fingerprint: that is the integrity proof |
| `set` **not payable** | The contract handles no money; storage staking is covered by the contract account's balance |
| `LookupMap` (not `UnorderedMap`) | Only exact-key lookups are needed; the storage prefix is cheaper |

The 7 tests (`cargo test --release`) cover: store/read, unknown code → `None`, idempotency, rejection of a malformed hash, empty code, different hash for the same code and isolation between batches.

---

### 🚀 4. Scaling path

1. **Today (v0.06):** KV contract `codigo → hash` — one fingerprint per batch, state-based verification.
2. **Stage 2:** timeline events (harvest → classification → packing → dispatch) as index-anchored entries, without touching the batch hash.
3. **Stage 3:** token representation of crates/batches (NEAR FT/NFT) and scheduled payments to the producer.

[⬆ Back to top](#-contratos-inteligentes-en-near-por-qué-near-y-cómo-funciona-el-nuestro)

---

## 🇧🇷 Português

📑 **Conteúdo:** [🧩 1. O que o ecossistema oferece](#-1-o-que-o-ecossistema-near-oferece) · [✅ 2. Vantagens](#-2-vantagens-da-near-para-o-agrochain) · [🥚 3. O contrato do AgroChain](#-3-o-contrato-do-agrochain-rural) · [🚀 4. Rota de escala](#-4-rota-de-escala)

---

### 🧩 1. O que o ecossistema NEAR oferece

A NEAR executa contratos inteligentes escritos em **Rust** (ou AS/JS) e compilados para **WebAssembly (Wasm)**, sobre contas com nome legível. O ecossistema entrega ferramentas oficiais prontas:

| Ferramenta | Para que serve |
| :--- | :--- |
| **near-sdk (Rust)** | Escrever, testar e depurar contratos; macros `#[near]` |
| **cargo + rustup** | Build e testes unitários com o mesmo fluxo do Rust (`wasm32-unknown-unknown`) |
| **JSON-RPC** | Invocar métodos (`query` / `call_function`), ler estado e enviar transações |
| **near-kit (Python)** | Cliente de alto nível com que o backend FastAPI assina `set` e lê `get` |
| **Faucet da Testnet** | Cria e financia contas de teste (10 NEAR) via `helper.nearprotocol.com` |
| **Explorador** | `explorer.testnet.near.org`: transações, contrato e estado legível |

---

### ✅ 2. Vantagens da NEAR para o AgroChain

1. **Estado persistente, não só transações.** Um contrato NEAR tem *storage* próprio: `view get` responde sem depender do histórico do RPC (que guarda o detalhe das transações por ~36 h). Para uma impressão que precisa ser verificável meses depois, essa é a diferença-chave.
2. **Finalidade rápida (1–3 s).** Ideal no ponto de venda rural: o produtor ancora ao registrar e o consumidor verifica ao escanear.
3. **Custos baixos e previsíveis.** Ancorar custa ≈0,001 NEAR de *gas* + *storage staking* (~100 bytes por lote); o saldo da conta do contrato (faucet) cobre com sobra um piloto.
4. **Segurança por projeto (Rust + Wasm).** Rust elimina classes inteiras de bugs (memória, threads) antes de compilar; Wasm restringe o que um contrato pode executar.
5. **Contas com nome.** `agrochainrural.testnet` é legível e verificável no explorador: o piloto pode *mostrar* o seu contrato a um auditor sem explicar endereços hex.
6. **Testes sem rede.** Os 7 testes do contrato rodam com `cargo test` em segundos, sem tocar a Testnet nem gastar NEAR.
7. **Baixo consumo energético.** A NEAR é PoS com finalidade rápida; sem proof-of-work.

---

### 🥚 3. O contrato do AgroChain Rural

O contrato vive em `contract/src/lib.rs` (near-sdk 5.30, edition 2024) e o artefato implantável está versionado em `contract/res/agrochain_kv.wasm`. É deliberadamente pequeno — dois métodos:

```rust
pub struct AgroChainKv {
    /// codigo_do_lote → hash SHA-256 em hex.
    lotes: LookupMap<String, String>,
}

#[near]
impl AgroChainKv {
    /// Ancora o hash de um lote. Idempotente e não payable.
    pub fn set(&mut self, codigo: String, hash: String) { /* ... */ }

    /// Devolve o hash ancorado para um código, ou `None` se ainda não existe.
    pub fn get(&self, codigo: String) -> Option<String> { /* ... */ }
}
```

**Decisões de design:**

| Decisão | Por quê |
| :--- | :--- |
| Hash como **hex de 64 caracteres** (não `[u8; 32]`) | O `view get` devolve exatamente o string que o backend compara; a paridade `sha256.py` ↔ `hash.ts` não muda |
| `set` **idempotente** (mesmo hash → no-op) | Os retries do backend são seguros; reancorar não quebra nada |
| `set` **estrito** (hash diferente → panic) | Um lote não pode trocar de impressão: essa é a prova de integridade |
| `set` **não payable** | O contrato não mexe com dinheiro; o *storage staking* é coberto pelo saldo da conta do contrato |
| `LookupMap` (não `UnorderedMap`) | Só se consulta por chave exata; o prefixo de storage é mais barato |

Os 7 testes (`cargo test --release`) cobrem: gravar/ler, código desconhecido → `None`, idempotência, rejeição de hash malformado, código vazio, hash diferente para o mesmo código e isolamento entre lotes.

---

### 🚀 4. Rota de escala

1. **Hoje (v0.06):** contrato KV `codigo → hash` — uma impressão por lote, verificação por estado.
2. **Etapa 2:** eventos da linha do tempo (colheita → classificação → embalagem → despacho) como entradas ancoradas por índice, sem tocar o hash do lote.
3. **Etapa 3:** representação de caixas/lotes com tokens (NEAR FT/NFT) e pagamentos programados ao produtor.

[⬆ Voltar ao topo](#-contratos-inteligentes-en-near-por-qué-near-y-cómo-funciona-el-nuestro)
