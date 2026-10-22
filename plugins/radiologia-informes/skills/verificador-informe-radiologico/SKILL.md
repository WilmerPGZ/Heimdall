---
name: "verificador-informe-radiologico"
description: "Holds the deterministic report checker used by four radiology report copilots (Claude RADS, NeuroRadio, RM de cuerpo, MSK). Their instructions extract and run it with one bash command before emitting block 1."
---

# Verificador del informe radiológico · v2.2 (2026-10-22)

The copilots' project files are no longer mounted as a folder in chat (checked 2026-10-04: no `/mnt/project`), but account and plugin skills are (under `/mnt/skills`; this one ships in the plugin `radiologia-informes`, with the same script also in `scripts/verificar_informe.py`). This skill only stores the checker; nothing here needs to be read into context.

## Run it (one bash call)
Save the proposed block 1 to `/tmp/salida.txt` and the pasted draft to `/tmp/borrador.txt`, then:

```
V=/tmp/verificar_informe.py; [ -s "$V" ] || sed -n '/^#BEGIN_SCRIPT$/,/^#END_SCRIPT$/p' "$(find /mnt/skills -path '*verificador-informe-radiologico*' -name SKILL.md 2>/dev/null | head -1)" > "$V"; python3 "$V" /tmp/salida.txt /tmp/borrador.txt [--extension 1|2|3] [--bloque3 /tmp/b3.txt]
```

The first call of a conversation extracts the script to `/tmp`; later calls reuse it. Output: «OK · sin alertas» or one alert per line. With `/alt`, put both Opiniones in the same file under the plain lines «Opinión · sobria» and «Opinión · asertiva»: one run checks each one separately and prefixes its alerts with `[sobria]` or `[asertiva]` (or run it once per version). Resolve every alert: fix it, or keep it and declare why. If the command finds no script, say so in block 3 and check by hand.

