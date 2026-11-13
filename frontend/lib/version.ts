/**
 * Versión y datos de la aplicación (fuente única).
 *
 * Se muestra en el pie de página, en el índice de ayuda y en «Acerca de».
 * Si se cambia la versión, se actualizan también `package.json` y la página
 * de novedades (`/ayuda/versiones`).
 */

export const VERSION = "0.6.0";
export const CICLO = "Version-0.06";
export const FECHA_LANZAMIENTO = "2026-11-11";

export const ENLACES = {
  app: "https://agrochain-frontend-kappa.vercel.app",
  api: "https://agrochain-backend-f89w.onrender.com",
  repositorio: "https://github.com/alucart2005/AgroChainRural",
  video: "https://www.youtube.com/watch?v=stVQCivrmCg",
  // Explorador de NEAR Testnet: el ancla se consulta por el ESTADO del
  // contrato, y la transacción que lo escribió se ve aquí.
  red: "https://explorer.testnet.near.org",
  correo: "soporte@agrotrace.co",
};

/** Novedades de cada ciclo, tal como quedaron en el historial de git. */
export const NOVEDADES = [
  {
    version: "0.6.0",
    ciclo: "Version-0.06",
    fecha: "2026-11-11",
    titulo: "El ancla se mueve de Stellar a NEAR",
    cambios: [
      "El SHA-256 de cada lote se guarda ahora en un contrato propio de NEAR Testnet en lugar del memo de una transacción de Stellar.",
      "La verificación lee el estado del contrato: el detalle de las transacciones caduca en el RPC público, el estado no.",
      "La ficha enlaza la transacción en el explorador de NEAR y muestra el bloque en lugar del ledger.",
      "Nuevo contrato KV en Rust (contract/) con reintentos idempotentes: repetir un ancla no cambia nada y un hash distinto para el mismo lote se rechaza.",
    ],
  },
  {
    version: "0.5.0",
    ciclo: "Version-0.05",
    fecha: "2026-11-09",
    titulo: "Ayuda, manual de usuario y versión visible",
    cambios: [
      "Menú de ayuda con manual de usuario trilingüe (es/en/pt), novedades, acerca de y reporte de problemas.",
      "La versión de la aplicación se muestra en el pie de página y en las páginas de ayuda.",
      "Rediseño de la etiqueta QR: tamaño proporcional y centrado, verificado como escaneable.",
    ],
  },
  {
    version: "0.4.0",
    ciclo: "Version-0.04",
    fecha: "2026-11-09",
    titulo: "Rediseño de la interfaz y navegación con submenús",
    cambios: [
      "Nuevo sistema visual «El libro de la finca»: tipografías Fraunces y Archivo, paleta esmeralda por variables CSS y filetes en lugar de tarjetas idénticas.",
      "Menú con submenús real para Inicio, Consulta, Lotes, Catálogo y Configuración, compartido por el sidebar y el panel móvil.",
      "Registro de lote en tres pasos (Datos, Evidencias, Resumen) con panel de fotos, cámara y resumen previo.",
      "Páginas nuevas: catálogo de productos, galería de evidencias y configuración del perfil.",
      "Ficha del lote con banner de verificación, carrusel de fotos, filas con iconos y grid de evidencias.",
      "Modo oscuro completo en toda la aplicación, con conmutador y sin destello al cargar.",
      "Inicio reequilibrado en celular y pie de página compacto a dos columnas.",
    ],
  },
  {
    version: "0.3.0",
    ciclo: "Version-0.03",
    fecha: "2026-11-09",
    titulo: "El lote de ejemplo pasa a ser un lote real",
    cambios: [
      "«Lote demo» ahora es el lote HUE-2026-008: tiene fotos reales, hash verificado y ancla en Stellar Testnet.",
      "Todas las referencias del sitio (nav, buscador, etiqueta QR, inicio) apuntan al mismo lote.",
      "Se corrigió el evento de despacho duplicado que tenía el lote en la base de datos.",
    ],
  },
  {
    version: "0.2.0",
    ciclo: "Version-0.02",
    fecha: "2026-11-08",
    titulo: "Estabilidad del backend",
    cambios: [
      "Migración de httpx a httpx2 para las llamadas del backend a Stellar.",
    ],
  },
];
