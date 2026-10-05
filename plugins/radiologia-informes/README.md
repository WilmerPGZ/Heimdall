# radiologia-informes

Kit para cuatro copilotos de informe radiológico en Claude (Claude RADS, NeuroRadio, RM de cuerpo y MSK).

## Qué trae

- **verificador-informe-radiologico**: chequeo determinista que las instrucciones de los copilotos corren antes de emitir cada informe (términos retirados, verbos de percepción, marcadores, decimales, tildes, ideas de la Opinión, lado, cifras, negaciones, procedimientos fuera de forma y cambios de unidad). El script está en `scripts/verificar_informe.py` y también dentro del SKILL.md.
- **fabrica-kb-radiologia**: reglas para construir, parchear y migrar archivos de conocimiento con el estándar KB v2.1 (voz narrativa del núcleo v1.4), con su linter (`scripts/lint_kb.py`), la migración mecánica a v2.1 con modo compacto para proyectos llenos (`scripts/migrar_kb_v21.py`) y el informe de redundancia (`scripts/redundancia_kb.py`).
- **evaluar-copiloto**: pruebas de regresión simuladas de una instrucción con subagentes (solo en Cowork), con calificación PASA / PARCIAL / FALLA. Los casos de prueba viven fuera del plugin.

## Uso

Se enciende y se apaga como una unidad desde Customize → Plugins. No envía datos a ningún servicio externo y no contiene datos de pacientes.
