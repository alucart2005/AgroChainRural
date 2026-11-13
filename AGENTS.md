# AGENTS.md

AgroChain Rural: trazabilidad de lotes de huevos de Finca Guarumo con SHA-256
anclado en un contrato KV de NEAR Testnet y QR por cubeta. Dos apps
independientes sin gestor de paquetes común: `frontend/` (Next.js 14, App
Router), `backend/` (FastAPI + SQLAlchemy) y el contrato Rust en `contract/`.
UI y términos de dominio en español (Colombia): *lote, cubeta, finca*. Ejecuta
los comandos dentro del subdirectorio correspondiente.

## Comandos

Frontend (`frontend/`):
- `npm install`
- `npm run dev` → http://localhost:3000
- `npm run lint`
- `npm run build` — también es la comprobación de tipos; no hay script `typecheck`. Luego `npm run start`.
- No hay ejecutor de tests: verificar con lint + build.

Backend (`backend/`, ejecutar desde ahí para que resuelvan los imports `app.*`):
- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- `.venv/bin/python -m pytest -q` — **84 tests**, todos con R2 y NEAR simulados (sin red, sin BD; el ID token de Google se simula)
- `uvicorn app.main:app --reload` — API en :8000
- `alembic upgrade head` — migra la base configurada en `DATABASE_URL`
- `python -m scripts.near_account create <cuenta.testnet>|show` — crea la cuenta con el faucet (imprime las líneas para `.env`) o la inspecciona
- `python -m scripts.desplegar_contrato` — despliega `contract/res/agrochain_kv.wasm` en `NEAR_CONTRACT_ID`
- `python -m scripts.anchor_demo` — ancla y verifica de verdad en Testnet (necesita las `NEAR_*`; crea una transacción real)
- `python -m scripts.reanclar [--listar]` — ancla los lotes que quedaron sin anclar
- `python -m scripts.migrar_sqlite_a_neon` — copia lotes del SQLite local a Neon y revalida los hashes
- Requiere Python ≥3.11 (`near-kit` lo exige; el Dockerfile ya usa 3.11).

Contrato (`contract/`, requiere `rustup` con `wasm32-unknown-unknown`):
- `cargo test --release` — tests unitarios (sin red; usa la feature `unit-testing`)
- `cargo build --release --target wasm32-unknown-unknown` — genera el wasm
- El artefacto desplegable se versiona en `contract/res/agrochain_kv.wasm`; `target/` está en `.gitignore`.

## Base de datos

SQLAlchemy 2 + Alembic. **Producción: Neon Postgres** (proyecto AgroChainRural,
región `aws-us-east-2`). **Desarrollo local: SQLite** (`agrotrace_local.db`,
ignorado por git) cuando `DATABASE_URL` está vacía — ver `app/db.py`.

La URL de Neon vive en `backend/.env.neon` (ignorado por git), **no** en
`.env`: así el día a día sigue usando SQLite y no se ensucian los datos reales.
El backend no la carga sola; se pasa a mano cuando hace falta:

```bash
DATABASE_URL="$(sed -n 's/^DATABASE_URL=//p' .env.neon)" alembic upgrade head
DATABASE_URL="$(sed -n 's/^DATABASE_URL=//p' .env.neon)" python -m scripts.migrar_sqlite_a_neon
```

En Render `DATABASE_URL` se fija en el panel (Settings → Environment) con el
endpoint **pooler** de Neon, no el directo.

Modelos (`app/models/lote.py`): `Lote` (codigo único `HUE-YYYY-NNN`,
fecha_cosecha, fecha_postura, linea_productiva, cantidad, unidad, finca,
municipio, `fotos` JSON con URLs de R2, `evidencias` JSON `[{nombre,tamano}]`,
hash_sha256, `near_tx_hash`/`near_block` (el ancla en NEAR), `usuario_id` FK
**nullable** (fuera del hash), created_at) y `Evento`
(tipo/fecha/descripcion, clave foránea a lote con `ON DELETE CASCADE`).
Las columnas `stellar_tx_hash`/`stellar_ledger` siguen en el modelo como
**archivo**: los lotes del piloto conservan su ancla original y no se leen ni
se escriben. Migración `0003_near` añade las dos columnas `near_*`.

Modelo `Usuario` (`app/models/usuario.py`, HU-06/HU-07): `google_sub` único,
email, nombre, foto_url y los 5 datos del primer ingreso (cedula, telefono,
finca, municipio); la propiedad `perfil_completo` marca si ya se diligenciaron.
Migración `0002_usuarios` (usa `batch_alter_table`: SQLite no admite ALTER de
constraints).

