# 📦 Documentación semanal 3 (MVP)

> **Proyecto:** AgroChain Rural · **Carpeta:** `frontend/` (Next.js 14 · App Router · TypeScript · Tailwind) · **Deploy:** Vercel
>
> 🌐 **¡App en línea!** [https://frontend-2mx1.vercel.app](https://frontend-2mx1.vercel.app)

> 🌐 **Idioma / Language:** [🇪🇸 Español](#-español) · [🇺🇸 English](#-english) · [🇧🇷 Português](#-português)

---

## 🇪🇸 Español

📑 **Contenido:** [🖥️ 1. Front construido](#-1-front-construido) · [⚓ 2. Decisión técnica](#-2-decisión-técnica) · [👥 3. Participación del equipo](#-3-participación-del-equipo) · [🚧 4. Bloqueos y siguiente paso](#-4-bloqueos-y-siguiente-paso)

---

### 🖥️ 1. Front construido

🌐 **La aplicación está desplegada y es usable desde cualquier dispositivo: [https://frontend-2mx1.vercel.app](https://frontend-2mx1.vercel.app)**

#### Stack y arquitectura

El frontend está construido con **Next.js 14 (App Router)**, **TypeScript** y **Tailwind CSS**, con `qrcode.react` para la generación de códigos QR. Es una aplicación de página única con rutas server-side y renderizado estático, apta para el consumo móvil en la finca (conexión Starlink) y en el punto de venta.

Todas las pantallas hablan con una capa de datos única (`lib/api.ts`), que decide la fuente en tiempo de ejecución: si existe `NEXT_PUBLIC_API_URL` hace `fetch` al backend FastAPI; si no, activa el **modo demo** con datos de ejemplo persistidos en `localStorage`. Esto permite recorrer todo el flujo del MVP en el navegador sin backend configurado — y es como está funcionando hoy la versión en producción de Vercel.

#### Pantallas implementadas y su vínculo con el Blueprint

| Ruta | Historia (Blueprint) | Qué implementa |
| :--- | :--- | :--- |
| `/` | — | Landing con el flujo de trazabilidad en 4 pasos: producción → evidencia → hash → QR → cliente. |
| `/productor` | HU-01 · HU-05 | Lista de lotes registrados con acceso a la página pública y a la etiqueta QR. |
| `/productor/nuevo` | HU-01 | Formulario de registro del productor: código del lote, fecha de cosecha, línea productiva, cantidad y **foto obligatoria**. El botón de guardado queda bloqueado sin evidencia fotográfica — regla del MVP. |
| `/lote/[id]` | HU-02 · HU-03 · HU-05 | Página pública de consulta (la que abre el consumidor tras escanear el QR): origen, finca, municipio, fecha, fotos del lote, botón **"Verificar integridad"** e historial cronológico de eventos. |
| `/lote/[id]/etiqueta` | HU-04 | Etiqueta imprimible con QR único por cubeta (ej. `HUE-2027-001`), lista para pegar al empaque físico mediante `window.print()`. |
| `/lote/NOEXISTE` | HU-02 (esc. 2) | Pantalla de alerta "Lote no encontrado / código no auténtico" ante códigos falsos o manipulados. |

Las cinco historias de usuario del Blueprint quedan cubiertas de extremo a extremo: el productor registra la cubeta de huevos (HU-01), el sistema le asigna un lote con evidencias (HU-02), la huella SHA-256 se guarda en el contrato KV de NEAR y se puede verificar (HU-03), la etiqueta QR física se imprime desde la app (HU-04) y el comprador consulta el historial del lote (HU-05).

#### Verificación de integridad (HU-03)

`lib/hash.ts` implementa la misma convención que el backend: **JSON canónico** (claves ordenadas, sin `undefined`) → **SHA-256** vía Web Crypto → hex de 64 caracteres. El payload incluye `codigo, fecha_cosecha, linea_productiva, cantidad, unidad, finca, municipio` y metadatos de las evidencias (`nombre`, `tamano`) — **nunca los bytes de la foto** (regla de oro: los archivos pesados quedan fuera de la blockchain). El botón "Verificar ahora" recalcula el hash desde los datos actuales y el backend lo contrasta con el estado del contrato de NEAR: coincide → insignia verde con `tx_hash` enlazado al explorador de NEAR Testnet; no coincide → alerta roja de alteración.

#### Flujo completo de prueba (lote semilla `HUE-2026-008`)

1. Abrir `/productor/nuevo`, llenar el formulario y adjuntar foto → se crea el lote.
2. Ir a `/lote/{id}/etiqueta`, imprimir la etiqueta con QR → se pega a la cubeta.
3. Escanear el QR (o abrir el enlace) en `/lote/{id}` → el consumidor ve origen, fotos e historial.
4. Pulsar "Verificar integridad" → resultado verde con transacción enlazada en el explorador de NEAR.

Este flujo fue validado con **pruebas E2E automatizadas (Playwright + Chromium): 10/10 verificaciones exitosas**, incluyendo bloqueo sin foto, creación del lote `HUE-2026-001`, verificación verde, etiqueta QR y pantalla 404.

#### Despliegue

El proyecto está desplegado en **Vercel** (proyecto `frontend`, Root Directory `frontend`, framework Next.js auto-detectado). **No hay `vercel.json`**: el frontend llama al backend **directamente** con `NEXT_PUBLIC_API_URL` (sin sufijo `/api`) y, si no responde o no está definida, opera el modo demo. Cada push a `main` genera un nuevo deployment de producción y cada pull request genera un preview aislado.

---

### ⚓ 2. Decisión técnica

**Pregunta:** ¿cómo anclar las huellas SHA-256 del MVP en blockchain?

| Opción | Qué es | Estado |
| :--- | :--- | :--- |
| **A** | **Contrato KV propio en NEAR Testnet** (`contract/`, Rust + near-sdk): mapa `codigo → hash` con `set` idempotente y lectura `view get` | ✅ **Elegida** (v0.06) |
| **B** | Solo argumentos de la transacción, sin contrato (el hash viaja pero no queda en estado consultable) | Descartada |
| — | *(Histórico)* Las versiones 0.01–0.05 anclaban con transacción clásica + Memo Hash en Stellar Testnet | Reemplazada |

**Decisión: Opción A.** El MVP necesita una sola cosa de la blockchain: **probar que la huella de un lote existió en un momento dado y no fue alterada después**. Eso exige que el dato siga siendo consultable mucho después — y el RPC público de NEAR solo conserva el **detalle** de las transacciones ~36 horas. El estado del contrato, en cambio, no caduca: `view get` responde hoy igual que en un año. El contrato además fija las reglas del ancla: reintentar el mismo hash es un no-op (reanclar es seguro) y un hash distinto para el mismo lote hace panic (el lote no puede cambiar de huella). Cada ancla cuesta ≈0,001 NEAR de *gas* + *storage staking* (~100 bytes), cubierto de sobra por el saldo de la cuenta del contrato.

**Qué se descartó y por qué:** (1) **La Opción B (solo argumentos de la transacción)** — el hash viajaría, pero la verificación dependería del histórico del RPC, que expura: un lote anclado la semana pasada quedaría inverificable. (2) **Almacenar fotos/videos en blockchain** — viola la regla de oro del `ProductBlueprint.md` §8 (los archivos pesados quedan en almacenamiento externo; solo viaja el hash), encarecería cada lote y expondría información sensible. (3) **Otras cadenas** — NEAR cumplió los criterios del piloto: estado persistente consultable, finalidad de 1–3 segundos, costos mínimos y predecibles, cuentas con nombre legible (`agrochainrural.testnet`) y SDK oficial para Python (`near-kit`).

---

### 👥 3. Participación del equipo

| Integrante | GitHub | Aporte en este entregable |
| :--- | :--- | :--- |
| **Napoleon de Jesus Anaya Romero** | `alucart2005` | Construcción del frontend (Next.js), backend de anclaje (FastAPI), scripts, tests, documentación trilingüe, despliegue en Vercel y MCPs del proyecto. Commits: `1e08f05`, `8cc4002`, `e92ef10`, `5769363`. |
| **Cristian Esteban Jiménez Durango** | `CristianEstebanJimenezDurango` | Propuso la HU-03 (verificación de integridad con huella SHA-256 en blockchain) — la historia diferenciadora del MVP. |
| **Jefferson Cabrera** | *pendiente de confirmar* | Propuso la HU-04 (etiqueta QR única por cubeta que conecta el empaque físico con el registro digital). |
| **Diego Martínez** | *pendiente de confirmar* | Propuso la HU-05 (historial de eventos del lote para validar frescura por parte del comprador local). |

---

### 🚧 4. Bloqueos y siguiente paso

**Bloqueos actuales:**

- El **backend (FastAPI) aún no está desplegado** en la nube (Railway/Render); el frontend opera en modo demo con datos locales.
- **Base de datos no conectada:** falta crear la instancia (Neon/PostgreSQL) y definir `DATABASE_URL`.
- **Faltan commits de los compañeros** esta semana (Cristian, Jefferson y Diego aún no han aportado al repositorio).
- `docs/semana3/StackTecnologico.md` sigue pendiente.

**Próximo paso hacia el MVP:** desplegar el backend en Railway/Render con las variables de entorno de NEAR Testnet (`NEAR_*`), conectar `NEXT_PUBLIC_API_URL` en Vercel para salir del modo demo y registrar los primeros lotes reales con anclaje on-chain verificable.

[⬆ Volver al inicio](#-documentación-semanal-3-mvp)

---

## 🇺🇸 English

📑 **Contents:** [💻 1. Frontend built](#-1-frontend-built) · [⚓ 2. Technical decision](#-2-technical-decision) · [👥 3. Team participation](#-3-team-participation) · [🚧 4. Blockers and next step](#-4-blockers-and-next-step)

---

### 💻 1. Frontend built

🌐 **The application is deployed and usable from any device: [https://frontend-2mx1.vercel.app](https://frontend-2mx1.vercel.app)**

#### Stack and architecture

The frontend is built with **Next.js 14 (App Router)**, **TypeScript** and **Tailwind CSS**, plus `qrcode.react` for QR code generation. It is a single-page application with server-side routes and static rendering, suitable for mobile use on the farm (Starlink connection) and at the point of sale.

Every screen talks to a single data layer (`lib/api.ts`), which picks the source at runtime: if `NEXT_PUBLIC_API_URL` exists it `fetch`es the FastAPI backend; otherwise it activates **demo mode** with sample data persisted in `localStorage`. This lets the whole MVP flow run in the browser with no backend configured — and that is exactly how today's Vercel production version works.

#### Screens implemented and their Blueprint link

| Route | Story (Blueprint) | What it implements |
| :--- | :--- | :--- |
| `/` | — | Landing page with the 4-step traceability flow: production → evidence → hash → QR → customer. |
| `/productor` | HU-01 · HU-05 | List of registered batches with links to the public page and the QR label. |
| `/productor/nuevo` | HU-01 | Farmer registration form: batch code, harvest date, production line, quantity and **mandatory photo**. The save button stays blocked without photographic evidence — an MVP rule. |
| `/lote/[id]` | HU-02 · HU-03 · HU-05 | Public lookup page (the one the customer opens after scanning the QR): origin, farm, municipality, date, batch photos, the **"Verify integrity"** button and the chronological event history. |
| `/lote/[id]/etiqueta` | HU-04 | Printable label with a unique QR per crate (e.g. `HUE-2027-001`), ready to stick on the physical package via `window.print()`. |
| `/lote/NOEXISTE` | HU-02 (sc. 2) | "Batch not found / code not authentic" alert screen for fake or tampered codes. |

All five Blueprint user stories are covered end to end: the farmer registers the egg crate (HU-01), the system assigns it a batch with evidence (HU-02), the SHA-256 fingerprint is stored in the NEAR KV contract and can be verified (HU-03), the physical QR label is printed from the app (HU-04) and the buyer looks up the batch history (HU-05).

#### Integrity verification (HU-03)

`lib/hash.ts` implements the same convention as the backend: **canonical JSON** (sorted keys, no `undefined`) → **SHA-256** via Web Crypto → 64-char hex. The payload includes `codigo, fecha_cosecha, linea_productiva, cantidad, unidad, finca, municipio` and evidence metadata (`nombre`, `tamano`) — **never the photo bytes** (golden rule: heavy files stay off-chain). The "Verify now" button recomputes the hash from current data and the backend contrasts it with the NEAR contract state: match → green badge with `tx_hash` linked to the NEAR Testnet explorer; mismatch → red tamper alert.

#### Full test flow (seed batch `HUE-2026-008`)

1. Open `/productor/nuevo`, fill the form and attach a photo → the batch is created.
2. Go to `/lote/{id}/etiqueta`, print the QR label → stick it on the crate.
3. Scan the QR (or open the link) at `/lote/{id}` → the customer sees origin, photos and history.
4. Click "Verify integrity" → green result with the transaction linked in the NEAR explorer.

This flow was validated with **automated E2E tests (Playwright + Chromium): 10/10 successful checks**, including photo-blocking, creation of batch `HUE-2026-001`, green verification, QR label and the 404 screen.

#### Deployment

The project is deployed on **Vercel** (project `frontend`, Root Directory `frontend`, auto-detected Next.js framework). **There is no `vercel.json`**: the frontend calls the backend **directly** through `NEXT_PUBLIC_API_URL` (no `/api` suffix); if it is missing or down, demo mode takes over. Each push to `main` generates a new production deployment and each pull request generates an isolated preview.

---

### ⚓ 2. Technical decision

**Question:** how does the MVP anchor its SHA-256 fingerprints on a blockchain?

| Option | What it is | Status |
| :--- | :--- | :--- |
| **A** | **Own KV contract on NEAR Testnet** (`contract/`, Rust + near-sdk): a `codigo → hash` map with an idempotent `set` and a `view get` read | ✅ **Chosen** (v0.06) |
| **B** | Only transaction arguments, no contract (the hash travels but stays in no queryable state) | Discarded |
| — | *(Historical)* versions 0.01–0.05 anchored with a classic transaction + Memo Hash on Stellar Testnet | Replaced |

**Decision: Option A.** The MVP needs exactly one thing from the blockchain: **to prove that a batch fingerprint existed at a given time and was not altered afterwards**. That requires the data to stay queryable long after — and NEAR's public RPC keeps **transaction detail** for only ~36 hours. Contract state, in contrast, does not expire: `view get` answers today the same as in a year. The contract also pins the anchor rules: retrying the same hash is a no-op (re-anchoring is safe) and a different hash for the same batch panics (a batch cannot change its fingerprint). Each anchor costs ≈0.001 NEAR of *gas* + storage staking (~100 bytes), easily covered by the contract account's balance.

**What was discarded and why:** (1) **Option B (transaction arguments only)** — the hash would travel, but verification would depend on the RPC history, which is pruned: a batch anchored last week would become unverifiable. (2) **Storing photos/videos on-chain** — it breaks the golden rule of `ProductBlueprint.md` §8 (heavy files stay in external storage; only the hash travels), would make every batch expensive and would expose sensitive information. (3) **Other chains** — NEAR met the pilot's criteria: queryable persistent state, 1–3 second finality, minimal predictable costs, human-readable accounts (`agrochainrural.testnet`) and an official Python SDK (`near-kit`).

---

### 👥 3. Team participation

| Member | GitHub | Contribution in this deliverable |
| :--- | :--- | :--- |
| **Napoleon de Jesus Anaya Romero** | `alucart2005` | Frontend build (Next.js), anchoring backend (FastAPI), scripts, tests, trilingual documentation, Vercel deployment and project MCPs. Commits: `1e08f05`, `8cc4002`, `e92ef10`, `5769363`. |
| **Cristian Esteban Jiménez Durango** | `CristianEstebanJimenezDurango` | Proposed HU-03 (integrity verification with a SHA-256 fingerprint on a blockchain) — the MVP's differentiating story. |
| **Jefferson Cabrera** | *pending confirmation* | Proposed HU-04 (unique QR label per crate linking the physical package to the digital record). |
| **Diego Martínez** | *pending confirmation* | Proposed HU-05 (batch event history so the local buyer can validate freshness). |

---

### 🚧 4. Blockers and next step

**Current blockers:**

- The **FastAPI backend is not yet deployed** in the cloud (Railway/Render); the frontend runs in demo mode with local data.
- **No database connected:** the instance (Neon/PostgreSQL) still needs to be created and `DATABASE_URL` defined.
- **Teammates' commits are missing** this week (Cristian, Jefferson and Diego have not contributed to the repository yet).
- `docs/semana3/StackTecnologico.md` is still pending.

**Next step toward the MVP:** deploy the backend on Railway/Render with the NEAR Testnet environment variables (`NEAR_*`), connect `NEXT_PUBLIC_API_URL` on Vercel to leave demo mode, and register the first real batches with verifiable on-chain anchoring.

[⬆ Back to top](#-documentación-semanal-3-mvp)

---

## 🇧🇷 Português

📑 **Conteúdo:** [💻 1. Frontend construído](#-1-frontend-construído) · [⚓ 2. Decisão técnica](#-2-decisão-técnica) · [👥 3. Participação da equipe](#-3-participação-da-equipe) · [🚧 4. Bloqueios e próximo passo](#-4-bloqueios-e-próximo-passo)

---

### 💻 1. Frontend construído

🌐 **O aplicativo está implantado e utilizável de qualquer dispositivo: [https://frontend-2mx1.vercel.app](https://frontend-2mx1.vercel.app)**

#### Stack e arquitetura

O frontend foi construído com **Next.js 14 (App Router)**, **TypeScript** e **Tailwind CSS**, além de `qrcode.react` para geração de códigos QR. É uma aplicação de página única com rotas server-side e renderização estática, adequada para uso móvel na fazenda (conexão Starlink) e no ponto de venda.

Todas as telas falam com uma camada única de dados (`lib/api.ts`), que escolhe a fonte em tempo de execução: se existir `NEXT_PUBLIC_API_URL`, faz `fetch` ao backend FastAPI; caso contrário, ativa o **modo demo** com dados de exemplo persistidos em `localStorage`. Isso permite percorrer todo o fluxo do MVP no navegador sem backend configurado — e é exatamente como funciona hoje a versão de produção no Vercel.

#### Telas implementadas e sua ligação com o Blueprint

| Rota | História (Blueprint) | O que implementa |
| :--- | :--- | :--- |
| `/` | — | Landing com o fluxo de rastreabilidade em 4 etapas: produção → evidência → hash → QR → cliente. |
| `/productor` | HU-01 · HU-05 | Lista de lotes registrados com acesso à página pública e à etiqueta QR. |
| `/productor/nuevo` | HU-01 | Formulário de registro do produtor: código do lote, data da colheita, linha produtiva, quantidade e **foto obrigatória**. O botão de salvar fica bloqueado sem evidência fotográfica — regra do MVP. |
| `/lote/[id]` | HU-02 · HU-03 · HU-05 | Página pública de consulta (aquela que o cliente abre após escanear o QR): origem, fazenda, município, data, fotos do lote, botão **"Verificar integridade"** e histórico cronológico de eventos. |
| `/lote/[id]/etiqueta` | HU-04 | Etiqueta imprimível com QR único por caixa (ex.: `HUE-2027-001`), pronta para colar no embalagem físico via `window.print()`. |
| `/lote/NOEXISTE` | HU-02 (esc. 2) | Tela de alerta "Lote não encontrado / código não autêntico" para códigos falsos ou adulterados. |

As cinco histórias de usuário do Blueprint estão cobertas de ponta a ponta: o produtor registra a caixa de ovos (HU-01), o sistema atribui um lote com evidências (HU-02), a impressão SHA-256 é guardada no contrato KV de NEAR e pode ser verificada (HU-03), a etiqueta QR física é impressa pelo app (HU-04) e o comprador consulta o histórico do lote (HU-05).

#### Verificação de integridade (HU-03)

`lib/hash.ts` implementa a mesma convenção do backend: **JSON canônico** (chaves ordenadas, sem `undefined`) → **SHA-256** via Web Crypto → hex de 64 caracteres. O payload inclui `codigo, fecha_cosecha, linea_productiva, cantidad, unidad, finca, municipio` e metadados das evidências (`nombre`, `tamano`) — **nunca os bytes da foto** (regra de ouro: arquivos pesados ficam fora da blockchain). O botão "Verificar agora" recalcula o hash dos dados atuais e o backend o compara com o estado do contrato da NEAR: coincide → selo verde com `tx_hash` linkado ao explorador da NEAR Testnet; não coincide → alerta vermelho de adulteração.

#### Fluxo completo de teste (lote semente `HUE-2026-008`)

1. Abrir `/productor/nuevo`, preencher o formulário e anexar foto → o lote é criado.
2. Ir em `/lote/{id}/etiqueta`, imprimir a etiqueta QR → colar na caixa.
3. Escanear o QR (ou abrir o link) em `/lote/{id}` → o cliente vê origem, fotos e histórico.
4. Clicar em "Verificar integridade" → resultado verde com a transação linkada no explorador da NEAR.

Esse fluxo foi validado com **testes E2E automatizados (Playwright + Chromium): 10/10 verificações bem-sucedidas**, incluindo bloqueio sem foto, criação do lote `HUE-2026-001`, verificação verde, etiqueta QR e a tela 404.

#### Implantação

O projeto está implantado no **Vercel** (projeto `frontend`, Root Directory `frontend`, framework Next.js detectado automaticamente). **Não há `vercel.json`**: o frontend chama o backend **diretamente** com `NEXT_PUBLIC_API_URL` (sem sufixo `/api`); se não houver resposta, o modo demo assume. Cada push em `main` gera um novo deployment de produção e cada pull request gera um preview isolado.

---

### ⚓ 2. Decisão técnica

**Pergunta:** como ancorar as impressões SHA-256 do MVP em blockchain?

| Opção | O que é | Status |
| :--- | :--- | :--- |
| **A** | **Contrato KV próprio na NEAR Testnet** (`contract/`, Rust + near-sdk): mapa `codigo → hash` com `set` idempotente e leitura `view get` | ✅ **Escolhida** (v0.06) |
| **B** | Só argumentos da transação, sem contrato (a impressão viaja, mas não fica em estado consultável) | Descartada |
| — | *(Histórico)* as versões 0.01–0.05 ancoravam com transação clássica + Memo Hash na Stellar Testnet | Substituída |

**Decisão: Opção A.** O MVP precisa de uma única coisa da blockchain: **provar que a impressão de um lote existiu em um momento dado e não foi alterada depois**. Isso exige que o dado continue consultável muito tempo depois — e o RPC público da NEAR guarda o **detalhe** das transações por apenas ~36 horas. O estado do contrato, em troca, não caduca: `view get` responde hoje igual como daqui a um ano. O contrato também fixa as regras da âncora: repetir o mesmo hash é um no-op (reancorar é seguro) e um hash diferente para o mesmo lote faz panic (o lote não pode trocar de impressão). Cada âncora custa ≈0,001 NEAR de *gas* + *storage staking* (~100 bytes), coberto com sobra pelo saldo da conta do contrato.

**O que foi descartado e por quê:** (1) **A Opção B (só argumentos da transação)** — a impressão viajaria, mas a verificação dependeria do histórico do RPC, que é expurgado: um lote ancorado na semana passada ficaria inverificável. (2) **Armazenar fotos/vídeos na blockchain** — quebra a regra de ouro do `ProductBlueprint.md` §8 (arquivos pesados ficam em armazenamento externo; só viaja o hash), encareceria cada lote e exporia informações sensíveis. (3) **Outras cadeias** — a NEAR cumpriu os critérios do piloto: estado persistente consultável, finalidade de 1–3 segundos, custos mínimos e previsíveis, contas com nome legível (`agrochainrural.testnet`) e SDK oficial para Python (`near-kit`).

---

### 👥 3. Participação da equipe

| Integrante | GitHub | Aporte nesta entrega |
| :--- | :--- | :--- |
| **Napoleon de Jesus Anaya Romero** | `alucart2005` | Construção do frontend (Next.js), backend de ancoragem na Stellar (FastAPI), scripts, testes, documentação trilingue, implantação no Vercel e MCPs do projeto. Commits: `1e08f05`, `8cc4002`, `e92ef10`, `5769363`. |
| **Cristian Esteban Jiménez Durango** | `CristianEstebanJimenezDurango` | Propôs a HU-03 (verificação de integridade com impressão SHA-256 na Stellar) — a história diferenciadora do MVP. |
| **Jefferson Cabrera** | *pendente de confirmação* | Propôs a HU-04 (etiqueta QR única por caixa que conecta o embalagem físico ao registro digital). |
| **Diego Martínez** | *pendente de confirmação* | Propôs a HU-05 (histórico de eventos do lote para o comprador local validar a frescura). |

---

### 🚧 4. Bloqueios e próximo passo

**Bloqueios atuais:**

- O **backend (FastAPI) ainda não está implantado** na nuvem (Railway/Render); o frontend opera em modo demo com dados locais.
- **Banco de dados não conectado:** falta criar a instância (Neon/PostgreSQL) e definir `DATABASE_URL`.
- **Faltam commits dos colegas** nesta semana (Cristian, Jefferson e Diego ainda não contribuíram no repositório).
- `docs/semana3/StackTecnologico.md` segue pendente.

**Próximo passo rumo ao MVP:** implantar o backend no Railway/Render com as variáveis de ambiente da Stellar Testnet, conectar `NEXT_PUBLIC_API_URL` e `BACKEND_URL` no Vercel para sair do modo demo e registrar os primeiros lotes reais com ancoragem on-chain verificável.

[⬆ Voltar ao topo](#-documentación-semanal-3-mvp)
