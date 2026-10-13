---
name: "verificador-informe-radiologico"
description: "Holds the deterministic report checker used by four radiology report copilots (Claude RADS, NeuroRadio, RM de cuerpo, MSK). Their instructions extract and run it with one bash command before emitting block 1."
---

# Verificador del informe radiológico · v1.9 (2026-10-11)

The copilots' project files are no longer mounted as a folder in chat (checked 2026-10-04: no `/mnt/project`), but account and plugin skills are (under `/mnt/skills`; this one ships in the plugin `radiologia-informes`, with the same script also in `scripts/verificar_informe.py`). This skill only stores the checker; nothing here needs to be read into context.

## Run it (one bash call)
Save the proposed block 1 to `/tmp/salida.txt` and the pasted draft to `/tmp/borrador.txt`, then:

```
V=/tmp/verificar_informe.py; [ -s "$V" ] || sed -n '/^#BEGIN_SCRIPT$/,/^#END_SCRIPT$/p' "$(find /mnt/skills -path '*verificador-informe-radiologico*' -name SKILL.md 2>/dev/null | head -1)" > "$V"; python3 "$V" /tmp/salida.txt /tmp/borrador.txt
```

The first call of a conversation extracts the script to `/tmp`; later calls reuse it. Output: «OK · sin alertas» or one alert per line. With `/alt`, put both Opiniones in the same file under the plain lines «Opinión · sobria» and «Opinión · asertiva»: one run checks each one separately and prefixes its alerts with `[sobria]` or `[asertiva]` (or run it once per version). Resolve every alert: fix it, or keep it and declare why. If the command finds no script, say so in block 3 and check by hand.

## Source of truth
`RADS/04 KB Markdown/_homogeneizacion/compartidos/verificar_informe.py`. When it changes, this skill is updated with the identical text. v1.2: markers like `[COMPLETAR: lado]` no longer trigger the colon or measurement alerts in the Opinión. v1.3: a decimal point at the end of a sentence («1.2.») is caught; body words added to the accent list (relación, ventrículo, hepático, esplénico, sistólico, diastólico…). v1.4: «RM … simple» and «RM de cráneo» are flagged; equivalent negations («no hay», «no se identifica», «sin evidencia de», «sin») count once and «sin contraste» is technique, not a negation; RADS category numbers («PE-RADS 3/RV+») no longer count as new figures. v1.5: ID and phone numbers («1.234.567», six or more digits) are never compared or printed, so a removed identifier never reappears in an alert. v1.6: PROCEDIMIENTO alert when a «Se sugiere» sentence names a procedure outside the N9 form (dictated → keep the intent and declare it), and UNIDAD alert when a unit of the draft disappears from the output (declare it; never convert). v1.7: narrative voice (core v1.4) — ORDEN alert when an Opinión idea opens with a certainty term, VOZ alerts for a verbless noun after a comma («, compresión de») and for filler («a nivel de», «presencia de», «que corresponda a»); ORDEN stays quiet when Hallazgos carries the same existence hedge («posible nódulo»); Opinión numbering pasted on one line («Opinión: 1. … 2. …») no longer counts as figures. v1.8: idea 1 of the Opinión may reach 80 words (integrated prose); «sin relación con el cuadro» is not a negation; negations are compared within Hallazgos; any bracket in block 1 is an alert; REPETICIÓN alerts for «hay» over twice and three findings opening with the same word. v1.9 (instruction v2.0, core v2.2): prose in the Opinión is no longer penalized — an idea is a paragraph (or a numbered line), the idea-count alert fires only above 5, and the word limits (idea 1 ≤100, the rest ≤50) are signals; new Opinión alerts for an idea that opens with a descriptor and names no diagnosis, «en el contexto de» with no answer, a sentence copied from Hallazgos and two options joined by «/»; BLOQUE alert for block 2–4 lines inside block 1 («Descripción: … →», «Faltó:», «Considerar añadir», «Antes de pegar», «Lección:», «Firmante:», «→ Maestro:»…); SIGLA alert for an isolated 3–5 capital token opening block 1 (a signer's sigla); RANGO alert for UH outside −1100…4000 or a percentage above 100; «Opinión · sobria» / «Opinión · asertiva» labels; the old `[VERIFICAR LADO]` exception is gone. Tests: `tests/test_verificar_v19.py` (`python3 -m unittest discover -s tests`).

```python
#BEGIN_SCRIPT
#!/usr/bin/env python3
"""verificar_informe.py · v1.9 (2026-10-11) · archivo compartido idéntico en los 4 copilotos.

Chequeo determinista del bloque 1 antes de emitirlo. No corrige: lista ALERTAS para que el modelo
las resuelva (corregir o declarar). Se ejecuta, no se lee: su texto no entra al contexto.

Uso:  python3 verificar_informe.py salida.txt [borrador.txt]
      (salida = bloque 1 propuesto; borrador = lo que el radiólogo pegó, opcional pero recomendado)
Sale con código 0 siempre; imprime «OK · sin alertas» o una alerta por línea.

Historial
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


def chequear_opinion(opin, hall, pref=""):
    """Chequeos de una Opinión (v1.9: se corre una vez por Opinión; con /alt, prefijo [sobria] / [asertiva])."""
    alertas = []
    ideas = ideas_de(opin)
    if len(ideas) > 5:  # v1.9: ideas ≤ procesos; antes, tope 3–4
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
        if n > tope:
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


def verificar(salida, borrador=None):
    """Devuelve la lista de alertas (sin duplicados, en orden) del bloque 1 propuesto."""
    salida = norm(salida)
    borrador = norm(borrador) if borrador is not None else None
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
    for m in NOMINAL.finditer(salida):
        alertas.append(f"VOZ · sustantivo tras coma donde va un verbo («que comprime», «que desplaza»; nunca un verbo más fuerte que el dictado) · «{m.group(0).strip(', ')}»")
    for m in RELLENO.finditer(salida):
        alertas.append(f"VOZ · relleno («a nivel de» → «en»; los demás se eliminan), salvo texto fijo de plantilla · «{m.group(0)}»")

    # v1.6: procedimiento recomendado fuera de la forma de N9
    for frase in re.split(r"(?<=[.])\s+|\n", salida):
        if re.search(r"\bse sugiere\b", frase, re.I) and PROC.search(frase) and not re.search(r"(guiad|dirigid)[ao]s? por|centro de referencia de sarcoma", frase, re.I):
            alertas.append(f"PROCEDIMIENTO · fuera de la forma «Se sugiere [procedimiento] guiado por [modalidad] para [objetivo].»: si es dictado, conserva la intención y decláralo; si es tuyo, solo con respaldo de un archivo cargado (N9) · «{frase.strip()[:70]}»")

    for etiqueta, opin in lista_opin:  # v1.9: con /alt, cada Opinión por separado y con prefijo
        alertas += chequear_opinion(opin, hall, f"[{etiqueta}] " if etiqueta else "")

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

    vistos = []
    for a in alertas:
        if a not in vistos:
            vistos.append(a)
    return vistos


def main():
    if len(sys.argv) < 2:
        print(__doc__.split("\nHistorial")[0])
        return
    salida = open(sys.argv[1], encoding="utf-8").read()
    borrador = open(sys.argv[2], encoding="utf-8").read() if len(sys.argv) > 2 else None
    vistos = verificar(salida, borrador)
    if vistos:
        print(f"ALERTAS · {len(vistos)}")
        print("\n".join(vistos))
    else:
        print("OK · sin alertas")


if __name__ == "__main__":
    main()
#END_SCRIPT
```