`lifespan` ejecuta `Base.metadata.create_all` y luego
`asegurar_columnas_sqlite()` (agrega a un SQLite ya existente las columnas que
`create_all` no añade a tablas viejas, p. ej. `lotes.usuario_id` y las
`lotes.near_*`); en Render las tablas las define Alembic (`alembic upgrade
head` en el CMD del Dockerfile) antes de arrancar, así que `create_all` queda
sin efecto.

> Ojo con el SQLite local: si la app ya creó `usuarios` con `create_all` pero
> `alembic_version` sigue en `0001_initial`, `alembic upgrade head` falla con
> `table usuarios already exists` (el `0002` intenta crearla de nuevo). Eso es
> preexistente y no afecta a producción; para migrar una base limpia usa un
> archivo recién creado.

## API (`app/api/`)

| Método | Ruta | Auth | HU |
|---|---|---|---|
| `GET` | `/api/health` | — | — |
| `POST` | `/api/auth/google` | ID token de Google | HU-06 |
| `GET` | `/api/auth/me` | Bearer JWT | HU-07 |
| `PUT` | `/api/auth/me` | Bearer JWT | HU-07 |
| `POST` | `/api/lotes` | Bearer JWT | HU-01 · HU-08 |
| `GET` | `/api/lotes` | — | HU-05 |
| `GET` | `/api/lotes/mios` | Bearer JWT | HU-08 |
| `GET` | `/api/lotes/{codigo}` | — | HU-02 |
| `GET` | `/api/lotes/{codigo}/eventos` | — | HU-05 |
| `POST` | `/api/lotes/{codigo}/eventos` | `X-API-Key` | HU-05 |
| `POST` | `/api/lotes/{codigo}/anclar` | `X-API-Key` | reintento de ancla |
| `GET` | `/api/verify/{codigo}` | — | HU-03 |
| `POST` | `/api/verify` | `X-API-Key` | auditoría de un ancla del contrato |

Dos mecanismos (`app/api/deps.py`): `require_productor` valida el **JWT** que
emite `POST /api/auth/google` (flujo Google Identity Services + `google-auth`) y
es obligatorio para **crear lotes** y ver `/api/lotes/mios`; `require_api_key`
queda solo para las escrituras internas sin usuario detrás (eventos, anclaje,
`POST /api/verify`). La `X-API-Key` es **pública** (va en el bundle JS), por eso
ya NO abre el registro de lotes. Las lecturas quedan abiertas para que el QR
funcione sin credenciales; si `API_KEY` está vacía, esos endpoints internos
quedan abiertos (desarrollo local).

`POST /api/verify` recibe `codigo` + `hash_hex` y dispara una consulta al
contrato: sin `X-API-Key` sería un proxy abierto y gratuito a la red de NEAR.
La ruta pública del consumidor sigue siendo `GET /api/verify/{codigo}`.

El QR **no** tiene endpoint propio: la etiqueta se genera en el navegador con
`qrcode.react` en `/lote/[id]/etiqueta` (HU-04).

### Paridad del hash (crítico)

`app/services/sha256.py` y `frontend/lib/hash.ts` deben producir el MISMO
SHA-256. El payload canónico son **exactamente 8 campos** (`CAMPOS_LOTE`):
`codigo`, `fecha_cosecha`, `linea_productiva`, `cantidad`, `unidad`, `finca`,
`municipio`, `evidencias`. `fecha_postura`, `fotos` (URLs de R2), hashes y
el ancla quedan FUERA a propósito.

`tests/test_sha256.py` fija vectores calculados con el código real del navegador;
si ese test falla, la verificación HU-03 se rompe en producción. **Cambiar un
lado obliga a recalcular los vectores con el otro.**

`tamano` en `evidencias` es el tamaño del data URL comprimido que envía el
cliente, no el del archivo original: es lo que viaja en el hash.

## NEAR (`app/services/near.py` + `contract/`)

El SHA-256 de cada lote se guarda como **hex de 64 caracteres** en un contrato
KV propio (`contract/res/agrochain_kv.wasm`, cuenta `NEAR_CONTRACT_ID`): mapa
`codigo → hash`. `set` es **no payable** (el *storage staking* lo cubre el
saldo de la cuenta del contrato) e **idempotente**: mismo hash → no-op, otro
hash para el mismo código → panic. `verify_anchor` lee con `view get`.

**Por qué el estado y no la transacción:** el RPC público de NEAR solo
conserva el detalle de las transacciones ~36 horas. Si la verificación
dependiera de buscar la transacción, un lote anclado la semana pasada quedaría
inverificable; el estado del contrato no caduca. Por eso la verificación HU-03
hace una triangulación de tres valores: el hash calculado en el navegador, el
guardado en la base y el devuelto por el contrato.

