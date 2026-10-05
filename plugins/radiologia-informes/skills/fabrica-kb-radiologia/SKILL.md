---
name: fabrica-kb-radiologia
description: Builds, patches, migrates and audits knowledge-base files (KB, SYS, TRANSVERSAL, CORE) for radiology report copilots under the KB standard v2.1, and harvests the radiologist's corrections into rules. Use for /kb work, new topic files, fixes, v1→v2 or v2.1 migration, pruning a full project, redundancy checks, lesson harvest or library sync.
---

# Fábrica de KB · copilotos de radiología (v1.4 · 2026-10-05)

The four copilots (Claude RADS, NeuroRadio, RM de cuerpo, MSK) answer the radiologist in Spanish. In chat they do NOT see their project files as a folder: they read them with the project-knowledge search, one query per need («<logical file name> <section or entity>»), and each project's trigger table (`despacho-<proyecto>`) lives at the end of the Δ1 of its instructions, not as a file. This skill holds the rules for writing those files, so the instructions do not carry them in every turn. Talk to the radiologist in Spanish; you may reason in English.

## Sources of truth (the RADS working folder, reachable from Cowork)
- Standard: `RADS/04 KB Markdown/_homogeneizacion/core/estandar-kb-v2.1.md` (search-ready rules: self-contained fichas, card index, retrieval test, v2.0→v2.1 migration) on top of `core/estandar-kb-v2.md` (subtypes) and `RADS/04 KB Markdown/estandar-kb-radiologia-v1.1.md` (§0 rules, §2 names, §3–§5 anatomy, §7 markers, §12 linter, §14 template). Read both before building.
- Tools in this skill's `scripts/` (run them, never reimplement): `migrar_kb_v21.py` (mechanical v2.0→v2.1 migration, idempotent; `--compacto` when the project is full: Contexto without description, Índice instead of «Posee», Fuentes without pages, changelog and [NF]-only gap lines to disk; `--check` = the v2.1 linter rules CTX, RET-P, SIZE, IDX, TAB plus missing Dictado/Keywords and example Opiniones that open with a certainty term) · `redundancia_kb.py` (report only: overlapping files, twin fichas, small files, orphans; merge only when it saves real space, because a merge breaks dispatch rows and pointers).
- Linter: `scripts/lint_kb.py` in this skill (the RADS copy `_tools/lint_kb.py` is the same script with its file list built in) — run it, do not reimplement it: `python3 scripts/lint_kb.py ARCHIVO_O_CARPETA --known <lista>`. The list of known file names is private and lives outside the plugin (`_tools/lint_known_<proyecto>.txt` in the RADS folder); in Cowork the RADS copy `_tools/lint_kb.py` already carries it; in a chat, build the list from `project_info`.
- Shared core and files: `_homogeneizacion/core/` (núcleo común v1.4, alcance, estándar, lecciones, manual) and `compartidos/` (terminology, shared KBs, `verificar_informe.py`; `buscar_kb.py` works only on a disk copy of a project). A shared file is edited there and copied identically to every project that uses it.
- Scope table: `core/alcance-comun-v1.md` decides which project owns a topic (CT spine → Claude RADS; other spine → NeuroRadio; MSK has no spine; a neck mass with supraclavicular epicenter stays in NeuroRadio).
- Lessons: `core/lecciones-comunes.md` (every past correction → its rule → its eval). Certainty scale: report manual §V.2–V.3.
- RM de cuerpo only: locate sources in `claude/indice-literatura-rm-fisica.md` and cite in Vancouver from its §1.

