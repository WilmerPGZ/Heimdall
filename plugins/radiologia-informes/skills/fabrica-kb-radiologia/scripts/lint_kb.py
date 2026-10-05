#!/usr/bin/env python3
"""lint_kb.py · linter de la KB de RM de cuerpo (parches 2026-10).

Uso:
  python3 lint_kb.py ARCHIVO_O_CARPETA [...] [--known lista.txt] [--out carpeta] [--quiet]

Reglas (FAIL bloquea la entrega; WARN se informa):
  RET   términos LELEX retirados fuera de [RETIRADO], changelog, líneas [W …] o notas de prohibición
  HEDGE hedges fuera de la escala LELEX en §12–§14
  D2    fórmulas de recomendación prohibidas en §12–§14
  CODE  residuos de código (\"+X.format(…)+\") en cualquier sección
  D1    interpretación («corresponde a», «atribuible a», «en relación con [proceso]») en Hallazgos de §13
  OP    dos puntos o medidas en frases de Opinión de §13
  TW    [TENSION] usado para registrar una sustitución LELEX
  MK    marcadores fuera del vocabulario cerrado
  CV    volumen fuera del CANON (4/3π, coeficiente 0,52 fuera de próstata, «candidato a CANON»)
  PTR   punteros a archivos inexistentes, a temario/brecha, «no emitido», CHANGELOG citado sin sección
  ER    decimal con punto en §12–§14, letras deletreadas («te dos»)
Zonas: §12–§14 = capa de informe (R). Dentro de §13, los bloques cuyo rótulo contiene «Opinión» o
«Cierres» son Opinión; el resto de §13 es Hallazgos.
"""
import os, re, sys, collections

KNOWN_DEFAULT = """""".split()  # lista de archivos del proyecto: pásala con --known <lista> (se guarda fuera del repositorio)

I = re.IGNORECASE
# ---------- patrones ----------
RET = [("compatible con", r"\bcompatibles? con\b"), ("definitivamente", r"\bdefinitivamente\b"),
       ("casi con certeza", r"\bcasi con certeza\b"), ("muy probablemente", r"\bmuy probablemente\b"),
       ("orienta(n) a", r"\borientan? a\b"), ("diagnóstico de", r"\bdiagn[oó]sticos? de\b")]
PROHIB_CTX = r"\b(no|nunca|sin|never|not|retirad\w*|prohib\w*|sustitu\w*|evitar|replace\w*)\b|→"
LINE_EXEMPT_RET = r"palabras a evitar|t[eé]rminos? (retirad|prohibid)|compatibles? con (la )?(resonancia|RM\b|MR)|MR[- ]conditional|condicional"
HEDGE = [("hallazgos que sugieren", r"\b(hallazgos?|características|rasgos|patrón|signos) que sugier\w*"),
         ("que sugiera(n)", r"\bque sugieran?\b"), ("cuyas características sugieren", r"\bcuyas características sugieren\b"),
         ("obliga a descartar", r"\bobliga\w* a (descartar|considerar)"), ("no se descarta", r"\bno se descarta\b"),
         ("sin poder descartar/excluir", r"\bsin poder (descartar|excluir)\b"),
         ("no permite(n) excluir/descartar", r"\bno permiten? (excluir|descartar)\b"),
         ("no es posible descartar", r"\bno es posible (descartar|diferenciar con seguridad)\b"),
         ("característico(s) de", r"\bcaracter[ií]stic[oa]s? de\b"),
         ("altamente ...", r"\baltamente (sugestiv|sospech|probable|improbable)\w*"),
         ("puede/podría corresponder a", r"\b(pueden?|podr[ií]an?) corresponder\b"),
         ("favorece", r"\bque favorecen?\b|\bhallazgo que favorece\b"),
         ("de aspecto ...", r"\bde aspecto (neopl[aá]sico|benigno|maligno|osteopor[oó]tico|flemonoso|reactivo|cr[oó]nico|posquir[uú]rgico|actínico|normal|habitual)\b"),
         ("hallazgos equívocos", r"\bequ[ií]vocos?\b"),
         ("como segunda posibilidad", r"\bsegunda posibilidad\b")]