`anchor_hash` reintenta 3 veces ante fallos transitorios del RPC; un **panic
del contrato no se reintenta** (no hay nada que arreglar). El bloque que
incluyó la transacción es un dato presentacional: si no se resuelve se guarda
`None` y el ancla sigue siendo válida.

El ancla **no bloquea la existencia del registro**: si el RPC falla, el lote
queda guardado con `near_tx_hash = None` y se reintenta con
`POST /api/lotes/{codigo}/anclar` o con `python -m scripts.reanclar`.
Ten en cuenta que la llamada al RPC sí sincroniza dentro del handler de
`POST /api/lotes`.

## Frontend

Rutas: `/` (landing + buscador HU-05), `/login` (HU-06, botón Google Identity
Services + modo demo), `/productor/completar` (HU-07, 5 datos del primer
ingreso), `/productor` (HU-05 · HU-08), `/productor/nuevo`
(HU-01 · HU-08), `/productor/lote/[codigo]/eventos` (HU-05), `/lote/[id]`
(HU-02), `/lote/[id]/etiqueta` (HU-04).

`components/ProtegerProductor.tsx` envuelve las rutas `/productor/*`: sin token
válido (o con perfil incompleto, `exigirPerfil`) redirige a `/login` o
`/productor/completar`. Se resuelve en el **cliente** porque la sesión vive en
`localStorage` (`lib/auth.ts`) y un `middleware.ts` de Next no puede leerla.
`Nav.tsx` muestra "Iniciar sesión" o el avatar + "Salir" según la sesión.

`lib/api.ts` habla con el backend cuando `NEXT_PUBLIC_API_URL` está definida; si
no, o si el backend no responde, cae al **modo demo** (`lib/demoStore.ts`,
localStorage). Las lecturas silencian el fallo pero lo dejan marcado con
`modoDemoActivo()`, y las pantallas lo anuncian con `components/AvisoModoDemo`:
sin ese aviso, un backend caído se veía como datos reales. Las **escrituras NO**
tienen fallback demo: el error se muestra y no se crea ningún lote fantasma.

Un `404` del backend se trata como "el lote no existe" y NO busca en el
almacén local, para que un QR falso no parezca auténtico.

## Variables de entorno

`backend/.env` (gitignored; plantilla `backend/.env.example`): `NEAR_NETWORK`,
`NEAR_RPC_URL`, `NEAR_ACCOUNT_ID`, `NEAR_PRIVATE_KEY`, `NEAR_CONTRACT_ID`,
`FRONTEND_URL` (CORS), `R2_*`, `API_KEY`, `GOOGLE_CLIENT_ID`,
`GOOGLE_CLIENT_SECRET`, `AUTH_SECRET` (secreto con el que se firman los JWT:
`openssl rand -hex 32`; vacío → el login responde 503), y `DATABASE_URL`
**vacío** para que el desarrollo local use SQLite. `backend/.env.neon` guarda
la URL de producción (también gitignored); ver la sección de base de datos.

`Settings` usa `extra="ignore"`, así que un `.env` heredado de la época de
Stellar (`STELLAR_*`, `HORIZON_URL`) convive sin tumbar el arranque mientras
se renombra. La clave `NEAR_PRIVATE_KEY` es la de `NEAR_ACCOUNT_ID` (ed25519,
con su prefijo) y **solo** vive en `.env` y en el panel de Render: jamás se
sube al repositorio.

Las cuentas de testnet se crean con
`python -m scripts.near_account create <cuenta.testnet>` (faucet oficial,
10 NEAR) e imprime las dos líneas para pegar en `.env`.

`frontend/.env.local` (plantilla `frontend/.env.example`): `NEXT_PUBLIC_API_URL`,
`NEXT_PUBLIC_API_KEY`, `NEXT_PUBLIC_SITE_URL`, `NEXT_PUBLIC_GOOGLE_CLIENT_ID`
(mismo Client ID que el backend, pero solo la parte pública: el popup de Google
no lleva secreto; vacío → `/login` muestra el aviso de no configurado y ofrece
el modo demo).

**`NEXT_PUBLIC_API_URL` va SIN sufijo `/api`** (`http://localhost:8000`,
`https://agrochain-backend-f89w.onrender.com`). `lib/api.ts` concatena rutas que ya
empiezan por `/api/`; un sufijo produce `/api/api/lotes` → 404 y el frontend
cae en modo demo sin avisar.