## Build a file
1. Confirm the owner project with the scope table, and that no file already covers the topic (on a disk copy: `python3 buscar_kb.py --raiz <copia> --buscar "<términos>"` and `--indice`; in the project: `project_info` / project search). One topic, one file; one fact, one owner.
2. Pick the subtype (standard v2 §1: ENT, EST, SYS, TRV, CORE, STY, TPL, IDX, LIT, TOOL; META never goes into a project) and its name pattern. Name = route: lowercase kebab-case Spanish; carry the modality when the same topic exists in two projects (`degenerativa-columna-tc` / `degenerativa-columna-rm`).
3. Card with every v2 field (`Subtipo`, `Slug`, `Proyecto(s)`, `Versión`, `Actualizado`, `Estado`, `Posee`, `No posee →`, `Dictado (ES)`, `Keywords (EN)`, `Fuentes`, `Copia idéntica en`, `Índice` with the exact ficha titles). Fichas `## 3.N · Entidad · slug` of 150–400 tokens (never over 600) with `> Contexto:`, `Dictado`, `Keywords`, `Escribe · Hallazgos`, `Escribe · Opinión`, `Certeza`, `Nivel`, `Trampa`, `Si falta →`, `Enseña` (pearl or classic error in ≤2 lines + source; it feeds the tutor). Differential `## 4.N`; pointers; gaps and tensions; sources; changelog; retired versions.
4. Search reaches fichas as loose fragments without the file header, so every ficha must stand alone: `> Contexto: <slug> · <modalidad> · <proyecto> · <entidad> · dispara: <palabras>`, the slug repeated in the title, a `Dictado` line with the words (and frequent speech errors) the radiologist actually dictates and a `Keywords` line in English. Tables ≤8 rows with their column names; one ficha per category in a SYS.
5. Two layers: reasoning in telegraphic English; everything that may reach a report in literal Spanish with full accents. Phrase banks follow the report manual §V.2–V.3 (no «compatible con», «diagnóstico de», «sin poder descartarse»), recommendations only in the núcleo N9 forms («Se sugiere…»), no perception verbs, no interpretation in `Escribe · Hallazgos`, no colons or measurements in an example Opinión. Narrative voice (núcleo v1.4, N6–N8): `Escribe · Hallazgos` is a complete sentence with a verb, articles and prepositions, location first when natural («En el hilio hepático hay una masa que comprime la vena porta.»), a verbless noun after a comma becomes its own verb («, compresión de» → «que comprime»; never a stronger one), no filler («a nivel de», «presencia de», «de tipo»); `Escribe · Opinión` opens with the certain finding or the diagnosis, never with a certainty term, and the term sits right before what it qualifies («Masa hepática, sospechosa de colangiocarcinoma.» · «Rotura del ligamento cruzado anterior, probablemente completa.»), agreeing in gender and number. A rule that holds only under a condition («cuando se sospecha tumor…») states that condition in the same line.
6. Extract only from uploaded or cited sources. A missing datum is `[NF]`; conflicting sources are `[TENSION]` with both values and origins, never resolved silently. A threshold always carries its acquisition conditions. Classification criteria live only in their SYS file; a KB points to it.
7. Retired versions and long changelogs stay on disk (or git), never inside a project file: search cannot tell current from retired text. Do not add REVISOR markers to new files.
8. Retrieval check (standard §6): in a chat of the owner project, two typical dictation phrases and one English keyword must bring the right ficha (with `#audit`, the footer names the file loaded). Per project, keep `prueba-recuperacion-<proyecto>.md` (20 real queries, target ≥18/20 right file and ≥16/20 right ficha) on disk and rerun it after each batch.

## Migrate a project to v2.1 (search-ready)
Order: MSK (pilot) → NeuroRadio → Claude RADS → RM de cuerpo; one writer per project. Procedure (template: `_homogeneizacion/cowork/cowork-05-msk-kb-v21.md`): inventory with sizes and capacity → freeze the 20-query retrieval test and measure the baseline → back up every project doc to disk → prune only META, exact copies, superseded versions, other projects' files and stale copies of shared CORE files (everything else is a listed candidate) → `migrar_kb_v21.py --compacto` on the backup → upload in `_orden-subida.txt` order → re-measure → adopt (≥ baseline and ≥18/20 file, ≥ baseline ficha) or revert the migrated files.

## Migrate a v1 file (no fichas) to v2
Take files in the priority order of the project's `migracion-v2.md`. For files that already have fichas, run the mechanical v2.0→v2.1 steps of standard §7 (Contexto line, slug in titles, card index, retired content to disk) before any rewrite. Keep every criterion, figure and citation; only restructure into card + fichas, move superseded text to retired versions, and add `Enseña` only when the source supports it. Run the linter and the access check of step 8.

## Patch an existing file
- Patch in its current skeleton; superseded text moves to the retired-versions section, never mixed with current content.
- Retired certainty terms are lexicon, not clinical content: replace them per manual §V.2–V.3 and log `[W AAAA-MM-DD]` in the changelog.
- Never change a criterion, threshold, figure or citation without a source.

## One writer per project
Before rewriting files in a project, compare `project_info` with the last manifest; never run two writing tasks on the same project at the same time (a parallel batch moved files mid-task on 2026-10-05).

## Harvest lessons
The radiologist's chats append behavior corrections to `lecciones-informe.md` in each project's memory (núcleo N18), and reports may leave «→ Factory: …» lines (N19). For each one: decide its owner (a ficha's `Trampa` or `Escribe`, the project delta, or the shared core), write the rule with `[W AAAA-MM-DD]`, add an eval case (MUST / MUST-NOT) to the project set, add a row to `core/lecciones-comunes.md`, and tell the radiologist which memory lines can now be removed. A lesson that would change the shared core is proposed, not applied, until the radiologist approves.

## Before delivering (in this order)
1. Linter: zero FAIL, and `migrar_kb_v21.py <carpeta> --check` clean for the files you touched.
2. Diff against the previous version.
3. Sync checklist: row in the `despacho-<proyecto>` table at the end of the owner's Δ1 (that instruction must then be pasted again; say so) · paired SYS declared · pointers from sibling files (one level only) · shared copies refreshed in every project that uses them.
4. Evals: run the project's eval set when the file changes a case it covers; record PASA / PARCIAL / FALLA. Adopt only with zero FALLA.

## Handoff note (the only text addressed to the radiologist, in Spanish)
File, subtype and owner project · dispatch row (and whether the instruction must be pasted again) · what it owns and what it points to · cross-file patches · declared gaps (`[NF]`, `[TENSION]`) with the source that would close them · linter and access-check results · one changelog line. Deliver complete files, never patches.