D2 = [("valoración por especialidad", r"\bvaloraci[oó]n (por|urol[oó]gica|quir[uú]rgica|neuroquir[uú]rgica|ecogr[aá]fica testicular)\b|\binterconsulta\b"),
      ("amerita", r"\bameritan?\b"), ("manejo", r"\bmanejo (urgente|quir[uú]rgico)\b|\bde manejo\b"),
      ("operabilidad/resecabilidad", r"\b(operabilidad|resecabilidad)\b"), ("resección", r"\bresecci[oó]n\b"),
      ("drenaje", r"\b(susceptible de|requerir|requiere|puede requerir) drenaje\b|\bdrenaje percut[aá]neo\b"),
      ("biopsia", r"\bse sugiere biopsia\b|\bbiopsia o vigilancia\b|\b(correlaci[oó]n|confirmaci[oó]n) histol[oó]gica\b|\bhistolog[ií]a resulta necesaria\b"),
      ("sin necesidad/criterios de seguimiento", r"\bsin (necesidad|criterios) de seguimiento\b|\bno requiere seguimiento\b"),
      ("correlación", r"\bcorrelaci[oó]n\b|\bcorrelacionar\w*\b|\ba correlacionar\b"),
      ("se recomienda", r"\bse recomienda\b|\brecomendaci[oó]n de correlaci"),
      ("comunicado al tratante", r"\bcomunicad[oa] (al|de forma)|\b(m[eé]dico|equipo|grupo) tratante\b"),
      ("requiere caracterización", r"\brequieren? (caracterizaci[oó]n|estudio|confirmaci[oó]n)\b"),
      ("conducta", r"\bconducta (sugerida|quir[uú]rgica)\b|\bdefinir conducta\b|\bdecidir (conducta|tratamiento)\b"),
      ("planeación quirúrgica", r"\bplaneaci[oó]n quir[uú]rgica\b|\bplanificaci[oó]n quir[uú]rgica\b"),
      ("control sin guía", r"\bse sugiere control\b(?!.*\bSeg[uú]n\b)|\bcontrol dirigido\b|\bque se sugiere (controlar|repetir)\b")]
D1 = [("corresponde a", r"\bcorresponden? a\b|\bcorresponden? con\b"), ("atribuible", r"\batribuibles? a\b"),
      ("en relación con [proceso]", r"\ben relaci[oó]n con (el |la |los |las |un |una )?(contenido|necrosis|edema|hemorragia|hemorr[aá]gic|inflamaci|infecci|fibrosis|contracci|neumobilia|moldes?|colaterales|muñ[oó]n del conducto|proceso|hepatopat|compresi|infiltraci|cambios|plicatura|met[aá]st|neopl|tumor|trombo|isquemia|congesti|estructura vascular|restricci|grasa intrav|hiperplasia|cicatriz|enfermedad|lesi[oó]n|absceso|quiste)"),
      ("sugiere origen", r"\bsugiere origen\b"), ("de aspecto", r"\bde aspecto (neopl[aá]sico|benigno|maligno|posquir[uú]rgico)\b")]
MEAS = r"\b\d+([.,]\d+)?\s?(mm|cm|ml|mL|cc|cm³)\b"
OP_EXC = r"prolapso|litiasis|c[aá]lculo|volumen prost[aá]tico"
MK_OK = re.compile(r"^\[(dato no en fuente|NF|TENSION|RETIRADO|INST|verificar|PEND:[^\]]+|KB\?:[^\]]+|W \d{4}-\d{2}-\d{2}[^\]]*|W \d{4}-\d{2}-XX)\]$")
MK_SUSPECT = re.compile(r"\[(dnf|TBD|\?|[^\]]*no legible[^\]]*|[^\]]*legibles?[^\]]*|[^\]]+ dato no en fuente[^\]]*|dato no en fuente [^\]]+|[^\]]*CANON candidate[^\]]*)\]", I)
CV = [("4/3π", r"4\s*/\s*3\s*[×x*]?\s*π|4/3\s*×\s*π"), ("candidato a CANON", r"candidat[oa]s? (a|de)l? CANON|CANON candidate|candidate for (destination )?CANON|formula CANON"),
      ("0,52 fuera de próstata", r"\b0[.,]52(?!36)\b")]
PTR_TXT = [("temario", r"\b(del|el|en el) temario\b|\btemario §"), ("brecha", r"\bbrecha v\d|\bbrecha-kb"),
           ("no emitido", r"\bno emitid[oa]\b|patch propuesto|patch proposed|proposed in (the )?handoff|nota de traspaso"),
           ("regla §N del proyecto", r"regla (de precedencia )?§\d+ del proyecto")]
ER = [("letra deletreada", r"\bte dos\b|\bte i uve\b|\bfactor (uve|pe|efe)\b|\bfactores pe\b|\bele (uno|dos)\b|\beme ese\b|\bcategor[ií]a eme\b"),
      ("decimal con punto", r"(?<![§v\w.])(?<!versi[oó]n )(?<!Tabla )(?<!Fig )\b\d+\.\d+\b(?!\.\d)")]