## Source of truth
`RADS/04 KB Markdown/_homogeneizacion/compartidos/verificar_informe.py`. When it changes, this skill is updated with the identical text. v1.2: markers like `[COMPLETAR: lado]` no longer trigger the colon or measurement alerts in the Opinión. v1.3: a decimal point at the end of a sentence («1.2.») is caught; body words added to the accent list (relación, ventrículo, hepático, esplénico, sistólico, diastólico…). v1.4: «RM … simple» and «RM de cráneo» are flagged; equivalent negations («no hay», «no se identifica», «sin evidencia de», «sin») count once and «sin contraste» is technique, not a negation; RADS category numbers («PE-RADS 3/RV+») no longer count as new figures. v1.5: ID and phone numbers («1.234.567», six or more digits) are never compared or printed, so a removed identifier never reappears in an alert. v1.6: PROCEDIMIENTO alert when a «Se sugiere» sentence names a procedure outside the N9 form (dictated → keep the intent and declare it), and UNIDAD alert when a unit of the draft disappears from the output (declare it; never convert). v1.7: narrative voice (core v1.4) — ORDEN alert when an Opinión idea opens with a certainty term, VOZ alerts for a verbless noun after a comma («, compresión de») and for filler («a nivel de», «presencia de», «que corresponda a»); ORDEN stays quiet when Hallazgos carries the same existence hedge («posible nódulo»); Opinión numbering pasted on one line («Opinión: 1. … 2. …») no longer counts as figures. v1.8: idea 1 of the Opinión may reach 80 words (integrated prose); «sin relación con el cuadro» is not a negation; negations are compared within Hallazgos; any bracket in block 1 is an alert; REPETICIÓN alerts for «hay» over twice and three findings opening with the same word. v1.9 (instruction v2.0, core v2.2): prose in the Opinión is no longer penalized — an idea is a paragraph (or a numbered line), the idea-count alert fires only above 5, and the word limits (idea 1 ≤100, the rest ≤50) are signals; new Opinión alerts for an idea that opens with a descriptor and names no diagnosis, «en el contexto de» with no answer, a sentence copied from Hallazgos and two options joined by «/»; BLOQUE alert for block 2–4 lines inside block 1 («Descripción: … →», «Faltó:», «Considerar añadir», «Antes de pegar», «Lección:», «Firmante:», «→ Maestro:»…); SIGLA alert for an isolated 3–5 capital token opening block 1 (a signer's sigla); RANGO alert for UH outside −1100…4000 or a percentage above 100; «Opinión · sobria» / «Opinión · asertiva» labels; the old `[VERIFICAR LADO]` exception is gone. v2.0: `--extension 1|2|3` (concise, neutral, extended report) with word budgets per level. v2.1: `--bloque3` (proposed block 3): FALTO-DICTADO, FALTO-CLINICO, FALTO-N, LLAMAR-CERTEZA; OPI-NUM1 with a draft. v2.2: PRIVACIDAD comes first — a person's name (with a title, a label, an age, a frequent first name plus surname, the AGFA «SURNAMES, NAMES» form or a name from the draft's signature), an ID document, a record number, a bed or room, a birth date, a phone or a signature in block 1 or block 3; eponyms, the signer's acronym and a dictated communication never alert; the alert names the type and line, never the datum, and every other alert masks it. Tests: `tests/test_verificar_v19.py` and `tests/test_privacidad_v22.py` (`python3 -m unittest discover -s tests`).

```python
#BEGIN_SCRIPT
#!/usr/bin/env python3
"""verificar_informe.py · v2.2 (2026-10-22) · archivo compartido idéntico en los 4 copilotos.

Chequeo determinista del bloque 1 antes de emitirlo. No corrige: lista ALERTAS para que el modelo
las resuelva (corregir o declarar). Se ejecuta, no se lee: su texto no entra al contexto.

Uso:  python3 verificar_informe.py salida.txt [borrador.txt] [--extension 1|2|3] [--bloque3 b3.txt]
      (salida = bloque 1 propuesto; borrador = lo que el radiólogo pegó, opcional pero recomendado)
Sale con código 0 siempre; imprime «OK · sin alertas» o una alerta por línea.

Historial
v2.2 (2026-10-22) · M0 (P4) · PRIVACIDAD, primera alerta: nombre de persona (con tratamiento, rótulo, edad, nombre frecuente +
  apellido, formato AGFA «APELLIDOS, NOMBRES» o el nombre que el borrador trae en su firma o en sus rótulos), documento (CC, TI,
  pasaporte), número de historia, cama o habitación, fecha de nacimiento, teléfono y firma, en el bloque 1 y en el bloque 3. Sin
  falsos positivos con epónimos, la sigla del firmante ni la comunicación dictada (N11). La alerta nombra el tipo y la línea, nunca
  el dato; las demás alertas lo enmascaran («‹dato personal›»). Sin datos personales, idéntico a v2.1.
v2.1 (2026-10-21) · D-238 (r16) · «--bloque3 b3.txt» (bloque 3 propuesto): FALTO-DICTADO (un elemento del «Faltó» ya está
  en el borrador), FALTO-CLINICO (pide clínica, antecedente, edad o estudio previo: no se ve en la imagen), FALTO-N (más de 3),
  LLAMAR-CERTEZA (el «Llamar» no copia el diagnóstico y el término de certeza de su idea de la Opinión). Con borrador:
  OPI-NUM1 (una sola idea con «1.» que el borrador no numera). Sin «--bloque3», idéntico a v2.0 salvo OPI-NUM1.
v2.0 (2026-10-21) · D-221 · «--extension 1|2|3» (conciso, neutro, extenso): palabras de contenido (sin cifras, unidades ni
  etiqueta) por oración en Hallazgos (20, 30, 40),
  oraciones por hallazgo (–, 3, 4), idea 1 de la Opinión (20, 35, 50 palabras), ideas totales sin la recomendación (3, 4, 5);
  con 1, la línea nominal en Hallazgos no es alerta de VOZ. Sin «--extension», idéntico a v1.9. El anclaje no cambia.
v1.9 (2026-10-11) · la Opinión en prosa no se castiga: una idea = un párrafo (o una línea numerada),
  alerta solo con >5 ideas, topes 100/50 palabras como señal; nuevos chequeos de la Opinión:
  descriptor sin diagnóstico, «en el contexto de» sin respuesta, frase copiada de Hallazgos, barra
  entre opciones; BLOQUE (rótulos de los bloques 2–4 dentro del bloque 1), SIGLA aislada al inicio,
  RANGO físico (UH, %); rótulos «Opinión · sobria» / «Opinión · asertiva» con alertas prefijadas;
  se retira la excepción [VERIFICAR LADO] (y MARCADOR_OK, sin uso).
v1.8 (2026-10-05) · idea 1 ≤80 palabras; «sin relación con el cuadro» no es negación; negaciones solo
  en Hallazgos; todo corchete es alerta; REPETICIÓN («hay» >2, tres aperturas iguales).
v1.7 · ORDEN y VOZ (voz narrativa) · v1.6 · PROCEDIMIENTO y UNIDAD · v1.5 · documentos y teléfonos
  nunca se comparan · v1.4 · RM «simple» / «de cráneo», negaciones equivalentes, categorías RADS ·
  v1.3 · decimal al final de frase, tildes de anatomía · v1.2 · marcadores fuera de la Opinión.
"""
import re
import sys
import unicodedata

# Términos retirados o prohibidos en el texto firmable (núcleo N8, N9, N12).
RETIRADOS = {
    r"\bcompatibles? con\b": "certeza retirada «compatible con» → término LELEX, declarado «de X a Y»",
    r"\bdiagn[oó]stico de\b": "certeza retirada «diagnóstico de» → enunciado directo",
    r"\bsin poder descartar(se)?\b": "certeza retirada «sin poder descartarse»",
    r"\bno se puede (descartar|excluir)\b": "«no se puede descartar» como conclusión → [VERIFICAR CERTEZA] o nivel explícito",
    r"\bse recomienda\b": "recomendación: solo «Se sugiere…» (N9)",
    r"\bcontrol evolutivo\b": "recomendación sin modalidad ni plazo (N9)",
    r"\bsi (est[aá] )?cl[ií]nicamente indicad[oa]\b": "condicional prohibido en la recomendación (N9)",
    r"\bcorrelacion(ar|e)(se)? (cl[ií]nicamente|con la cl[ií]nica)\b": "«correlacionar clínicamente» a secas (N9)",
    r"\baproximadamente\b": "sin «aproximadamente» (N12)",
    r"\bHU\b": "«UH», no «HU» (N12)",
    r"\bTAC\b": "«TC», no «TAC» (N12)",
    r"\bRMN\b": "«RM», no «RMN» (N12)",
    r"\bruptura\b": "«rotura», no «ruptura» (N12)",
    r"\bconminut[ao]\b": "«multifragmentaria», no «conminuta» (N12)",
    r"\bRM\b[^\n]{0,30}\bsimple\b": "RM: «sin medio de contraste», no «simple» (v1.4)",
    r"\b(RM|resonancia)\b[^\n]{0,25}\bde cr[aá]neo\b": "RM «de cerebro», no «de cráneo» (v1.4)",
}
PERCEPCION = r"\b(se (observan?|identifican?|evidencian?|visualizan?|aprecian?|demuestran?)|observo|visualizo|identifico)\b"

# Palabras frecuentes que el dictado por voz deja sin tilde (forma sin tilde → forma correcta).
# Solo palabras sin homónimo válido sin tilde en el informe.
TILDES = dict(x.split(":") for x in """
relacion:relación ventriculo:ventrículo ventriculos:ventrículos perihepatico:perihepático esplenico:esplénico esplenica:esplénica hepatico:hepático hepatica:hepática sistolico:sistólico sistolica:sistólica diastolico:diastólico diastolica:diastólica
rotula:rótula trocanter:trocánter gluteo:glúteo biceps:bíceps triceps:tríceps cuadriceps:cuádriceps condilo:cóndilo epicondilo:epicóndilo metafisis:metáfisis diafisis:diáfisis epifisis:epífisis apofisis:apófisis lamina:lámina sacroiliaca:sacroilíaca iliaco:ilíaco iliaca:ilíaca calcaneo:calcáneo astragalo:astrágalo clavicula:clavícula escapula:escápula oseo:óseo osea:ósea oseos:óseos oseas:óseas esclerotico:esclerótico esclerotica:esclerótica litico:lítico litica:lítica blastico:blástico blastica:blástica ecogenico:ecogénico cubito:cúbito cartilago:cartílago retraccion:retracción insercion:inserción
lesion:lesión lesiones:lesiones region:región regiones:regiones higado:hígado pancreas:páncreas rinon:riñón rinones:riñones
vesicula:vesícula coledoco:colédoco apendice:apéndice mesenterico:mesentérico mesenterica:mesentérica adenopatia:adenopatía
adenopatias:adenopatías vertebra:vértebra vertebras:vértebras pediculo:pedículo acetabulo:acetábulo femur:fémur humero:húmero
perone:peroné aortico:aórtico aortica:aórtica embolo:émbolo parenquima:parénquima quistico:quístico quistica:quística
solido:sólido solida:sólida lobulo:lóbulo lobulos:lóbulos pulmon:pulmón pulmones:pulmones torax:tórax pelvico:pélvico pelvica:pélvica
medula:médula capsula:cápsula ulcera:úlcera musculo:músculo musculos:músculos tendon:tendón angulo:ángulo integro:íntegro
integra:íntegra simetrico:simétrico simetrica:simétrica asimetrico:asimétrico utero:útero ovarico:ovárico diametro:diámetro
maximo:máximo minimo:mínimo milimetros:milímetros centimetros:centímetros area:área numero:número tambien:también
segun:según traves:través evaluacion:evaluación disminucion:disminución resolucion:resolución laceracion:laceración
extravasacion:extravasación liquido:líquido examenes:exámenes opinion:opinión tecnica:técnica indicacion:indicación
comparacion:comparación craneo:cráneo encefalo:encéfalo hipofisis:hipófisis organo:órgano organos:órganos craneal:craneal
ileon:íleon colico:cólico cardiaco:cardíaco cardiaca:cardíaca hemorragico:hemorrágico hemorragica:hemorrágica
isquemico:isquémico isquemica:isquémica cronico:crónico cronica:crónica cronicos:crónicos agudo:agudo patologico:patológico
patologica:patológica fisiologico:fisiológico fisiologica:fisiológica limite:límite limites:límites calculo:cálculo calculos:cálculos
diafragmatico:diafragmático hilio:hilio pleural:pleural mediastinico:mediastínico mediastinica:mediastínica tiroides:tiroides
yuxtaposicion:yuxtaposición extension:extensión dilatacion:dilatación oclusion:oclusión compresion:compresión
herniacion:herniación desviacion:desviación fractura:fractura luxacion:luxación articulacion:articulación articulaciones:articulaciones
""".split() if x.split(":")[0] != x.split(":")[1])

SIDE = re.compile(r"\b(derech[oa]s?|izquierd[oa]s?|bilateral(es)?)\b", re.I)
NUM = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)?(?![\w])")
PROC = re.compile(r"\b(biopsia|drenaje|CPRE|resecci[oó]n|punci[oó]n|ablaci[oó]n|embolizaci[oó]n|colecistostom[ií]a|nefrostom[ií]a)\b", re.I)
UNIDAD = re.compile(r"\d(?:[.,]\d+)?\s*(mm²/s|mm2/s|mm|cm|cc|mL|ml|UH|HU|kPa|%)")
MEDIDA = re.compile(r"\d+(?:[.,]\d+)?\s*(mm|cm|cc|ml|mL|UH|%|kPa)\b")
CATEGORIA = re.compile(r"\b(RADS|AAST|SINS|AO|FIGO|TNM|Bosniak|Fleischner|Fardon|ASPECTS|Spetzler|Fisher|Weber|Garden|Schatzker|Salter|Neer|Gleason|grado|tipo|nivel)\b", re.I)


# v1.7 · voz narrativa (núcleo v1.4, N6–N8)
CERTEZA_INICIAL = re.compile(r"^(probables?|posibles?|posiblemente|probablemente|sospech\w*|sugestiv\w*|consistentes?|hallazgos (sugestivos|sospechosos|consistentes|en relaci[oó]n))\b", re.I)
NOMINAL = re.compile(r",\s*(compresi[oó]n|desplazamiento|contacto|obliteraci[oó]n|borramiento|infiltraci[oó]n|invasi[oó]n|estenosis)\s+(de|del|sobre|con)\b", re.I)
RELLENO = re.compile(r"\b(a nivel de(l)?|presencia de|de tipo|llama la atenci[oó]n|cabe (anotar|destacar|resaltar)|que corresponda a)\b", re.I)

# v1.9 · Opinión v2.0 (núcleo v2.2, N3, N7)
# Rótulo de Opinión, con las variantes de /alt («Opinión · sobria», «Opinión · asertiva»).
ROTULO_OPINION = re.compile(
    r"^[ \t]*(opini[oó]n|conclusi[oó]n|impresi[oó]n)(?:[ \t]*[·\-–][ \t]*(sobria|asertiva))?[ \t]*:?[ \t]*$", re.I | re.M)
ROTULO_INLINE = re.compile(r"^\s*(opini[oó]n|conclusi[oó]n|impresi[oó]n)\s*:", re.I | re.M)
# Prohibición 5 de N7: descriptor en lugar de diagnóstico. Se comparan sobre texto plano (sin tildes, minúsculas).
DESCRIPTOR = re.compile(
    r"^(?:\d+[.)]\s*)?(?:(?:el|la|los|las|un|una|unos|unas)\s+)?"
    r"(imagen(?:es)?|tejidos?|opacidad(?:es)?|hiperintensidad(?:es)?|hipointensidad(?:es)?|hipodensidad(?:es)?"
    r"|hiperdensidad(?:es)?|realces?|engrosamientos?|acunamientos?|perdida de (?:la )?altura"
    r"|aumento de (?:la )?densidad|disminucion de (?:la )?densidad|alteracion(?:es)? de (?:la )?senal"
    r"|cambios? de (?:la )?senal|areas? de|zonas? de|focos? de (?:hiper|hipo))\b")
DIAGNOSTICO = re.compile(
    r"\b(fractur|infarto|hemorragi|hematoma|neumoni|absceso|coleccion|neoplasi|tumor|metastasi|carcinoma|adenoma"
    r"|quiste|edema|isquemi|trombo|embolia|estenosis|hernia|rotura|luxacion|infeccion|inflamacion|\w+itis\b"
    r"|probable|sospechos|sugestiv|consistente con|posible|indeterminad|rads|categoria|grado|bosniak|aast"
    # v1.9: ampliación prudente (diagnósticos frecuentes que la lista base no cubría)
    r"|laceraci|contusi|necros|necrotic|aneurisma|diseccion|linfoma|sarcoma|enfermedad|malformaci|adenopati"
    r"|sin signos de)")
CONTEXTO = re.compile(r"\ben (?:el )?contexto de[^.;,]*", re.I)
BARRA = re.compile(r"(?<!\w)[^\W\d_]{4,}/[^\W\d_]{4,}(?!\w)")
# Rótulos de los bloques 2–4 (y notas de mantenimiento) que nunca van en el texto firmable.
BLOQUE = re.compile(
    r"^[ \t]*(?:[-•*][ \t]*)?(?:\*\*)?("
    r"falt[oó]:|considerar a[nñ]adir|antes de pegar|opini[oó]n propuesta:|opini[oó]n reconstruida:"
    r"|lecci[oó]n:|firmante:|redacci[oó]n:|aprendizaje:|→ ?maestro:|→ ?factory:"
    r"|\d[ \t]*·[ \t]*(?:informe refinado|cambios|seguridad|aprendizaje)\b"
    r"|descripci[oó]n:(?=[^\n]*(?:→|->|·[ \t]*falt[oó])))", re.I | re.M)
SIGLA = re.compile(r"[A-ZÑ]{3,5}")
SIGLAS_CLINICAS = set(
    "TC TAC RM RMN RX US TEP TVP HSA ACV LCA LCP LCM LCL VCS VCI AAST SINS RADS UH ADC FLAIR DWI SWI STIR "
    "PET SPECT ECMO EVAR TEVAR TIPS NMPI TNM FIGO "
    "ECO TORAX NOTA ANGIO".split())  # v1.9: la última fila son rótulos de plantilla de 3–5 letras
MILES = r"\d{1,3}(?:[    ]\d{3})+"
UH_VALOR = re.compile(r"(?<![\w.,])([-−–]?)(" + MILES + r"|\d+)(?:[.,]\d+)?\s*(?:UH|HU)\b")
PCT_VALOR = re.compile(r"(?<![\w.,])(" + MILES + r"|\d+)(?:[.,](\d+))?\s*%")


# v2.2 (M0 · P4): PRIVACIDAD, primera alerta. Datos que identifican a una persona en el texto firmable o en el bloque 3
# (N1-10). Solo con contexto (rótulo, tratamiento, firma, formato AGFA o el mismo nombre en el borrador): un apellido
# suelto, un epónimo («signo de Murphy», «Bosniak IIF») o la sigla del firmante nunca alertan. La comunicación que el
# radiólogo dicta (N11) conserva su nombre. Las alertas nunca repiten el dato: lo nombran por su tipo y su línea.
_MAY = r"[A-ZÁÉÍÓÚÑ]"
_MIN = r"[a-záéíóúñü]"
_PAL = _MAY + _MIN + r"+"
PRIV_ID = r"[A-Z]{0,2}(?:\d{1,3}(?:\.\d{3}){1,3}|\d{6,})(?![\d.,]*\d)"  # cuerpo de un documento: ≥6 cifras o miles con punto («TI 160-180» de RM no)
PRIV_DOC = re.compile(
    r"(?i:(?<![\w-])(?:c\.?\s?c\.?|t\.?\s?i\.?|r\.?\s?c\.?|c\.?\s?e\.?|nuip|pasaporte|c[eé]dula(?: de (?:ciudadan[ií]a|extranjer[ií]a))?"
    r"|tarjeta de identidad|registro civil|documento(?: de identidad)?|identificaci[oó]n|n[uú]mero de identificaci[oó]n)"
    r"(?![\w-])\s*(?:n[º°o]\.?|no\.|#|:|-)?\s*)" + PRIV_ID)
PRIV_HC = re.compile(
    r"(?i)(?<![\w-])(?:historia(?: cl[ií]nica)?|h\.\s?c\.|hc|n[uú]mero de historia|n\.?[º°o]\.? de historia|historia n[º°o]\.?"
    r"|n[uú]mero de (?:ingreso|admisi[oó]n|estudio|acceso)|accession|episodio)\s*(?:n[º°o]\.?|no\.|#|:|-)?\s*[A-Z]{0,3}\d[\d.\-]{3,}\d")
PRIV_NUM = re.compile(r"(?<![\w.,/:-])(?:\d{1,3}(?:\.\d{3}){2,}|\d{7,})(?![\w.,/:]*\d)(?!\s*(?:mm|cm|mL|ml|UH|HU|%|kPa|g|kg))")
PRIV_TEL = re.compile(
    r"(?i)(?:(?<![\w])(?:tel[eé]fono|tel\.|celular|cel\.|m[oó]vil|whatsapp|contacto)\s*(?:n[º°o]\.?|#|:)?\s*\+?\d[\d \-]{6,}\d"
    r"|(?<![\d,.x])(?:\+?57[ \-]?)?3\d{2}[ \-]?\d{3}[ \-]?\d{4}(?![\d,]))")
PRIV_CAMA = re.compile(r"(?i)(?<![\w])(?:cama|habitaci[oó]n|hab\.|cub[ií]culo|camilla)\s*(?:n[º°o]\.?|#|:|-)?\s*\d{1,4}[A-Za-z]?(?![\w])")
PRIV_NAC = re.compile(
    r"(?i)(?<![\w])(?:fecha de nacimiento|f\.\s?nac\.?|f\.\s?de\s?nac\.?|nacid[oa] el|naci[oó] el|fdn)(?:\s*:)?"
    r"(?:\s*\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}|\s+\d{1,2} de [a-z]+ de \d{4})?")
PRIV_FIRMA = re.compile(
    r"(?im)^[ \t]*(?:firma(?:do|da)?(?![\wáéíóúñ])(?: electr[oó]nicamente| digitalmente)?(?: por)?\s*:?|m[eé]dic[oa] (?:radi[oó]log[oa]|residente|tratante|que firma)\s*:"
    r"|radi[oó]log[oa] que firma|registro m[eé]dico|reg\.\s?m[eé]d\.?|r\.\s?m\.\s*(?:n[º°o]\.?)?\s*\d{3,}|tarjeta profesional|t\.\s?p\.\s*\d{3,})")
PRIV_TRATO = re.compile(
    r"(?<![\w])(?:Dr|Dra|Doctor|Doctora|Sr|Sra|Srta|Señor|Señora|Señorita|Enf|Lic|Ing)\.?(?:\(a\))?\s+((?:" + _PAL + r"|" + _MAY + r"{2,}(?![\w]))"
    r"(?:\s+(?:" + _PAL + r"|" + _MAY + r"{2,}(?![\w])))*)")
PRIV_ROTULO = re.compile(
    r"(?<![\w])(?i:nombres?(?: del paciente| completo)?|apellidos?|paciente|usuari[oa]|acompañante|madre|padre|familiar|responsable)\s*:\s*"
    r"(" + _MAY + r"[\wÁÉÍÓÚÑáéíóúñü]+(?:\s+" + _MAY + r"[\wÁÉÍÓÚÑáéíóúñü]+)*)")
PRIV_EDAD = re.compile(r"(?<![\w])(" + _PAL + r"(?:\s+" + _PAL + r"){1,3}),?\s+(?:de\s+)?\d{1,3}\s+(?:años|meses)(?!\s+de evoluci)")
PRIV_AGFA = re.compile(r"(?m)^[ \t]*(" + _MAY + r"{3,}(?: " + _MAY + r"{2,}){0,3}, ?" + _MAY + r"{3,}(?: " + _MAY + r"{2,}){0,2})[ \t]*$")
DEMOGRAFIA = set("paciente femenina femenino masculina masculino mujer hombre varon nino nina lactante recien neonato adulto adulta "
                 "gestante adolescente escolar preescolar anciano anciana senor senora de la el una un primigestante multigestante".split())
PRIV_COMUNICA = re.compile(r"(?i)\b(comunicad[oa]s?|se comunic|informad[oa]s? a|se inform|notificad[oa]s? a|se notific|se habl[oó] con|"
                           r"comentad[oa]s? con|se coment)")
MEDICAS_MAY = set("TC TAC RM RMN RX ECO ECOGRAFIA ECOGRAFÍA DOPPLER ANGIO ANGIOTC ANGIORM TOMOGRAFIA TOMOGRAFÍA RESONANCIA RADIOGRAFIA "
                  "RADIOGRAFÍA ABDOMEN PELVIS TORAX TÓRAX CRANEO CRÁNEO CEREBRO CUELLO COLUMNA RODILLA HOMBRO CADERA TOBILLO MUÑECA CODO "
                  "CON SIN CONTRASTE SIMPLE TOTAL MAGNETICA MAGNÉTICA COMPUTADA COMPUTARIZADA DE DEL Y LA EL LOS LAS HALLAZGOS OPINION "
                  "OPINIÓN TECNICA TÉCNICA INDICACION INDICACIÓN COMPARACION COMPARACIÓN ESTUDIO DERECHA DERECHO IZQUIERDA IZQUIERDO "
                  "BILATERAL CONTRASTADO CONTRASTADA PROTOCOLO FASE ARTERIAL VENOSA PORTAL TARDIA TARDÍA URGENCIAS".split())
# Primeros nombres frecuentes: alertan solo seguidos de un apellido con mayúscula («María Quintero»).
NOMBRES = set("""juan jose luis carlos jorge andres diego miguel pedro pablo javier alejandro daniel david felipe santiago sebastian
camilo julian oscar fernando ricardo mauricio hernan gustavo alvaro jaime german fabio edgar hector rafael manuel francisco antonio
alberto eduardo sergio mario raul hugo ivan wilson nelson freddy jhon john brayan kevin cristian nicolas mateo samuel tomas martin
emiliano jairo orlando rodrigo victor arturo enrique gabriel esteban alexander leonardo gerardo humberto alfonso ruben ramiro gilberto
maria ana luz carmen rosa martha marta gloria blanca sandra claudia diana paola patricia andrea carolina catalina natalia juliana
valentina daniela camila laura sofia isabella mariana gabriela alejandra angela beatriz cecilia esperanza fanny gladys liliana lucia
margarita mercedes monica nancy olga pilar rocio stella teresa yolanda ximena adriana alba amparo aura elsa elizabeth lorena marcela
milena nubia sara tatiana viviana yaneth yesenia jennifer lina leidy lady johana erika karen ingrid mary nelly dora ines josefa emilia
elena victoria clara fernanda antonia manuela salome valeria juana""".split())
# Epónimos y nombres propios de escalas: nunca son el nombre de una persona del borrador.
EPONIMOS = set("""joseph mary windermere lady murphy glisson bosniak fleischner couinaud morison douglas hounsfield wirsung santorini vater oddi treitz meckel crohn hodgkin
wilms graves hashimoto riedel spiegel bochdalek morgagni klatskin mirizzi caroli budd chiari monro silvio sylvio willis galeno rolando
luschka magendie virchow robin schmorl baker hoffa segond hill sachs bankart bennett lisfranc chopart jones colles smith barton monteggia
galeazzi salter harris kienbock kienböck perthes osgood schlatter sinding larsen pellegrini stieda haglund morton kager insall salvati hoh
gleason fazekas lugano deauville kioto kyoto atlanta balthazar tokio stanford debakey wells agatston gartner nabot bartholin skene cowper
brenner krukenberg meigs sertoli leydig peyronie fournier wilson wernicke korsakoff marchiafava bignami creutzfeldt jakob dandy walker
arnold blake rathke dorello hirschsprung ladd zenker killian boerhaave mallory weiss barrett schatzki menetrier whipple kerckring cantlie
rex calot hartmann kupffer rokitansky aschoff heister hamman kerley westermark hampton golden pancoast swyer james poland tietze mondor
paget cooper waldeyer rouviere troisier ewing codman sudeck charcot brodie garre ollier maffucci gorham jaffe lichtenstein waldt matcuk
child pugh milan lauren borrmann bismuth strasberg todani amsterdam rome roma tanner fisher hunt hess spetzler martin garden schatzker
neer weber danis frykman mayo gustilo tscherne pauwels denis magerl anderson levine effendi edwards evans sanders hawkins tile young
burgess letournel judet ficat steinberg kellgren lawrence outerbridge noyes pfirrmann modic fardon mcrae chamberlain wackenheim powers
cobb ferguson risser lenke king meyerding""".split())


def _plana(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def _es_eponimo(w):
    return _plana(w).strip(".,") in EPONIMOS


def _nombre_valido(tokens):
    """Un candidato a nombre: al menos un token de ≥3 letras que no sea epónimo, rótulo médico ni demografía."""
    ws = [t for t in tokens if len(t) >= 3]
    return bool(ws) and not all(_es_eponimo(t) or t.upper() in MEDICAS_MAY or _plana(t) in DEMOGRAFIA for t in ws)


def _nombres_en(texto):
    """[(tipo, tokens, span)] de nombres de persona con contexto en el texto."""
    out = []
    for m in PRIV_TRATO.finditer(texto):
        tk = m.group(1).split()
        if _nombre_valido(tk):
            out.append(("nombre de persona", tk, m.group(0)))
    for m in PRIV_ROTULO.finditer(texto):
        tk = m.group(1).split()
        if _plana(tk[0]) not in DEMOGRAFIA and _nombre_valido(tk):
            out.append(("nombre de persona", tk, m.group(0)))
    for m in PRIV_EDAD.finditer(texto):
        tk = m.group(1).split()
        if _plana(tk[0]) not in DEMOGRAFIA and not any(_es_eponimo(t) for t in tk) and _nombre_valido(tk):
            out.append(("nombre de persona", tk, m.group(1)))
    for m in re.finditer(r"(?<![\w])(" + _PAL + r")\s+(" + _PAL + r"(?:\s+" + _PAL + r")?)", texto):
        if _plana(m.group(1)) in NOMBRES and not _es_eponimo(m.group(2).split()[0]):
            out.append(("nombre de persona", [m.group(1)] + m.group(2).split(), m.group(0)))
    for m in PRIV_AGFA.finditer(texto):
        tk = re.findall(r"\w+", m.group(1))
        if not any(t in MEDICAS_MAY for t in tk) and _nombre_valido(tk):
            out.append(("nombre de persona", tk, m.group(1)))
    return out


def _firma_tokens(borrador):
    """Nombres de las últimas líneas del borrador (firma pegada, Δ-R8 (4)): «Dr./Dra. Apellido» o «Apellidos, Nombres»."""
    cola = "\n".join([l for l in (borrador or "").splitlines() if l.strip()][-3:])
    return [t for _, tk, _ in _nombres_en(cola) for t in tk]


def privados(texto, borrador=None):
    """[(tipo, nº de línea, span)] de datos que identifican a una persona en el texto, sin la comunicación dictada (N11)."""
    out, bp = [], _plana(borrador or "")
    lineas = texto.splitlines()
    tok_borr = set()
    for _, tk, _ in _nombres_en(borrador or ""):
        tok_borr.update(_plana(t) for t in tk if len(t) >= 3 and not _es_eponimo(t) and t.upper() not in MEDICAS_MAY and _plana(t) not in DEMOGRAFIA)
    tok_borr.update(_plana(t) for t in _firma_tokens(borrador) if len(t) >= 3 and not _es_eponimo(t))
    for i, l in enumerate(lineas, 1):
        comunica = bool(PRIV_COMUNICA.search(l))
        hall = []
        for rx, tipo in ((PRIV_DOC, "documento de identidad"), (PRIV_HC, "número de historia"), (PRIV_TEL, "teléfono"),
                         (PRIV_CAMA, "cama o habitación"), (PRIV_NAC, "fecha de nacimiento"), (PRIV_FIRMA, "firma")):
            hall += [(tipo, m.group(0)) for m in rx.finditer(l)]
        if not any(t == "documento de identidad" or t == "número de historia" or t == "teléfono" for t, _ in hall):
            hall += [("documento de identidad", m.group(0)) for m in PRIV_NUM.finditer(l)
                     if not re.search(r"(?i)(pmid|doi|isbn|issn|nct)\W{0,3}$", l[max(0, m.start() - 8):m.start()])]
        for tipo, tk, span in _nombres_en(l):
            if comunica and all(_plana(t) in bp for t in tk if len(t) >= 3):
                continue  # N11: la comunicación que el radiólogo dictó, con su nombre
            hall.append((tipo, span))
        for w in re.findall(r"[\wÁÉÍÓÚÑáéíóúñü]{3,}", l):
            if _plana(w) in tok_borr and (w[0].isupper()) and not (comunica and _plana(w) in bp) and not any(w in s for _, s in hall):
                hall.append(("nombre de persona", w))
        out += [(t, i, s) for t, s in hall]
    return out


def chequear_privacidad(texto, borrador, donde):
    """Alertas PRIVACIDAD (una por tipo y línea) y los spans a enmascarar en las demás alertas."""
    al, spans = [], []
    for tipo, i, s in privados(texto or "", borrador):
        a = f"PRIVACIDAD · {tipo} en el {donde}, línea {i}: quítalo; nunca entra al informe ni a la respuesta (N1-10)"
        if a not in al:
            al.append(a)
        spans.append(s)
    return al, spans


def enmascarar(texto, spans):
    """Las demás alertas citan el bloque 1: el dato personal sale como «‹dato personal›»."""
    for s in sorted(set(x for x in spans if x and x.strip()), key=len, reverse=True):
        texto = texto.replace(s, "‹dato personal›")
    return texto



def norm(s):
    return unicodedata.normalize("NFC", s)


def plano(s):
    """v1.9: minúsculas y sin tildes (ñ → n) para comparar términos sin depender de la ortografía."""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def secciones(texto):
    """Separa Hallazgos y Opinión por su rótulo; si no hay rótulos, todo es Hallazgos."""
    m = ROTULO_OPINION.search(texto)
    if not m:
        m = ROTULO_INLINE.search(texto)
    if not m:
        return texto, ""
    return texto[:m.start()], texto[m.end():]


def opiniones(texto):
    """v1.9: Hallazgos y lista de Opiniones [(etiqueta, texto)]; con /alt hay dos («sobria», «asertiva»)."""
    rotulos = list(ROTULO_OPINION.finditer(texto))
    if not rotulos:
        hall, opin = secciones(texto)
        return hall, ([("", opin)] if opin.strip() else [])
    lista = []
    for i, m in enumerate(rotulos):
        fin = rotulos[i + 1].start() if i + 1 < len(rotulos) else len(texto)
        lista.append(((m.group(2) or "").lower(), texto[m.end():fin]))
    if len(lista) > 1:
        lista = [(et or f"opinión {k + 1}", t) for k, (et, t) in enumerate(lista)]
    else:
        lista = [("", lista[0][1])]
    return texto[:rotulos[0].start()], [(et, t) for et, t in lista if t.strip() or len(lista) > 1]


def ideas_de(opin):
    """v1.9: una idea = un párrafo (separado por líneas en blanco) o una línea que abre con numeración.
    Devuelve listas de líneas; se ignoran las líneas de rótulo y las que empiezan por «[»."""
    ideas, actual = [], []
    for linea in opin.splitlines():
        l = linea.strip()
        if not l:
            if actual:
                ideas.append(actual)
                actual = []
            continue
        if l.startswith("[") or ROTULO_OPINION.match(l):
            continue
        if actual and re.match(r"\d+[.)]\s", l):
            ideas.append(actual)
            actual = []
        actual.append(l)
    if actual:
        ideas.append(actual)
    return ideas


def frases_norm(texto):
    """v1.9: frases (separadas por «.», «;» o salto de línea) normalizadas para comparar Opinión y Hallazgos."""
    salida = []
    for f in re.split(r"[.;\n]", texto):
        f = re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", plano(f))).strip()
        f = re.sub(r"^\d+\s+", "", f)
        if f:
            salida.append(f)
    return salida


def numeros(texto):
    sin_marcadores = re.sub(r"\[[^\]]*\]", " ", texto)
    sin_marcadores = re.sub(r"\b\d{1,3}(?:\.\d{3}){2,}\b|\b\d{6,}\b", " ", sin_marcadores)  # v1.5: documentos y teléfonos nunca se comparan ni se imprimen
    sin_marcadores = re.sub(r"(?m)^\s*\d+[.)]\s", " ", sin_marcadores)  # numeración de la Opinión
    sin_marcadores = re.sub(r"(?<=[:.]\s)\d{1,2}[.)]\s", " ", sin_marcadores)  # v1.7: numeración pegada en una sola línea («Opinión: 1. … 2. …»)
    sin_marcadores = re.sub(r"\b[\w-]*RADS\s+\d+\w*(?:/[\w+]+)*", " ", sin_marcadores)  # v1.4: categoría derivada
    return {n.replace(",", ".") for n in NUM.findall(sin_marcadores)}


def negaciones(texto):
    """v1.4: «no hay X», «no se identifica X», «sin evidencia de X», «sin signos de X» y «sin X» cuentan como UNA negación."""
    t = re.sub(r"\bno\s+(hay|se\s+(identifica|identifican|observa|observan|evidencia|evidencian|visualiza|visualizan|aprecia|aprecian)|presenta|presentan|muestra|muestran)\b", " NEG ", texto, flags=re.I)
    t = re.sub(r"\bsin\s+(medio\s+de\s+)?contraste\b", " ", t, flags=re.I)  # técnica, no hallazgo
    t = re.sub(r"\bsin\s+relaci[oó]n\s+con\s+(el|la)\s+\w+(\s+agud[oa])?\b", " ", t, flags=re.I)  # v1.8: cierre de Hickam (N7), no es un hallazgo negativo
    t = re.sub(r"\bsin\s+(evidencia|signos|imagen|im[aá]genes)\s+de\b", " NEG ", t, flags=re.I)
    t = re.sub(r"\b(sin|no)\b", " NEG ", t, flags=re.I)
    return len(re.findall(r"\bNEG\b", t))


# v2.0 (D-221): umbrales por nivel de extensión (N6b): 1 conciso · 2 neutro · 3 extenso
EXTENSION = {1: {"oracion": 20, "oraciones": None, "idea1": 20, "otras": 20, "ideas": 3},
             2: {"oracion": 30, "oraciones": 3, "idea1": 35, "otras": 50, "ideas": 4},
             3: {"oracion": 40, "oraciones": 4, "idea1": 50, "otras": 50, "ideas": 5}}


def palabras(s):
    """v2.0: palabras de contenido para los topes de extensión: sin la etiqueta «Estructura:», cifras, unidades ni la «x» de las medidas."""
    s = re.sub(r"^[^:\n]{1,30}:\s*", "", s.strip())
    return len([w for w in re.findall(r"[^\W\d_]+", s) if w.lower() not in ("x", "mm", "cm", "ml", "mm2", "s", "uh")])


def chequear_extension(hall, n):
    """v2.0: palabras por oración y oraciones por hallazgo (una línea = un hallazgo) en Hallazgos, según el nivel."""
    alertas, e = [], EXTENSION[n]
    for linea in hall.splitlines():
        l = re.sub(r"\[[^\]]*\]", "", linea).strip()
        if not re.search(r"\w", l) or ROTULO_OPINION.match(l):
            continue
        frases = [f for f in re.split(r"(?<=[.;])\s+", l) if re.search(r"\w", f)]
        for f in frases:
            k = palabras(f)
            if k > e["oracion"]:
                alertas.append(f"EXTENSIÓN {n} · oración de {k} palabras en Hallazgos (≤{e['oracion']} en este nivel) · «{f[:50]}…»")
        if e["oraciones"] and len(frases) > e["oraciones"]:
            alertas.append(f"EXTENSIÓN {n} · hallazgo en {len(frases)} oraciones (≤{e['oraciones']} en este nivel) · «{l[:50]}…»")
    return alertas


def chequear_opinion(opin, hall, pref="", extension=None):
    """Chequeos de una Opinión (v1.9: se corre una vez por Opinión; con /alt, prefijo [sobria] / [asertiva]).
    v2.0: con «extension», los topes de ideas y de palabras salen de EXTENSION (la recomendación «Se sugiere…» no cuenta)."""
    alertas = []
    ideas = ideas_de(opin)
    e = EXTENSION.get(extension)
    if e:
        n_ideas = len([i for i in ideas if not re.match(r"(\d+[.)]\s*)?se sugiere\b", " ".join(i).strip(), re.I)])
        if n_ideas > e["ideas"]:
            alertas.append(f"{pref}EXTENSIÓN {extension} · {n_ideas} ideas en la Opinión (≤{e['ideas']} en este nivel; ideas ≤ procesos, N7)")
    elif len(ideas) > 5:  # v1.9: ideas ≤ procesos; antes, tope 3–4
        alertas.append(f"{pref}OPINIÓN · {len(ideas)} ideas: ¿cada una es un proceso distinto? (N7: ideas ≤ procesos)")
    frases_hall = {f for f in frases_norm(hall) if len(f.split()) >= 8}
    for k, lineas in enumerate(ideas):
        lineas = [re.sub(r"^\d+[.)]\s*", "", lineas[0])] + lineas[1:]
        cuerpo = " ".join(lineas)
        texto = re.sub(r"\[[^\]]*\]", "", cuerpo)  # v1.2: los marcadores no cuentan
        for linea in lineas:  # cada línea abre una frase (N3: nunca un salto dentro de una frase)
            tl = re.sub(r"\[[^\]]*\]", "", linea).strip()
            mc = CERTEZA_INICIAL.match(tl)
            sig = re.match(r"\S+\s+(\w+)", tl)
            duda_existencia = bool(mc and sig and re.search(r"\b(posibles?|probables?|parece|aparente)\s+(un[ao]?\s+)?" + re.escape(sig.group(1)), hall, re.I))
            if mc and not duda_existencia:
                alertas.append(f"{pref}ORDEN · la idea abre con el término de certeza: abre con el hallazgo cierto y pon el término sobre el diagnóstico («Masa hepática, sospechosa de colangiocarcinoma»); se conserva solo si Hallazgos duda de la existencia del hallazgo · «{linea[:60]}»")
        if ":" in texto:
            alertas.append(f"{pref}OPINIÓN · dos puntos en una idea · «{cuerpo[:60]}»")
        for m in MEDIDA.finditer(texto):
            alertas.append(f"{pref}OPINIÓN · medida en la Opinión (solo si el tamaño ES el criterio o es excepción del delta) · «{m.group(0)}»")
        n = len(cuerpo.split())
        tope = 100 if k == 0 else 50  # v1.9: guía idea 1 ≈60 y el resto cortas; el tope es una señal
        if e and not re.match(r"(\d+[.)]\s*)?se sugiere\b", cuerpo.strip(), re.I):
            tope_e, n_e = (e["idea1"] if k == 0 else e["otras"]), palabras(texto)
            if n_e > tope_e:
                alertas.append(f"{pref}EXTENSIÓN {extension} · idea {k + 1} de {n_e} palabras (≤{tope_e} en este nivel) · «{cuerpo[:50]}…»")
        elif e:
            pass
        elif n > tope:
            alertas.append(f"{pref}OPINIÓN · idea de {n} palabras (guía: idea 1 ≈60, el resto cortas; es una señal, no un tope) · «{cuerpo[:50]}…»")
        # v1.9 · N7: la respuesta, no el descriptor ni el contexto
        respuesta = plano(CONTEXTO.sub(" ", texto))
        con_diagnostico = bool(DIAGNOSTICO.search(respuesta))
        if CONTEXTO.search(texto) and not con_diagnostico:
            alertas.append(f"{pref}OPINIÓN · «en el contexto de» no sustituye la respuesta: nombra el diagnóstico que explica la indicación (N7) · «{cuerpo[:60]}»")
        elif DESCRIPTOR.match(plano(texto.strip())) and not con_diagnostico:
            alertas.append(f"{pref}OPINIÓN · la idea abre con un descriptor y no nombra un diagnóstico: traduce el descriptor (acuñamiento → fractura; ganglio con centro hipodenso → adenopatía necrótica) o conserva el descriptor solo si ES el hallazgo (N7-5) · «{cuerpo[:60]}»")
        for frase in re.split(r"[.;]", texto):
            fn = frases_norm(frase)
            if fn and len(fn[0].split()) >= 8 and fn[0] in frases_hall:
                alertas.append(f"{pref}OPINIÓN · frase idéntica a una de Hallazgos: la Opinión sintetiza, no repite (N7) · «{frase.strip()[:60]}»")
        for m in BARRA.finditer(texto):
            alertas.append(f"{pref}OPINIÓN · dos opciones unidas por «/»: ordénalas con su certeza («probablemente X; Y menos probable») (N7, N9) · «{m.group(0)}»")
    lados_h = {s.lower()[:5] for s in SIDE.findall(hall) for s in [s[0] if isinstance(s, tuple) else s]}
    opin_lado = re.sub(r"\b(ventr[ií]culo|aur[ií]cula|coraz[oó]n|cavidades)\s+(derech|izquierd)\w*", " ", opin, flags=re.I)
    for m in SIDE.finditer(opin_lado):  # v1.9: sin la excepción [VERIFICAR LADO] (el bloque 1 no lleva corchetes)
        if m.group(1).lower()[:5] not in lados_h:
            alertas.append(f"{pref}LADO · «{m.group(1)}» en la Opinión no aparece en Hallazgos → corrígelo si el borrador lo resuelve; si no, aviso «Antes de pegar» (N2)")
    return alertas


CERTEZAS = ("consistente con", "menos probable", "improbable", "probablemente", "probable", "sospechos", "sugestiv", "posible", "indeterminad")
CLINICO = re.compile(r"\b(edad|anos|antecedente|clinic|sintoma|fiebre|dolor|laboratorio|leucocit|pcr|bilirrubin|creatinin|hcg|"
                     r"embaraz|historia|tratamiento|quimioterapia|cirugia previa|estudio previo|previo|comparacion|antiguedad)", re.I)
VACIAS_F = set("faltó falto para sobre entre desde hasta como cual cuál cuales donde tiene tienen está están esta este estos estas otra otro".split())


def falto_elementos(b3):
    """v2.1: elementos de la línea «Faltó: ¿…?» del bloque 3 (coma, punto y coma, «·», «¿…?» separados, y el último «y»)."""
    m = re.search(r"Falt[oó][^:]*:\s*(.+)", b3 or "")
    if not m:
        return []
    cuerpo = re.split(r"\n", m.group(1))[0]
    partes = [x for x in re.split(r"[,;·]|\?\s*¿", cuerpo) if x.strip(" ¿?.")]
    if partes:
        partes[-1:] = [x for x in re.split(r"\s+y\s+", partes[-1]) if x.strip(" ¿?.")]
    return [x.strip(" ¿?.") for x in partes]


def chequear_bloque3(b3, salida, borrador):
    """v2.1 (r16): el filtro del «Faltó» y el «Llamar» = Opinión."""
    al, bp = [], plano(borrador or "")
    els = falto_elementos(b3)
    if len(els) > 3:
        al.append(f"FALTO-N · el «Faltó» trae {len(els)} elementos: deja ≤3, los que cambian el manejo de hoy o la categoría (N6)")
    for e in els:
        if CLINICO.search(plano(e)):
            al.append(f"FALTO-CLINICO · «{e}» no se ve en la imagen (clínica, antecedente, edad o previo): fuera del «Faltó» (N6)")
            continue
        ws = [w for w in re.findall(r"[a-z]{4,}", plano(e)) if w not in VACIAS_F]
        if bp and ws and all(w[:5] in bp for w in ws):
            al.append(f"FALTO-DICTADO · «{e}» ya está dictado (o su sinónimo): fuera del «Faltó» (N6)")
    _, ops = opiniones(salida)
    ideas = [" ".join(i) for _, o in ops for i in ideas_de(o)]
    for l in (b3 or "").splitlines():
        m = re.search(r"Llamar\s*:\s*([^·\n]+)", l)
        if not m or not ideas:
            continue
        ll = plano(m.group(1))
        ws = set(re.findall(r"[a-z]{5,}", ll))
        idea = max(ideas, key=lambda i: len(ws & set(re.findall(r"[a-z]{5,}", plano(i)))))
        ci, cl = {c for c in CERTEZAS if c in plano(idea)}, {c for c in CERTEZAS if c in ll}
        if ci != cl:
            al.append(f"LLAMAR-CERTEZA · «Llamar: {m.group(1).strip()}» debe copiar el diagnóstico y el término de certeza de su idea de la Opinión (N11)")
    return al


def verificar(salida, borrador=None, extension=None, bloque3=None):
    """Devuelve la lista de alertas (sin duplicados, en orden) del bloque 1 propuesto. v2.0: extension 1|2|3 (N6b) o None (= v1.9).
    v2.1: bloque3 (texto del bloque 3) añade FALTO-* y LLAMAR-CERTEZA; con borrador, OPI-NUM1."""
    extension = int(extension) if extension else None
    salida = norm(salida)
    borrador = norm(borrador) if borrador is not None else None
    # v2.2 (M0 · P4): PRIVACIDAD primero; el dato se enmascara antes de los demás chequeos, que así nunca lo repiten
    priv, spans = chequear_privacidad(salida, borrador, "bloque 1")
    if bloque3:
        bloque3 = norm(bloque3)
        p3, s3 = chequear_privacidad(bloque3, borrador, "bloque 3")
        priv, spans = priv + p3, spans + s3
    spans += [s for _, _, s in privados(borrador or "")]
    verificar.privados = spans
    salida = enmascarar(salida, spans)
    borrador = enmascarar(borrador, spans) if borrador is not None else None
    bloque3 = enmascarar(bloque3, spans) if bloque3 else bloque3
    alertas = []
    hall, lista_opin = opiniones(salida)

    # v1.9: sigla del firmante aislada al inicio (Δ-R8)
    primera = next((l.strip() for l in salida.splitlines() if l.strip()), "")
    if SIGLA.fullmatch(primera) and primera not in SIGLAS_CLINICAS:
        alertas.append(f"SIGLA · «{primera}» aislado al inicio del bloque 1: si es la sigla del firmante, quítala (Δ-R8); el nombre o la sigla nunca entran al informe")
    # v1.9: líneas de los bloques 2–4 dentro del bloque 1
    for m in BLOQUE.finditer(salida):
        alertas.append(f"BLOQUE · «{m.group(1).rstrip(':').strip()}» pertenece a los bloques 2–3, no al informe (N3, N6)")

    for patron, msg in RETIRADOS.items():
        for m in re.finditer(patron, salida, re.I):
            alertas.append(f"TÉRMINO · {msg} · «{m.group(0)}»")
    for m in re.finditer(PERCEPCION, hall, re.I):
        alertas.append(f"PERCEPCIÓN · verbo de percepción en Hallazgos (salvo texto fijo de plantilla, declarado) · «{m.group(0)}»")

    for m in re.finditer(r"\[[^\]]*\]", salida):  # v1.8: el bloque 1 no lleva corchetes (núcleo N2 v1.8); la duda va al aviso «Antes de pegar»
        alertas.append(f"MARCADOR · el bloque 1 no lleva corchetes: corrígelo o súbelo al aviso «Antes de pegar» (N2) · «{m.group(0)}»")

    for m in re.finditer(r"(?<![\w.])\d+\.\d+(?!\w|\.\d)", salida):  # v1.3: también al final de frase
        alertas.append(f"DECIMAL · usar coma decimal (salvo texto fijo de plantilla) · «{m.group(0)}»")
    for m in re.finditer(r"\d\s*[×X*]\s*\d", salida):
        alertas.append(f"FORMATO · usar «x» minúscula entre medidas · «{m.group(0)}»")
    for m in re.finditer(r"\d(mm|cm|cc|mL|ml)\b", salida):
        alertas.append(f"ESPACIO · número y unidad separados («6 mm») · «{m.group(0)}»")

    # v1.9: valores fuera de rango físico (N1-9)
    for m in UH_VALOR.finditer(salida):
        valor = int(re.sub(r"\D", "", m.group(2))) * (-1 if m.group(1) else 1)
        if valor < -1100 or valor > 4000:
            alertas.append(f"RANGO · «{m.group(0).strip()}» fuera del rango físico: duda que solo resuelve la imagen → aviso «Antes de pegar» (N1-9)")
    for m in PCT_VALOR.finditer(salida):
        valor = float(re.sub(r"\D", "", m.group(1)) + "." + (m.group(2) or "0"))
        if valor > 100 and not re.search(r"aument|increment|crec", plano(salida[max(0, m.start() - 40):m.start()])):
            alertas.append(f"RANGO · «{m.group(0).strip()}» mayor de 100")

    for palabra in re.findall(r"\b[a-záéíóúñü]+\b", salida, re.I):
        correcta = TILDES.get(palabra.lower())
        if correcta:
            alertas.append(f"TILDE · «{palabra}» → «{correcta}»")

    # v1.8: variedad léxica en Hallazgos (N6)
    n_hay = len(re.findall(r"\bhay\b", hall, re.I))
    if n_hay > 2:
        alertas.append(f"REPETICIÓN · «hay» aparece {n_hay} veces en Hallazgos (máximo 2): usa el verbo que dice qué hace o qué es el hallazgo (N6)")
    primeras = [re.findall(r"\w+", l.lower())[:1] for l in hall.splitlines() if re.search(r"\w", l)]
    primeras = [x[0] for x in primeras if x]
    for i in range(len(primeras) - 2):
        if primeras[i] == primeras[i + 1] == primeras[i + 2] and primeras[i] not in ("el", "la", "los", "las"):
            alertas.append(f"REPETICIÓN · tres hallazgos seguidos abren con «{primeras[i]}» (N6)")
            break

    # v1.7: voz narrativa
    for m in NOMINAL.finditer(salida if extension != 1 else "\n".join(t for _, t in lista_opin)):  # v2.0: con 1, línea nominal en Hallazgos
        alertas.append(f"VOZ · sustantivo tras coma donde va un verbo («que comprime», «que desplaza»; nunca un verbo más fuerte que el dictado) · «{m.group(0).strip(', ')}»")
    for m in RELLENO.finditer(salida):
        alertas.append(f"VOZ · relleno («a nivel de» → «en»; los demás se eliminan), salvo texto fijo de plantilla · «{m.group(0)}»")

    # v1.6: procedimiento recomendado fuera de la forma de N9
    for frase in re.split(r"(?<=[.])\s+|\n", salida):
        if re.search(r"\bse sugiere\b", frase, re.I) and PROC.search(frase) and not re.search(r"(guiad|dirigid)[ao]s? por|centro de referencia de sarcoma", frase, re.I):
            alertas.append(f"PROCEDIMIENTO · fuera de la forma «Se sugiere [procedimiento] guiado por [modalidad] para [objetivo].»: si es dictado, conserva la intención y decláralo; si es tuyo, solo con respaldo de un archivo cargado (N9) · «{frase.strip()[:70]}»")

    for etiqueta, opin in lista_opin:  # v1.9: con /alt, cada Opinión por separado y con prefijo
        alertas += chequear_opinion(opin, hall, f"[{etiqueta}] " if etiqueta else "", extension)
    if extension in EXTENSION:
        alertas += chequear_extension(hall, extension)

    if borrador is not None:
        nb, ns = numeros(borrador), numeros(salida)
        for n in sorted(nb - ns, key=lambda x: float(x)):
            alertas.append(f"CIFRA · «{n}» está en el borrador y no en la salida (¿se perdió o cambió?)")
        for n in sorted(ns - nb, key=lambda x: float(x)):
            alertas.append(f"CIFRA · «{n}» es nueva respecto al borrador (solo válida si es un cálculo declarado, p. ej. volumen)")
        def unidades(t):
            t = re.sub(r"\[[^\]]*\]", " ", t)
            return {{"ml": "mL", "HU": "UH", "mm2/s": "mm²/s"}.get(u, u) for u in UNIDAD.findall(t)}
        for u in sorted(unidades(borrador) - unidades(salida)):
            alertas.append(f"UNIDAD · «{u}» del borrador no aparece en la salida: declara el cambio (nunca conviertas unidades salvo excepción del delta)")
        hall_b, _ = secciones(borrador)
        neg_b = negaciones(hall_b if hall_b.strip() else borrador)  # v1.8: se comparan Hallazgos; «Sin signos de…» en la Opinión responde la indicación
        neg_s = negaciones(hall)
        if neg_s > neg_b:
            alertas.append(f"NEGACIÓN · la salida tiene {neg_s - neg_b} negación(es) más que el borrador: confirma que ninguna es un negativo no dictado")
        _, ob = opiniones(borrador)
        for etiqueta, opin in lista_opin:  # v2.1 (r16): una sola idea sin «1.», salvo que el borrador numere (la huella o E: decláralo)
            ids = ideas_de(opin)
            if len(ids) == 1 and re.match(r"1[.)]\s", ids[0][0]) and not any(re.search(r"(?m)^\s*1[.)]\s", o) for _, o in ob):
                alertas.append(f"{'[' + etiqueta + '] ' if etiqueta else ''}OPI-NUM1 · una sola idea va sin «1.» (N7), salvo que el borrador, la huella o la sección E numeren")
    if bloque3:
        alertas += chequear_bloque3(bloque3, salida, borrador)

    vistos = []
    for a in priv + [enmascarar(x, spans) for x in alertas]:
        if a not in vistos:
            vistos.append(a)
    return vistos


def main():
    if len(sys.argv) < 2:
        print(__doc__.split("\nHistorial")[0])
        return
    args, ext = list(sys.argv[1:]), None
    if "--extension" in args:  # v2.0 (D-221)
        i = args.index("--extension"); ext = args[i + 1]; del args[i:i + 2]
        if ext not in ("1", "2", "3"):
            print("--extension: 1 (conciso), 2 (neutro) o 3 (extenso)", file=sys.stderr)
            sys.exit(2)
    b3 = None
    if "--bloque3" in args:  # v2.1 (r16)
        i = args.index("--bloque3"); b3 = open(args[i + 1], encoding="utf-8").read(); del args[i:i + 2]
    salida = open(args[0], encoding="utf-8").read()
    borrador = open(args[1], encoding="utf-8").read() if len(args) > 1 else None
    vistos = verificar(salida, borrador, ext, b3)
    if vistos:
        print(f"ALERTAS · {len(vistos)}")
        print("\n".join(vistos))
    else:
        print("OK · sin alertas")


if __name__ == "__main__":
    main()
#END_SCRIPT
```
