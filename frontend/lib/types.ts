export type EventoTipo =
  | "cosecha"
  | "clasificacion"
  | "empaque"
  | "despacho";

export interface Evento {
  id: string;
  tipo: EventoTipo;
  fecha: string;
  descripcion: string;
}

export interface Evidencia {
  nombre: string;
  tamano: number;
}

export interface Lote {
  id: string;
  codigo: string;
  fecha_cosecha: string;
  /** Fecha de postura de los huevos (HU-02). Opcional: si falta se usa la de cosecha. */
  fecha_postura?: string;
  linea_productiva: string;
  cantidad: number;
  unidad: string;
  finca: string;
  municipio: string;
  fotos: string[];
  evidencias: Evidencia[];
  hash_sha256: string;
  /** Hash de la transacción que ancló la huella en el contrato de NEAR. */
  near_tx_hash: string | null;
  /** Altura del bloque que incluyó esa transacción (cosmético; puede ser null). */
  near_block: number | null;
  eventos: Evento[];
  created_at: string;
  demo?: boolean;
}

export interface Verificacion {
  verificado: boolean;
  hash_calculado: string;
  hash_registrado: string | null;
  tx_hash: string | null;
  block: number | null;
  demo: boolean;
  /** Motivo de falla de infraestructura (RPC de NEAR caído, lote sin anclar...). */
  error?: string | null;
}

export const EVENTO_LABELS: Record<EventoTipo, string> = {
  cosecha: "Cosecha",
  clasificacion: "Clasificación",
  empaque: "Empaque",
  despacho: "Despacho",
};

export const LINEAS_PRODUCTIVAS = [
  "Huevos Guarumo",
  "Pescado Tilapia",
  "Frutales varios",
];

// --- Autenticación con Google (HU-06, HU-07) ---------------------------------

/** Shape exacto de ``UsuarioOut`` del backend. */
export interface Usuario {
  id: string;
  email: string;
  nombre: string;
  foto_url: string | null;
  cedula: string | null;
  telefono: string | null;
  finca: string | null;
  municipio: string | null;
  /** false → el primer ingreso aún no diligencia los 5 datos (HU-07). */
  perfil_completo: boolean;
}

/** Respuesta de ``POST /api/auth/google``: JWT + productor. */
export interface Sesion {
  token: string;
  usuario: Usuario;
}
