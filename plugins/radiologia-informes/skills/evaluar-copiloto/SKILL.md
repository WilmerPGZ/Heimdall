---
name: evaluar-copiloto
description: Regression-tests a radiology report copilot instruction against its eval set by simulating fresh chats with subagents and grading each case PASA, PARCIAL or FALLA. Use in Cowork after any change to the shared core, a project delta or the checker, before the radiologist pastes the new instruction.
---

# Evaluar copiloto · pruebas de regresión simuladas (v1.1 · 2026-10-22)

Works only where subagents exist (Cowork). Talk to the radiologist in Spanish; reason in English. The simulation tests the instruction's logic (format, certainty, markers, dictated-content rules, voice). It cannot test anything that depends on project files (dispatch hits, SYS criteria, KB phrase banks): mark those MUSTs «N/A sim» and leave them for a real chat.

## Inputs (private, in the RADS working folder; never copy them into this plugin)
- Instruction: `_homogeneizacion/salida/plan-09/instruccion/rNN.md` (the one about to be pasted; the single copilot since D-221).
- Eval set: the newest `_homogeneizacion/evals/evals-comunes-v*.md` (ID table + MUST / MUST-NOT per case), the synthetic drafts `evals/casos-sinteticos-E01-E11.md`, the release's deterministic evals in `evals/rNN-G-D*/` and the blind A/B cases in `salida/plan-09/ab/ab-D*/casos.json`. Run the IDs of that project plus «los 4». (The old per-project folders `insumos/` and `salida/<proyecto>/` were retired in D-236.)
- Checker: `scripts/verificar_informe.py` of the sibling skill `verificador-informe-radiologico` (or `compartidos/verificar_informe.py`).

## Procedure
1. Copy the instruction, the checker and the case drafts to a scratch folder. Never put patient identifiers in any prompt or file; case drafts are already anonymized, and if one is not, stop and say so.
2. **Run** (one subagent per project, cases independent): the subagent reads the instruction as its system prompt and answers each case as a fresh chat; no project files are available, so it handles every load as «file not available» exactly as the instruction says; it runs the checker on its block 1 (`python3 verificar_informe.py salida.txt borrador.txt`) and resolves alerts as the instruction says; it writes each full reply to `out-<ID>.md`. Correction turns (cases with «turno 2») are run in the same subagent conversation, in order.
3. **Grade** with a separate subagent that did not write the answers: for each case, every MUST and MUST-NOT → cumple / no cumple / N/A sim, with the literal fragment that proves it. PASA = all applicable MUSTs and no MUST-NOT · PARCIAL = a MUST missed without breaking N1 or N2 · FALLA = any MUST-NOT, or a MUST of N1 or N2 missed.
4. **Read the FALLA and PARCIAL yourself** against the instruction text: is it the instruction (ambiguous or conflicting rule → propose the exact line to change), the case (MUST outdated by a later decision → say which), or the simulation (needs project files → N/A)? Never edit the instruction or the eval set in this skill; propose.
5. **Record** a dated block at the end of the project's `evals-resultado.md`: instruction version and core version, model, table ID · resultado · motivo, and the proposed fixes.

## Progress lines (VESPER, background flavor)
Ornament only, never inside a copilot answer, a case file or a grade; the grades stay PASA / PARCIAL / FALLA. One line per event, «+++ … +++», ≤80 characters, from `lexicon-imperium.md` §4 (plugin root): first action «+++ Letanía de ignición · la Forja despierta +++» · audit «+++ Inquisitio abierta · <alcance> +++» / «+++ Inquisitio cerrada · <n> hallazgos +++» · a runner starts / returns «+++ Servocráneo <n> parte con su lote · <tema> +++» / «+++ Servocráneo <n> entregó su lote · <k> de <N> +++» · summary «+++ Probatio: <a> benditos · <b> parciales · <c> herejías +++» (PASA = bendito, PARCIAL = parcial, FALLA = herejía; benditos + parciales + herejías = casos), with 0 parciales and 0 herejías append «· el Emperador protege» · fatal error «+++ El espíritu de la máquina se resiste · <qué falló> · <qué hago ahora> +++». No patient data, dictated entity or person's name in any line.

## Report to the radiologist (Spanish, ≤12 lines)
Version tested · PASA / PARCIAL / FALLA / N/A counts · each FALLA in one line with its cause · proposed fixes · what still needs a real chat. Adoption rule: zero FALLA in simulation AND in the real cases that the simulation marked N/A.
