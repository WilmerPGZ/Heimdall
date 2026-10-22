# lexicon-imperium · VESPER · léxico de ambientación del Copiloto de Informes · v2 (2026-10-21)
<!-- Source of truth for every themed term. The chat instruction carries a compact copy (Δ-UI); the Factory, radkb.py and evaluar-copiloto read this file. Edit this file first; the Δ-UI copy changes in the same release. -->

## 0 · Rules
- Flavor wraps, plain Spanish explains: every themed string makes the action clearer, never darker. Gothic name first; plain hint after «·» when the Latin alone does not say what happens; hint ≤4 words.
- Additive only: never rename a file, skill, command, flag, section letter, machine-read prefix («SIN RESULTADOS», «NO EXISTE», «ÍNDICE DESACTUALIZADO», «MOTOR», «SIN HUELLA», «comprimidas por tope», «omitidas por tope», «cargar kb-X»), engine header («#### radkb v2.0 · …», «#### clave · …»), harvest marker («→ Factory», «→ Maestro», «Lección»), grade (PASA, PARCIAL, FALLA) or KB marker ([NF], [TENSION], [RETIRADO], [PEND…], [W …]).
- Never in report text, the warning line, «Llamar», «Faltó», «Considerar», block headings or the model's reasoning. Never patient data, a dictated entity or a person's name; a signer only by sigla.
- Ornament lines start and end with «+++»; no tool or model parses them.
- Lengths: tool label ≤45 characters before the sigillum · command header ≤90 · progress line ≤80 · Codex word ≤10 letters.
- Fixed or deterministic strings only (by event or by day of year); never random.
- Scarcity: always → Codex, Verispex, placa de datos, folio · sometimes → sigillum, sello de pureza, hallazgo crítico, letanía de ignición, Dogma, Tabulae, Scriptorium, Auspicium, Schola · rare → Exterminatus, Omnissiah, «el Emperador protege», disformidad, espíritu de la máquina.
- No GW passages: names and short iconic cries only; never the Credo Omnissiah or official Thoughts for the Day.
- Spanish edition forms: servocráneo, disformidad, placa de datos, tecnosacerdote.
- One term, one meaning.

## 1 · Lore
| Project piece | Imperium name |
|---|---|
| project codename | VESPER (not shown during a shift) |
| the copilot | el Lexmecánico |
| a kb-* skill | Codex (pl. Codices) |
| ficha | folio (pl. folia) |
| specialty delta | Dogma |
| SYS file | Tabulae |
| signer card | sigillum |
| checker | el Verispex · rite: Ritus Verificationis |
| checker run with 0 alerts | sello de pureza |
| pre-lectura (N20) | Auspicium |
| tutor / study | la Schola |
| search inside a file | Scriptorium |
| Factory | la Forja |
| Factory orchestrator | el Magos |
| subagent / checker fallback | servocráneo |
| batch of fichas | lote de folios |
| recompile the index | reconsagrar el índice |
| audit | Inquisitio |
| regression eval | Probatio (PASA = bendito, PARCIAL = parcial, FALLA = herejía) |
| library sync | sincronizar el Archivum |
| /tmp/borrador.txt | placa de datos |
| first command of a chat or Forja session | letanía de ignición |
| full redo from the ledger / retired ficha | Exterminatus |
| engine missing or unreadable | tormenta de disformidad |
| script exception | el espíritu de la máquina se resiste |
| big Forja job closed | Gloria al Omnissiah |
| Probatio with 0 PARCIAL and 0 FALLA | el Emperador protege |

## 2 · Codex names
kb-neuro Neuralis · kb-rads Corporis · kb-rmcuerpo Magnetis · kb-msk Ossium · kb-cardio Cordis · kb-fisica-rm Physicae.
- Visible skill names [W 2026-10-22 · E-D240 · exception to «additive only»]: codex-neuralis (kb-neuro) · codex-corporis (kb-rads) · codex-magnetis (kb-rmcuerpo) · codex-ossium (kb-msk) · codex-cordis (kb-cardio) · codex-physicae (kb-fisica-rm). Only the SKILL.md `name`, the zip's root folder and the zip name change; the internal id kb-* stays in links, deltas, prefixes («cargar kb-X»), engine headers, evals, kb25, the Factory and the skill-kb folders. The engine reads both (alias table `CODEX_SKILL`).
- Reserved [W 2026-10-22], not yet created: **Mammae** = codex-mammae (kb-mama; recipe A, genitive of *mamma*: mammography, tomosynthesis, breast US and MRI, BI-RADS) · **Nuclearis** = codex-nuclearis (kb-mn; recipe B, -alis adjective agreeing with the masculine codex: PET/CT, SPECT, scintigraphy). Engine table `CODEX_RESERVADOS`; while reserved, the study is refined with the core («Ningún Codex cubre este estudio: lo refiné con el núcleo.»).
New skills: «Codex <Latin>», ≤10 letters, a genitive noun or a Mechanicus-style adjective in -alis agreeing with the masculine codex.

## 3 · radkb.py output
- Section headers: «### <letter> · <Gothic> · <current title>».
| Letter | Gothic | Current title |
|---|---|---|
| B | Vox | banderas |
| P | Quaestio | pregunta clínica (indicación) |
| S | Tabulae | clasificaciones |
| R | Via | ruta |
| D | Decreta | delta |
| F | Folia | fichas |
| E | Stylus | estilo |
| L | Nexus | enlaces |
| V | Lacunae | vacíos |
- Extra letters keep their current header until a Gothic name is registered here.
- pack, last two lines of the whole output: «+++ Codex <X> abierto · <N> folios · <fecha imperial> +++» (two skills: «+++ Codices <A> et <B> abiertos · <N> folios · <fecha> +++») · «+++ Pensamiento del día: <latín> · <español> +++».
- verificar, last line, from the same alert list that sets the exit code: «+++ Sello de pureza · el Verispex no halla herejía +++» (0 alerts) or «+++ El Verispex señala <N> alertas · sin sello hasta resolverlas +++». Exit codes unchanged.
- Errors, one line before any traceback: engine or index missing or unreadable → «+++ Tormenta de disformidad · <qué falló> +++»; script exception → «+++ El espíritu de la máquina se resiste · <qué falló> +++».
- Imperial date: «0 <fraction> <year>.M<millennium>», fraction = (day_of_year × 1000 // days_in_year) % 1000, zero-padded; year = year % 1000; millennium = year // 1000 + 1; time zone America/Bogota. 2026-10-21 → «0 805 026.M3».
- Thought of the day: DOGMATA[day_of_year % 12], 0-based:
  0 Quod non dictatum est, non scribitur · lo no dictado no se escribe
  1 Latus sacrum est · el lado es sagrado
  2 Mensura sine unitate, haeresis · medida sin unidad es herejía
  3 Nulla opinio sine responsione · ninguna Opinión sin respuesta
  4 Certitudo in incerto ponitur · la duda va sobre lo dudoso
  5 Prius urgens, deinde cetera · primero lo urgente
  6 Novacula Occami, scutum Hickami · una causa si alcanza, dos si no
  7 «Se observa» delenda est · «se observa» debe ser destruido
  8 Anathema sit «compatible con» · maldito sea «compatible con»
  9 Oculus non videt quod mens non novit · el ojo no ve lo que la mente no conoce
  10 Quaere secundum · busca la segunda lesión
  11 Comparatio regina probationum · la comparación es la reina de las pruebas
- Script docstrings may open with one themed line («Cogitador del Lexmecánico: …»); identifiers, functions and flags never change.

## 4 · Background work (Cowork, Claude Code, Factory skills)
- Progress lines: «+++ <acción en claro> +++», ≤80 characters.
| Event | Line |
|---|---|
| first Forja action of a session | «+++ Letanía de ignición · la Forja despierta +++» |
| plan ready | «+++ El Magos trazó el plan · <N> lotes de folios +++» |
| subagent starts | «+++ Servocráneo <n> parte con su lote · <tema> +++» |
| subagent returns | «+++ Servocráneo <n> entregó su lote · <k> de <N> +++» |
| new ficha written | «+++ Folio forjado · <archivo lógico> 3.<N> +++» |
| ficha retired ([RETIRADO]) | «+++ Exterminatus · folio retirado: <archivo> 3.<N> +++» |
| index recompiled | «+++ Índice reconsagrado · Codex <X> +++» |
| audit starts / ends | «+++ Inquisitio abierta · <alcance> +++» · «+++ Inquisitio cerrada · <n> hallazgos +++» |
| lessons harvested | «+++ Cosecha de la Forja · <n> lecciones nuevas +++» |
| library sync | «+++ Archivum sincronizado · <n> archivos +++» |
| eval summary | «+++ Probatio: <a> benditos · <b> parciales · <c> herejías +++»; with 0 parciales and 0 herejías append «· el Emperador protege» |
| big job closed (index recompiled + Probatio run) | «+++ Gloria al Omnissiah · Codex <X> reconsagrado y probado +++» |
| fatal error | «+++ El espíritu de la máquina se resiste · <qué falló> · <qué hago ahora> +++» |

## 5 · Chat surfaces
Tool labels (layer 1), service lines (layer 2) and command headers (layer 4) live in the instruction's Δ-UI. Since r17 the service lines are written in place in their VESPER form; the plain forms they replace: «Firmante: <SIGLA> · huella cargada · vale para el chat.» → «Sigillum <SIGLA> · huella cargada · vale para el chat.» · «Firmante: <SIGLA> · huella parcial; el resto, estilo común.» → «Sigillum <SIGLA> · huella parcial; el resto, estilo común.» · «Sin huella de <SIGLA>: estilo común.» → «Sigillum <SIGLA> no hallado: estilo común.» · «Sin sigla de firmante: estilo común.» → «Sin sigillum: estilo común.» · «Sin base de conocimiento: la skill <kb-x> no está disponible en este chat.» → «El Codex <X> no responde en este chat: refiné solo con el núcleo.» · «Lo refiné con el núcleo; ninguna base de conocimiento cubre este estudio.» → «Ningún Codex cubre este estudio: lo refiné con el núcleo.» · «Sin ficha en la skill para <tema>: usé la bandeja del proyecto.» → «Sin folio en el Codex para <tema>: usé la bandeja del proyecto.»

## 6 · Reserve (approved candidates, not yet used)
Reliquia (backup) · Roseta (W's «sí» authorizing a load) · Sello de juramento (opening an encargo) · Logis (token-budget estimates) · Noosfera (search index; needs a hint) · Bibliotheca (literature search).

## 7 · Adding a term
Need → reserve and glossary → web (Lexicanum, Fandom EN/ES, Warhammer Community, Black Library extracts; forums only for reception) → 3–5 candidates → filter F1–F10 → Latin check (Wiktionary, Whitaker's Words, Lewis & Short; codex is masculine) → recipe A–G → register here + Δ-UI if chat-visible + eval literals if layer 2 + test if layer 3 → show W if it changes what he sees in every report.

## 8 · Changelog
- v3 · 2026-10-22 · D-241 (M0): visible names codex-* [W, exception to «additive only»]; Mammae and Nuclearis reserved; plain forms of the service lines kept here (r17 writes the VESPER forms in place).
- v2 · 2026-10-21 · VESPER consolidated: Neuralis, Magnetis, servocráneo, sello de pureza, letanía de ignición, Exterminatus, disformidad, Omnissiah, «el Emperador protege», section names, imperial date fixed to 0 805 026.M3, reserve list.
- v1 · 2026-10-21 · first lexicon (labels, service lines, engine ornament, Forja progress lines).