Todo lo prefijado con `NEXT_PUBLIC_` se embebido en el JavaScript servido al
navegador: `NEXT_PUBLIC_API_KEY` es **pública**, no un secreto.

## Despliegue

> **Infraestructura propia de `AgroChainRural` (provisionada 2026-11-13).**
> La infraestructura del repo original `AgroTraceRural` (Render
> `agrotrace-backend-z3q1`, Vercel `frontend-2mx1`, Neon `agrotrace`, R2
> `agrotrace-evidence`) es **independiente y no se toca**: aquí hay copias
> nuevas y vacías, sin migración de datos.

- **Base de datos → Neon**, proyecto `AgroChainRural`
  (`broad-butterfly-52434898`, `aws-us-east-2`), rama `br-odd-sun-bem5k9ti`,
  base `neondb`, PostgreSQL 18. En Render va la URI **del pooler** (termina en
  `-pooler`); para migraciones a mano, la URI **directa**. Esquema en `0003_near`
  (4 tablas; `lotes` con 18 columnas, incluidas `near_tx_hash` y `near_block`).
- **Backend → Render** (Web Service + Docker, `render.yaml`). NO Vercel: las
  funciones de Vercel se cortan a los 10 s y su filesystem es efímero.
  Servicio `agrochain-backend` (`srv-dbr7r45ckfvc73dfps40`), región Oregon,
  plan free, `healthCheckPath=/api/health`
  → `https://agrochain-backend-f89w.onrender.com`.
  Render despliega desde `main`; el CMD del Dockerfile migra antes de servir
  (log esperado al arrancar: `Context impl PostgresqlImpl`).
  11 variables de entorno en el panel (API REST:
  `PUT /v1/services/{id}/env-vars` **reemplaza la lista completa**).
- **Frontend → Vercel**, proyecto `agrochain-frontend`
  (`prj_vdHS8cb0seFR8qpmvtQUwxQK8uKJ`), Root Directory `frontend`, enlazado a
  este repo (`main`) → `https://agrochain-frontend-kappa.vercel.app`.
  Variables de producción: `NEXT_PUBLIC_API_URL` (la de Render, **sin** sufijo
  `/api`), `NEXT_PUBLIC_API_KEY`, `NEXT_PUBLIC_SITE_URL` y
  `NEXT_PUBLIC_GOOGLE_CLIENT_ID`. Cambiarlas obliga a **redeploy**: Next
  las inlina en el bundle durante el build. **Ojo**: `agrochain-frontend.vercel.app`
  (sin sufijo) es otro proyecto ajeno, no usarlo.
- **Evidencia → Cloudflare R2**, bucket `agrochain-evidence` (pendiente de
  crear con un token con permisos R2). La producción vieja usa
  `agrotrace-evidence` y **no se toca**.
- El frontend llama al backend **directamente** con `NEXT_PUBLIC_API_URL` y el
  backend permite el origen con `FRONTEND_URL`. **No hay `vercel.json`**: Vercel
  no interpola variables de entorno dentro de ese fichero, así que un rewrite
  con `${BACKEND_URL}` nunca funcionó y solo duplicaba la URL en dos sitios.
- **Cuenta y contrato de NEAR:** `render.yaml` declara `NEAR_NETWORK`,
  `NEAR_RPC_URL`, `NEAR_ACCOUNT_ID`, `NEAR_PRIVATE_KEY` y `NEAR_CONTRACT_ID`
  con `sync: false` (se completan en el panel). La clave secreta nunca viaja
  al repositorio.

## Convenciones

- Commits cortos y prefijados (`feat:`, `fix:`, `docs:`, `chore:`); hacer push
  **solo bajo petición explícita**.
- Documentación trilingüe (ES / EN / PT) siguiendo el patrón de
  `docs/semana2/KanbanBacklog.md`.
- Producto piloto: huevos de Finca Guarumo, Cáceres (Antioquia). Código de
  lote `HUE-YYYY-NNN`, secuencial por año.
- Las 23 historias viven en `docs/backlog/` — `IssuesListos.md` (HU-01..HU-05,
  español), `BacklogAuthGoogle.md` (HU-06..HU-08),
  `BacklogInfraProduccion.md` (HU-09..HU-13), `BacklogEstabilidadBackend.md`
  (HU-14..HU-15) y `BacklogRedisenoVisual.md` (HU-16..HU-23), las cuatro
  últimas trilingües — y en GitHub Issues #1..#23. El tablero es el
  [proyecto #14](https://github.com/users/alucart2005/projects/14), con
  roadmap de 5 entregas (milestones cerrados) y `Priority`/`Size`/fechas
  reales por historia.