fn_re = re.compile(r"`([A-Za-z0-9][A-Za-z0-9._\-]*[A-Za-z0-9])(?:\.md)?(?:\s*§[^`]*)?`")

def scan(path, known):
    txt = open(path, encoding="utf-8").read()
    lines = txt.splitlines()
    out = []  # (nivel, regla, línea, sec, detalle, texto)
    sec = "H"; in_ret = in_cl = False; sub = ""; in_code = False
    has_changelog = bool(re.search(r"^##+\s*(Changelog|CHANGELOG|Registro de cambios)", txt, re.M))
    for i, l in enumerate(lines, 1):
        if l.strip().startswith("```"):
            in_code = not in_code
        m = re.match(r"^(#{2,3})\s+(.*)", l)
        if m:
            h = m.group(2)
            if m.group(1) == "##":
                mm = re.match(r"(\d+)[.\s]", h); sec = mm.group(1) if mm else "x"; sub = ""
            in_ret = "RETIRADO" in h.upper()
            in_cl = bool(re.search(r"changelog|registro de cambios", h, I))
            if m.group(1) == "###": sub = h
            if not in_ret and not in_cl and m.group(1) == "##": in_ret = False
            continue
        if in_ret or in_cl:
            continue
        # sub-bloques de §13 marcados en negrita
        bm = re.match(r"^\s*\*\*([^*]+)\*\*\s*$", l) or re.match(r"^\s*\*\*([^*]+)\*\*", l) if sec == "13" else None
        if bm and (l.strip().startswith("**")):
            sub = bm.group(1)
        low = l.lower()
        exempt_line = ("[W 20" in l) or ("[RETIRADO]" in l) or ("[INST]" in l)
        R = sec in ("12", "13", "14")
        is_op = R and sec == "13" and re.search(r"opini[oó]n|cierres?", sub, I) is not None
        is_hall = R and sec == "13" and not is_op and not re.search(r"t[eé]cnica|limitaci", sub, I)
        bullet = l.lstrip().startswith(("-", "*", "|")) or (R and l.strip() and not l.startswith(">"))
        # RET
        if not exempt_line:
            for k, rx in RET:
                for mt in re.finditer(rx, l, I):
                    pre = l[max(0, mt.start() - 22):mt.start()]
                    if re.search(LINE_EXEMPT_RET, l, I):
                        continue
                    if re.search(PROHIB_CTX, pre.strip(), I):
                        continue
                    if k == "diagnóstico de" and not R:
                        out.append(("WARN", "RET", i, sec, k, l)); continue
                    if k == "compatible con" and re.search(r"\bnot?\b|\bnunca\b|\bno\b", pre, I):
                        continue
                    out.append(("FAIL", "RET", i, sec, k, l))
        # TW
        if "[TENSION]" in l and re.search(r"LELEX|compatible|sustituci", l, I):
            out.append(("FAIL", "TW", i, sec, "[TENSION] usado para LELEX", l))
        # MK
        for mt in MK_SUSPECT.finditer(l):
            out.append(("FAIL", "MK", i, sec, mt.group(0), l))
        if re.search(r"no legibles? en (la )?extracci", l, I) and not MK_SUSPECT.search(l):
            out.append(("FAIL", "MK", i, sec, "«no legible»", l))
        # CODE: residuos de código en el texto
        if re.search(r'"\+[A-Za-z_]+\.format\(|\)\+"|\\n(?=[A-Z*-])', l):
            out.append(("FAIL", "CODE", i, sec, "residuo de código", l))
        # CV
        if not exempt_line:
            for k, rx in CV:
                if re.search(rx, l, I):
                    if k.startswith("0,52") and (re.search(r"prost|PI-RADS|D3|κ|kappa|AUC|\bp ?=", l, I) or (re.search(r"CANON", l) and not re.search(CV[1][1], l, I))):
                        continue
                    out.append(("FAIL", "CV", i, sec, k, l))
        # PTR
        if not exempt_line:
            for k, rx in PTR_TXT:
                if re.search(rx, l, I):
                    out.append(("FAIL", "PTR", i, sec, k, l))
        if re.search(r"original (conservado )?en el CHANGELOG", l, I) and not has_changelog:
            out.append(("FAIL", "PTR", i, sec, "CHANGELOG citado sin sección", l))
        for mt in fn_re.finditer(l):
            name = mt.group(1)
            if "-" not in name or not re.search(r"[a-z]", name): continue
            if not re.match(r"^(clasificacion|rm-|estilo-|[a-z]+-[a-z])", name): continue
            if name in known: continue
            ctx = l[max(0, mt.start() - 8):mt.start()]
            if "PEND:" in ctx or "KB?:" in ctx: continue
            if name in ("terminologia-radiologica-espanol", "descripcion-lesiones", "reporting-principles-condensed-EN") or name.startswith(("brecha-", "temario-")):
                out.append(("FAIL", "PTR", i, sec, name, l)); continue
            if re.search(r"^(v\d|e\d|[a-z]{1,3}-\d)", name):  # tokens tipo `e-dixon`, `fl3d` no son archivos
                continue
            out.append(("WARN", "PTR?", i, sec, name, l))
        if not R or in_code and sec != "14":
            continue
        # ---- capa de informe ----
        if not exempt_line:
            for k, rx in HEDGE:
                if re.search(rx, l, I):
                    pre_ok = re.search(r"(nunca|no usar|evitar|never|not|prohib|retir)\w*[^.]{0,30}" + rx, l, I)
                    if not pre_ok:
                        out.append(("FAIL", "HEDGE", i, sec, k, l))
            for k, rx in D2:
                if re.search(rx, l, I):
                    pre_ok = re.search(r"(nunca|no usar|evitar|never|prohib|forbidden|D2)\w*[^.]{0,40}" + rx, l, I)
                    if k == "control sin guía" and re.search(r"Seg[uú]n\b[^.]{0,160}se sugiere control", l, I):
                        pre_ok = True
                    if not pre_ok:
                        out.append(("FAIL", "D2", i, sec, k, l))
            for k, rx in ER:
                for mt in re.finditer(rx, l, I):
                    if k.startswith("decimal"):
                        s = l[max(0, mt.start() - 3):mt.end() + 2]
                        if re.search(r"§|`|\(\s*§|v\d|\d\.\d\.\d", s) or re.search(r"https?://|doi|10\.\d{4}", l, I):
                            continue
                    out.append(("FAIL", "ER", i, sec, k + ": " + mt.group(0), l))
        if is_hall and not exempt_line and not l.startswith(">"):
            for k, rx in D1:
                if re.search(rx, l, I):
                    out.append(("FAIL", "D1", i, sec, k, l))
        if is_op and l.lstrip().startswith("-") and not exempt_line:
            body = re.sub(r"^\s*-\s*", "", l)
            body_nc = re.sub(r"\([^)]*\)|`[^`]*`|\[[^\]]*\]", "", body)
            if ":" in body_nc:
                out.append(("FAIL", "OP", i, sec, "dos puntos en Opinión", l))
            if re.search(MEAS, body_nc) and not re.search(OP_EXC, body, I):
                out.append(("FAIL", "OP", i, sec, "medida en Opinión", l))
    return out

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    known = set(KNOWN_DEFAULT)
    outdir = None
    if "--known" in sys.argv:
        known |= set(open(sys.argv[sys.argv.index("--known") + 1]).read().split())
    if "--out" in sys.argv:
        outdir = sys.argv[sys.argv.index("--out") + 1]
        args = [a for a in args if a != outdir]
    files = []
    for a in args:
        if os.path.isdir(a):
            for root, _, fs in os.walk(a):
                files += [os.path.join(root, f) for f in fs if f.endswith(".md") and not f.startswith("00-") and "_diff" not in root and "_lint" not in root]
        else:
            files.append(a)
    total_fail = 0
    summary = []
    for f in sorted(files):
        res = scan(f, known)
        fails = [r for r in res if r[0] == "FAIL"]; warns = [r for r in res if r[0] == "WARN"]
        total_fail += len(fails)
        cnt = collections.Counter(r[1] for r in fails)
        summary.append((os.path.basename(f), "PASS" if not fails else "FAIL", dict(cnt), len(warns)))
        rep = [f"# lint_kb · {os.path.basename(f)} · {'PASS' if not fails else 'FAIL'} · FAIL={len(fails)} WARN={len(warns)}"]
        for lv, rule, ln, sec, k, t in res:
            rep.append(f"{lv} {rule} L{ln} §{sec} [{k}] {t.strip()[:160]}")
        if outdir:
            os.makedirs(outdir, exist_ok=True)
            open(os.path.join(outdir, os.path.basename(f).replace(".md", ".lint.txt")), "w", encoding="utf-8").write("\n".join(rep) + "\n")
        if "--quiet" not in sys.argv:
            print("\n".join(rep))
    print("\n## RESUMEN")
    for name, st, cnt, nw in summary:
        print(f"{st}\t{name}\t{cnt if cnt else ''}\tWARN={nw}")
    print(f"TOTAL FAIL={total_fail} · archivos={len(summary)} · PASS={sum(1 for s in summary if s[1]=='PASS')}")
    sys.exit(1 if total_fail else 0)

if __name__ == "__main__":
    main()
