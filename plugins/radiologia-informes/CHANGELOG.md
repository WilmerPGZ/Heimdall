# Changelog

## 1.3.0 · verificador v2.2 · léxico VESPER · retiro de la Fábrica v2.1

- **Verificador v2.2:** PRIVACIDAD es la primera alerta (nombre de persona, documento, número de historia, cama, fecha de nacimiento, teléfono o firma en el bloque 1 o el 3), solo con contexto: los epónimos, la sigla del firmante y la comunicación dictada no alertan; la alerta nunca repite el dato y las demás lo enmascaran. Trae también v2.0 (`--extension 1|2|3`) y v2.1 (`--bloque3`: FALTO-DICTADO, FALTO-CLINICO, FALTO-N, LLAMAR-CERTEZA; OPI-NUM1). Pruebas: 62 de v1.9 + 1 de privacidad con 27 casos inventados.
- **`lexicon-imperium.md`** (raíz del plugin): léxico de ambientación VESPER v3, fuente única de los términos; lo leen la Fábrica y `evaluar-copiloto`.
- **`evaluar-copiloto` v1.1:** rutas nuevas del set de evaluación (D-236) y líneas de progreso VESPER (Probatio: benditos · parciales · herejías).
- **Se retira `fabrica-kb-radiologia`** (estándar KB v2.1): la sustituye la Fábrica v2.5 (`fabrica-kb-v25`), que no vive en este plugin. Queda en el historial de git.

## 1.2.0 · verificador v1.9

- **Opinión con criterio:** la unidad de idea pasa a ser el párrafo (también una línea numerada abre idea); alerta de número de ideas solo con más de 5; guía de palabras por idea 100 / 50 (señal, no tope). La frase de razonamiento («probablemente X; Y es menos probable porque…») no alerta.
- **Nuevas alertas en la Opinión:** idea que abre con un descriptor sin nombrar diagnóstico; «en el contexto de» que sustituye a la respuesta; frase idéntica a una de Hallazgos (≥8 palabras); dos opciones unidas por «/».
- **Nuevas alertas de forma:** rótulos de bloques auxiliares dentro del informe (BLOQUE); token en mayúsculas aislado al inicio (SIGLA); valores físicamente imposibles de UH o porcentaje >100 (RANGO).
- **Rótulos `Opinión · sobria` / `Opinión · asertiva` (`/alt`):** cada variante se revisa por separado con prefijo en la alerta; antes no se reconocían.
- Se elimina la excepción de LADO tras un marcador de verificación.
- Misma CLI y mismo formato de salida (código 0 siempre). Se añade `verificar()` y una batería de 62 pruebas (`tests/`, solo biblioteca estándar).
- Compatible con v1.8 en los chequeos que no cambian.

## 1.1.3

- Verificador v1.8.
