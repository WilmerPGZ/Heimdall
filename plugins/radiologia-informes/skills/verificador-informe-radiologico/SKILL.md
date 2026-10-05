---
name: "verificador-informe-radiologico"
description: "Holds the deterministic report checker used by four radiology report copilots (Claude RADS, NeuroRadio, RM de cuerpo, MSK). Their instructions extract and run it with one bash command before emitting block 1."
---

# Verificador del informe radiológico · v1.6 (2026-10-05)

The copilots' project files are no longer mounted as a folder in chat (checked 2026-10-04: no `/mnt/project`), but account and plugin skills are (under `/mnt/skills`; this one ships in the plugin `radiologia-informes`, with the same script also in `scripts/verificar_informe.py`). This skill only stores the checker; nothing here needs to be read into context.

## Run it (one bash call)
Save the proposed block 1 to `/tmp/salida.txt` and the pasted draft to `/tmp/borrador.txt`, then:

```
V=/tmp/verificar_informe.py; [ -s "$V" ] || sed -n '/^#BEGIN_SCRIPT$/,/^#END_SCRIPT$/p' "$(find /mnt/skills -path '*verificador-informe-radiologico*' -name SKILL.md 2>/dev/null | head -1)" > "$V"; python3 "$V" /tmp/salida.txt /tmp/borrador.txt
```

The first call of a conversation extracts the script to `/tmp`; later calls reuse it. Output: «OK · sin alertas» or one alert per line. Resolve every alert: fix it, or keep it and declare why. If the command finds no script, say so in block 3 and check by hand.

## Source of truth
`RADS/04 KB Markdown/_homogeneizacion/compartidos/verificar_informe.py`. When it changes, this skill is updated with the identical text. v1.2: markers like `[COMPLETAR: lado]` no longer trigger the colon or measurement alerts in the Opinión. v1.3: a decimal point at the end of a sentence («1.2.») is caught; body words added to the accent list (relación, ventrículo, hepático, esplénico, sistólico, diastólico…). v1.4: «RM … simple» and «RM de cráneo» are flagged; equivalent negations («no hay», «no se identifica», «sin evidencia de», «sin») count once and «sin contraste» is technique, not a negation; RADS category numbers («PE-RADS 3/RV+») no longer count as new figures. v1.5: ID and phone numbers («1.234.567», six or more digits) are never compared or printed, so a removed identifier never reappears in an alert. v1.6: PROCEDIMIENTO alert when a «Se sugiere» sentence names a procedure outside the N9 form (dictated → keep the intent and declare it), and UNIDAD alert when a unit of the draft disappears from the output (declare it; never convert).

