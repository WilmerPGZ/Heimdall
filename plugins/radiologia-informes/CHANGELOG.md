# Changelog

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
