//! Contrato KV de AgroChain Rural.
//!
//! Guarda, por código de lote (`HUE-YYYY-NNN`), la huella SHA-256 del lote
//! como **hex de 64 caracteres**. El `view get` devuelve exactamente el string
//! que el backend ya compara en `app/services/sha256.py`, sin conversiones.
//!
//! Se eligió almacenar la cadena hex (y no `[u8; 32]`) a propósito: el hash
//! canónico del lote no depende de la cadena, así que guardar el texto deja la
//! verificación HU-03 idéntica a la de Stellar.

use near_sdk::near;
use near_sdk::store::LookupMap;

/// Longitud de un SHA-256 en hex (32 bytes → 64 caracteres).
const LEN_HASH: usize = 64;

#[near(contract_state)]
pub struct AgroChainKv {
    /// codigo_de_lote → hash SHA-256 en hex.
    lotes: LookupMap<String, String>,
}

// `LookupMap` no implementa `Default` (necesita un prefijo de almacenamiento
// propio), así que se escribe a mano.
impl Default for AgroChainKv {
    fn default() -> Self {
        Self {
            lotes: LookupMap::new(&b"lotes"[..]),
        }
    }
}

#[near]
impl AgroChainKv {
    /// Ancla el hash de un lote.
    ///
    /// Es **idempotente**:
    /// - lote nuevo → se guarda;
    /// - mismo código con el mismo hash → no-op (reintentos seguros);
    /// - mismo código con otro hash → panic: el dato fue alterado.
    ///
    /// No es pagable: el *storage staking* lo cubre el saldo de la cuenta del
    /// contrato (~100 bytes por lote ≈ 0.001 NEAR).
    pub fn set(&mut self, codigo: String, hash: String) {
        assert!(!codigo.is_empty(), "codigo vacio");
        assert_eq!(hash.len(), LEN_HASH, "hash debe tener 64 caracteres hex");

        // Se clona para liberar el préstamo sobre `codigo` antes del `insert`.
        let previo = self.lotes.get(&codigo).cloned();

        match previo {
            Some(previo) => assert_eq!(
                previo, hash,
                "el lote ya existe con un hash distinto"
            ),
            None => {
                self.lotes.insert(codigo, hash);
            }
        }
    }

    /// Devuelve el hash anclado para un código, o `None` si aún no existe.
    pub fn get(&self, codigo: String) -> Option<String> {
        self.lotes.get(&codigo).cloned()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use near_sdk::test_utils::test_env::setup_free;

    const CODIGO: &str = "HUE-2027-001";
    const HASH_A: &str = "1111111111111111111111111111111111111111111111111111111111111111";
    const HASH_B: &str = "2222222222222222222222222222222222222222222222222222222222222222";

    #[test]
    fn guarda_y_devuelve_el_hash() {
        setup_free();
        let mut contrato = AgroChainKv::default();
        contrato.set(CODIGO.into(), HASH_A.into());
        assert_eq!(contrato.get(CODIGO.into()), Some(HASH_A.to_string()));
    }

    #[test]
    fn codigo_desconocido_devuelve_none() {
        setup_free();
        let contrato = AgroChainKv::default();
        assert_eq!(contrato.get("NO-EXISTE".into()), None);
    }

    #[test]
    fn es_idempotente_con_el_mismo_hash() {
        setup_free();
        let mut contrato = AgroChainKv::default();
        contrato.set(CODIGO.into(), HASH_A.into());
        // Un reintento debe ser un no-op, no un error.
        contrato.set(CODIGO.into(), HASH_A.into());
        assert_eq!(contrato.get(CODIGO.into()), Some(HASH_A.to_string()));
    }

    #[test]
    #[should_panic(expected = "hash debe tener 64 caracteres hex")]
    fn rechaza_hash_de_longitud_incorrecta() {
        setup_free();
        let mut contrato = AgroChainKv::default();
        contrato.set(CODIGO.into(), "abc".into());
    }

    #[test]
    #[should_panic(expected = "codigo vacio")]
    fn rechaza_codigo_vacio() {
        setup_free();
        let mut contrato = AgroChainKv::default();
        contrato.set(String::new(), HASH_A.into());
    }

    #[test]
    #[should_panic(expected = "el lote ya existe con un hash distinto")]
    fn rechaza_hash_distinto_para_el_mismo_codigo() {
        setup_free();
        let mut contrato = AgroChainKv::default();
        contrato.set(CODIGO.into(), HASH_A.into());
        contrato.set(CODIGO.into(), HASH_B.into());
    }

    #[test]
    fn aislamiento_entre_prefijos_de_almacenamiento() {
        setup_free();
        let mut contrato = AgroChainKv::default();
        contrato.set("HUE-2027-001".into(), HASH_A.into());
        contrato.set("HUE-2027-002".into(), HASH_B.into());
        assert_eq!(contrato.get("HUE-2027-001".into()), Some(HASH_A.to_string()));
        assert_eq!(contrato.get("HUE-2027-002".into()), Some(HASH_B.to_string()));
    }
}