```python
#BEGIN_SCRIPT
#!/usr/bin/env python3
"""verificar_informe.py · v1.6 (2026-10-05) · archivo compartido idéntico en los 4 copilotos.

Chequeo determinista del bloque 1 antes de emitirlo. No corrige: lista ALERTAS para que el modelo
las resuelva (corregir o declarar). Se ejecuta, no se lee: su texto no entra al contexto.

Uso:  python3 verificar_informe.py salida.txt [borrador.txt]
      (salida = bloque 1 propuesto; borrador = lo que el radiólogo pegó, opcional pero recomendado)
Sale con código 0 siempre; imprime «OK · sin alertas» o una alerta por línea.
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

# Marcadores válidos en el bloque 1 (núcleo N2).
MARCADOR_OK = re.compile(
    r"^\[(VERIFICAR( (LADO|MEDIDA|CATEGORÍA|CERTEZA))?|VERIFICAR TÉRMINO: .+|COMPLETAR: .+|ILEGIBLE: .+)\]$")

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


def norm(s):
    return unicodedata.normalize("NFC", s)


def secciones(texto):
    """Separa Hallazgos y Opinión por su rótulo; si no hay rótulos, todo es Hallazgos."""
    m = re.search(r"^\s*(opini[oó]n|conclusi[oó]n|impresi[oó]n)\s*:?\s*$", texto, re.I | re.M)
    if not m:
        m = re.search(r"^\s*(opini[oó]n|conclusi[oó]n|impresi[oó]n)\s*:", texto, re.I | re.M)
    if not m:
        return texto, ""
    return texto[:m.start()], texto[m.end():]


def numeros(texto):
    sin_marcadores = re.sub(r"\[[^\]]*\]", " ", texto)
    sin_marcadores = re.sub(r"\b\d{1,3}(?:\.\d{3}){2,}\b|\b\d{6,}\b", " ", sin_marcadores)  # v1.5: documentos y teléfonos nunca se comparan ni se imprimen
    sin_marcadores = re.sub(r"(?m)^\s*\d+[.)]\s", " ", sin_marcadores)  # numeración de la Opinión
    sin_marcadores = re.sub(r"\b[\w-]*RADS\s+\d+\w*(?:/[\w+]+)*", " ", sin_marcadores)  # v1.4: categoría derivada
    return {n.replace(",", ".") for n in NUM.findall(sin_marcadores)}


def negaciones(texto):
    """v1.4: «no hay X», «no se identifica X», «sin evidencia de X», «sin signos de X» y «sin X» cuentan como UNA negación."""
    t = re.sub(r"\bno\s+(hay|se\s+(identifica|identifican|observa|observan|evidencia|evidencian|visualiza|visualizan|aprecia|aprecian)|presenta|presentan|muestra|muestran)\b", " NEG ", texto, flags=re.I)
    t = re.sub(r"\bsin\s+(medio\s+de\s+)?contraste\b", " ", t, flags=re.I)  # técnica, no hallazgo
    t = re.sub(r"\bsin\s+(evidencia|signos|imagen|im[aá]genes)\s+de\b", " NEG ", t, flags=re.I)
    t = re.sub(r"\b(sin|no)\b", " NEG ", t, flags=re.I)
    return len(re.findall(r"\bNEG\b", t))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    salida = norm(open(sys.argv[1], encoding="utf-8").read())
    borrador = norm(open(sys.argv[2], encoding="utf-8").read()) if len(sys.argv) > 2 else None
    alertas = []
    hall, opin = secciones(salida)

    for patron, msg in RETIRADOS.items():
        for m in re.finditer(patron, salida, re.I):
            alertas.append(f"TÉRMINO · {msg} · «{m.group(0)}»")
    for m in re.finditer(PERCEPCION, hall, re.I):
        alertas.append(f"PERCEPCIÓN · verbo de percepción en Hallazgos (salvo texto fijo de plantilla, declarado) · «{m.group(0)}»")

    for m in re.finditer(r"\[[^\]]*\]", salida):
        if not MARCADOR_OK.match(m.group(0)):
            alertas.append(f"MARCADOR · fuera del vocabulario del bloque 1 (N2) · «{m.group(0)}»")

    for m in re.finditer(r"(?<![\w.])\d+\.\d+(?!\w|\.\d)", salida):  # v1.3: también al final de frase
        alertas.append(f"DECIMAL · usar coma decimal (salvo texto fijo de plantilla) · «{m.group(0)}»")
    for m in re.finditer(r"\d\s*[×X*]\s*\d", salida):
        alertas.append(f"FORMATO · usar «x» minúscula entre medidas · «{m.group(0)}»")
    for m in re.finditer(r"\d(mm|cm|cc|mL|ml)\b", salida):
        alertas.append(f"ESPACIO · número y unidad separados («6 mm») · «{m.group(0)}»")

    for palabra in re.findall(r"\b[a-záéíóúñü]+\b", salida, re.I):
        correcta = TILDES.get(palabra.lower())
        if correcta:
            alertas.append(f"TILDE · «{palabra}» → «{correcta}»")

    # v1.6: procedimiento recomendado fuera de la forma de N9
    for frase in re.split(r"(?<=[.])\s+|\n", salida):
        if re.search(r"\bse sugiere\b", frase, re.I) and PROC.search(frase) and not re.search(r"guiad[ao]s? por|centro de referencia de sarcoma", frase, re.I):
            alertas.append(f"PROCEDIMIENTO · fuera de la forma «Se sugiere [procedimiento] guiado por [modalidad] para [objetivo].»: si es dictado, conserva la intención y decláralo; si es tuyo, solo con respaldo de un archivo cargado (N9) · «{frase.strip()[:70]}»")

    if opin.strip():
        ideas = [l.strip() for l in opin.splitlines() if l.strip() and not l.strip().startswith("[")]
        if len(ideas) > 4:
            alertas.append(f"OPINIÓN · {len(ideas)} ideas (tope 3, o 4 en politrauma u oncología multiorgánica)")
        for idea in ideas:
            cuerpo = re.sub(r"^\d+[.)]\s*", "", idea)
            texto = re.sub(r"\[[^\]]*\]", "", cuerpo)  # v1.2: los marcadores no cuentan
            if ":" in texto:
                alertas.append(f"OPINIÓN · dos puntos en una idea · «{cuerpo[:60]}»")
            for m in MEDIDA.finditer(texto):
                alertas.append(f"OPINIÓN · medida en la Opinión (solo si el tamaño ES el criterio o es excepción del delta) · «{m.group(0)}»")
            n = len(cuerpo.split())
            if n > 40:
                alertas.append(f"OPINIÓN · idea de {n} palabras (tope 25; compleja 40) · «{cuerpo[:50]}…»")
        lados_h = {s.lower()[:5] for s in SIDE.findall(hall) for s in [s[0] if isinstance(s, tuple) else s]}
        opin_lado = re.sub(r"\b(ventr[ií]culo|aur[ií]cula|coraz[oó]n|cavidades)\s+(derech|izquierd)\w*", " ", opin, flags=re.I)
        for m in SIDE.finditer(opin_lado):
            if "[VERIFICAR LADO]" in opin_lado[m.end():m.end() + 25]:
                continue
            if m.group(1).lower()[:5] not in lados_h:
                alertas.append(f"LADO · «{m.group(1)}» en la Opinión no aparece en Hallazgos → [VERIFICAR LADO]")

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
        neg_b = negaciones(borrador)
        neg_s = negaciones(salida)
        if neg_s > neg_b:
            alertas.append(f"NEGACIÓN · la salida tiene {neg_s - neg_b} negación(es) más que el borrador: confirma que ninguna es un negativo no dictado")

    if alertas:
        vistos = []
        for a in alertas:
            if a not in vistos:
                vistos.append(a)
        print(f"ALERTAS · {len(vistos)}")
        print("\n".join(vistos))
    else:
        print("OK · sin alertas")


if __name__ == "__main__":
    main()
#END_SCRIPT
```