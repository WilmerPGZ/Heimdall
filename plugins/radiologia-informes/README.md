# radiologia-informes

Kit del Copiloto de Informes radiológicos en Claude (antes cuatro copilotos: Claude RADS, NeuroRadio, RM de cuerpo y MSK).

## Qué trae

- **verificador-informe-radiologico**: chequeo determinista que las instrucciones de los copilotos corren antes de emitir cada informe (términos retirados, verbos de percepción, marcadores, decimales, tildes, ideas de la Opinión con criterio (descriptor sin diagnóstico, «en el contexto de», frase copiada de Hallazgos, opciones con «/»), variantes `/alt`, lado, cifras, negaciones, procedimientos fuera de forma, cambios de unidad, rótulos de bloques auxiliares, siglas sueltas y rangos imposibles de UH o porcentaje). El script está en `scripts/verificar_informe.py` y también dentro del SKILL.md. Desde la v2.2 revisa también la privacidad (ningún dato personal en el informe). Las pruebas (63) están en `tests/`.
- **lexicon-imperium.md**: léxico de ambientación VESPER (nombres de fondo; nunca entra al informe).
- **evaluar-copiloto**: pruebas de regresión simuladas de una instrucción con subagentes (solo en Cowork), con calificación PASA / PARCIAL / FALLA. Los casos de prueba viven fuera del plugin.

## Uso

Se enciende y se apaga como una unidad desde Customize → Plugins. No envía datos a ningún servicio externo y no contiene datos de pacientes.
