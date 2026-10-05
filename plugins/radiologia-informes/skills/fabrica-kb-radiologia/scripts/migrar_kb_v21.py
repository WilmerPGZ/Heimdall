#!/usr/bin/env python3
"""migrar_kb_v21.py · v1.2 (2026-10-05) · migración mecánica estándar KB v2.0 → v2.1 (pasos 1–4 de §7).

Uso:
  python3 migrar_kb_v21.py ENTRADA SALIDA RETIRADO --proyecto MSK      # migra una carpeta de .md
  python3 migrar_kb_v21.py ENTRADA --check                              # solo reglas v2.1 (CTX, RET-P, SIZE, IDX, TAB)
Qué hace (idempotente):
  1. «> Contexto:» de cada ficha → «<slug> · <modalidad> · <proyecto> · <descripción> · dispara: <…>»; slug en el título.
  2. Tarjeta: agrega «Índice» (3.N y 4.N con su título exacto).
  3. Changelog y «Versiones retiradas» → RETIRADO/<slug>.retirado.md; en el archivo queda una línea.
  4. Quita la línea «REVISOR: ~N tokens» de la tarjeta.
  --compacto (proyecto lleno): Contexto sin descripción (la entidad ya está en el título del mismo fragmento),
  Índice en una línea en lugar de «Posee», Fuentes sin capítulos, páginas ni fechas de consulta (las páginas siguen
  en cada ficha), changelog reducido a la línea «en disco», líneas solo-[NF] de «Vacíos» al disco ([TENSION] se queda). El total debe bajar; `_orden-subida.txt` ordena la subida del que más ahorra al que crece.
  --limpieza (recomendado tras el piloto MSK 2026-10-05): SOLO lo que no compite en la búsqueda —
  Fuentes sin capítulos ni páginas, changelog a disco, líneas solo-[NF] de «Vacíos» a disco, línea REVISOR fuera.
  No toca Contexto, títulos, «Posee» ni agrega Índice (el Índice en la tarjeta le quitó fichas a la búsqueda: 11→7/20).
  No toca contenido clínico. Lo que pide revisión (fichas >600 tokens, tablas >8 filas, sin Dictado o Keywords,
  Opinión de ejemplo que abre con certeza) va al informe JSON y a la consola.
"""
import json, os, re, sys

H_FICHA = re.compile(r"^## ([34]\.\d+) · (.+?)\s*$")
H_SEC = re.compile(r"^## ")
CERT = re.compile(r"«\s*(probables?|posibles?|sospech\w*|sugestiv\w*|hallazgos (sugestivos|sospechosos|consistentes))\b", re.I)
RET_TIT = re.compile(r"^## \d+ · (Changelog|Versiones retiradas)\b", re.I)

def tokens(txt):  # estimación conservadora para español
    return int(len(txt.split()) * 1.6)

def slug_de(lineas, nombre):
    for l in lineas[:25]:
        m = re.search(r"\*\*Slug:\*\*\s*`?([a-z0-9-]+)", l)
        if m:
            return m.group(1)
    return re.sub(r"^(kb_|claude_|claude )", "", os.path.splitext(nombre)[0])

def fichas(lineas):
    out = []
    for i, l in enumerate(lineas):
        m = H_FICHA.match(l)
        if m:
            j = i + 1
            while j < len(lineas) and not H_SEC.match(lineas[j]) and not lineas[j].startswith("<!-- REVISOR:fin"):
                j += 1
            out.append((i, j, m.group(1), m.group(2)))
    return out

def titulo_sin_slug(t, slug):
    return re.sub(r"\s*·\s*" + re.escape(slug) + r"$", "", t).strip()

def revisar(lineas, slug, nombre):
    rep = {"archivo": nombre, "slug": slug, "fichas": 0, "SIZE": [], "TAB": [], "CTX": [], "SIN_DICTADO": [], "SIN_KEYWORDS": [], "OPINION_CERTEZA_INICIAL": [], "RET-P": [], "IDX": ""}
    fs = fichas(lineas)
    rep["fichas"] = len(fs)
    for i, j, n, t in fs:
        cuerpo = "\n".join(lineas[i:j])
        if tokens(cuerpo) > 600:
            rep["SIZE"].append(f"{n} (~{tokens(cuerpo)})")
        ctx = lineas[i + 1] if i + 1 < len(lineas) else ""
        if not (t.endswith(slug) and ctx.startswith(f"> Contexto: {slug} ·") and "dispara:" in ctx):  # vale con o sin descripción
            rep["CTX"].append(n)
        if n.startswith("3.") and not re.search(r"\*\*Dictado:\*\*|^Dictado:", cuerpo, re.M):
            rep["SIN_DICTADO"].append(n)
        if n.startswith("3.") and not re.search(r"\*\*Keywords:\*\*|^Keywords:", cuerpo, re.M):
            rep["SIN_KEYWORDS"].append(n)
        for l in lineas[i:j]:
            if "Escribe · Opinión" in l and CERT.search(l):
                rep["OPINION_CERTEZA_INICIAL"].append(n)
                break
    filas, ini = 0, None
    for k, l in enumerate(lineas + [""]):
        if l.lstrip().startswith("|"):
            if filas == 0:
                ini = k
            filas += 1
        else:
            if filas - 2 > 8:
                rep["TAB"].append(f"línea {ini + 1} ({filas - 2} filas)")
            filas = 0
    for l in lineas:
        if re.match(r"^## \d+ · Versiones retiradas", l, re.I):
            rep["RET-P"].append(l.strip())
    tiene_idx = any("**Índice:**" in l for l in lineas[:80])
    rep["IDX"] = "ok" if tiene_idx else "falta"
    return rep

def migrar(texto, nombre, proyecto, compacto=False, limpieza=False):
    if limpieza:
        compacto = True
    L = texto.split("\n")
    slug = slug_de(L, nombre)
    retirado = []
    # 3 · Changelog y versiones retiradas fuera
    k = 0
    while k < len(L):
        if RET_TIT.match(L[k]):
            j = k + 1
            while j < len(L) and not H_SEC.match(L[j]):
                j += 1
            bloque = L[k:j]
            cuerpo = [l for l in bloque[1:] if l.strip()]
            ya = any("en disco" in l for l in cuerpo)
            if not ya:
                retirado += bloque + [""]
                if "changelog" in L[k].lower() and compacto:
                    L[k:j] = [L[k], "- Versiones anteriores y changelog completo: en disco.", ""]
                    k += 3
                    continue
                if "changelog" in L[k].lower():
                    ult = next((l for l in bloque[1:] if l.strip().startswith("- ")), "")
                    L[k:j] = [L[k], (ult if ult else "") , "- Versiones anteriores y changelog completo: en disco.", ""]
                    L[k + 1:k + 2] = [] if not ult else [ult]
                else:
                    L[k:j] = []
                    continue
            k = j if ya else k + 1
        else:
            k += 1
    # 1 · Contexto y slug en el título
    for i, j, n, t in ([] if limpieza else reversed(fichas(L))):
        if not t.endswith(slug):
            L[i] = f"## {n} · {t} · {slug}"
        if not (i + 1 < len(L) and L[i + 1].startswith("> Contexto:")):
            entidad = titulo_sin_slug(t, slug)
            tipo = "diferencial" if n.startswith("4.") else "[NF]"
            L.insert(i + 1, f"> Contexto: {slug} · {tipo} · {proyecto} · {entidad} · dispara: {entidad.lower()}")
            continue
        if i + 1 < len(L) and L[i + 1].startswith("> Contexto:"):
            c = L[i + 1][len("> Contexto:"):].strip()
            if c.startswith(slug + " ·") and "dispara:" in c:
                continue
            c = c.rstrip(".")
            m = re.search(r"\s*·?\s*usar cuando (?:el borrador )?(?:dicta|describe|pide|informa|menciona)?\s*(.+)$", c, re.I)
            dispara = ""
            if m:
                dispara = m.group(1).strip()
                c = c[:m.start()].strip(" ·")
            partes = [p.strip() for p in c.split(" · ") if p.strip()]
            modalidad = partes[0] if partes else "[NF]"
            resto = partes[1:]
            entidad = titulo_sin_slug(t, slug)
            desc = " · ".join(resto) if resto else entidad
            if not dispara:
                d = next((l for l in L[i:j] if "**Dictado:**" in l), "")
                dm = re.search(r"\*\*Dictado:\*\*\s*([^·]+)", d)
                dispara = dm.group(1).strip() if dm else entidad.lower()
            L[i + 1] = (f"> Contexto: {slug} · {modalidad} · {proyecto} · dispara: {dispara}" if compacto
                        else f"> Contexto: {slug} · {modalidad} · {proyecto} · {desc} · dispara: {dispara}")
    # 4 · REVISOR fuera de la tarjeta · 2 · Índice
    card = next((i for i, l in enumerate(L) if l.startswith("## 0 · Tarjeta")), None)
    if limpieza and card is not None:
        fin = next((i for i in range(card + 1, len(L)) if H_SEC.match(L[i])), len(L))
        L[card + 1:fin] = [l for l in L[card + 1:fin] if not l.startswith("- **REVISOR:**")]
        card = None
    if card is not None:
        fin = next((i for i in range(card + 1, len(L)) if H_SEC.match(L[i])), len(L))
        nueva = []
        for l in L[card + 1:fin]:
            if l.startswith("- **REVISOR:**"):
                continue
            l = re.sub(r"\s*·\s*\*\*REVISOR:\*\*[^·]*", "", l)
            nueva.append(l)
        nueva = [l for l in nueva if not l.startswith("- **Índice:**") and not l.startswith("  - 3.") and not l.startswith("  - 4.")]
        if compacto:
            nueva = [l for l in nueva if not l.startswith("- **Posee:**")]
            nueva = [re.sub(r"\s*·\s*\*\*Tamaño:\*\*[^·]*", "", l) for l in nueva]
        while nueva and not nueva[-1].strip():
            nueva.pop()
        if compacto:
            idx = ["- **Índice:** " + " · ".join(f"{n} {titulo_sin_slug(t, slug)}" for _, _, n, t in fichas(L))]
        else:
            idx = ["- **Índice:**"] + [f"  - {n} · {titulo_sin_slug(t, slug)}" for _, _, n, t in fichas(L)]
        L[card + 1:fin] = nueva + idx + [""]
    if compacto:  # [NF] (nota de mantenimiento) al disco; [TENSION] se queda
        en_vac, nf = False, []
        for i, l in enumerate(L):
            if H_SEC.match(l):
                en_vac = bool(re.match(r"^## \d+ · Vacíos", l))
                continue
            if en_vac and "[NF]" in l and "[TENSION]" not in l and l.startswith("- "):
                nf.append(i)
        if nf:
            retirado += ["## Vacíos [NF] retirados del proyecto"] + [L[i] for i in nf] + [""]
            for i in reversed(nf):
                del L[i]
    if compacto:  # Fuentes sin capítulos, páginas ni fechas
        en_fuentes = False
        for i, l in enumerate(L):
            if H_SEC.match(l):
                en_fuentes = bool(re.match(r"^## \d+ · Fuentes", l))
                continue
            m0 = re.match(r"^(- \*\*S\d+:\*\*\s*)(.*)$", l) if en_fuentes else None
            if m0:
                cuerpo = m0.group(2)
                stop = re.search(r"\s*[,·;]\s*(caps?\.|pp?\.\s|PDF|folios?\b|consultad|libro\b|verificad|sin DOI)", cuerpo)
                corto = cuerpo[:stop.start()] if stop else cuerpo
                doi = re.search(r"DOI\s+(10\.\S+?)(?=[\s·;,)]|$)", cuerpo)
                if doi and doi.group(1) not in corto:
                    corto += f" · DOI {doi.group(1)}"
                if re.search(r"solo resumen", cuerpo) and "solo resumen" not in corto:
                    corto += " · solo resumen"
                L[i] = m0.group(1) + corto.rstrip(" ,;·")
    return "\n".join(L), slug, retirado

def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    proyecto = a[a.index("--proyecto") + 1] if "--proyecto" in a else "[NF]"
    if "--check" in a:
        ent = a[0]; reps = []
        for n in sorted(os.listdir(ent)):
            if n.endswith(".md"):
                L = open(os.path.join(ent, n), encoding="utf-8").read().split("\n")
                if any(l.startswith("## 0 · Tarjeta") for l in L):
                    reps.append(revisar(L, slug_de(L, n), n))
        tot = {k: sum(1 for r in reps if r[k] and r[k] != "ok") for k in ["CTX", "SIZE", "TAB", "RET-P", "SIN_DICTADO", "SIN_KEYWORDS", "OPINION_CERTEZA_INICIAL"]}
        tot["IDX"] = sum(1 for r in reps if r["IDX"] != "ok")
        print(json.dumps({"archivos": len(reps), "archivos_con_problema": tot}, ensure_ascii=False))
        json.dump(reps, open(os.path.join(ent, "_check-v21.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return
    ent, sal, ret = a[0], a[1], a[2]
    os.makedirs(sal, exist_ok=True); os.makedirs(ret, exist_ok=True)
    reps = []
    for n in sorted(os.listdir(ent)):
        if not n.endswith(".md"):
            continue
        t = open(os.path.join(ent, n), encoding="utf-8").read()
        if "## 0 · Tarjeta" not in t:
            print(f"SALTO (sin tarjeta, migración completa en Fábrica) · {n}")
            continue
        nuevo, slug, retirado = migrar(t, n, proyecto, "--compacto" in a, "--limpieza" in a)
        if ("--compacto" in a or "--limpieza" in a) and len(nuevo.split()) > len(t.split()):
            print(f"CRECE · {n} · {len(t.split())} → {len(nuevo.split())} palabras (súbelo al final)")
        open(os.path.join(sal, n), "w", encoding="utf-8").write(nuevo)
        if retirado:
            open(os.path.join(ret, f"{slug}.retirado.md"), "w", encoding="utf-8").write("\n".join(retirado))
        r = revisar(nuevo.split("\n"), slug, n)
        r["palabras_antes"], r["palabras_despues"] = len(t.split()), len(nuevo.split())
        reps.append(r)
    json.dump(reps, open(os.path.join(sal, "_informe-migracion-v21.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    orden = sorted(reps, key=lambda r: r["palabras_despues"] - r["palabras_antes"])
    open(os.path.join(sal, "_orden-subida.txt"), "w", encoding="utf-8").write(
        "\n".join(f'{r["archivo"]}\t{r["palabras_despues"] - r["palabras_antes"]:+d}' for r in orden) + "\n")
    revisar_k = ["CTX", "SIZE", "TAB", "RET-P", "SIN_DICTADO", "SIN_KEYWORDS", "OPINION_CERTEZA_INICIAL"]
    print(json.dumps({"migrados": len(reps), "palabras": [sum(r["palabras_antes"] for r in reps), sum(r["palabras_despues"] for r in reps)],
                      "pendiente_revision": {k: sum(1 for r in reps if r[k]) for k in revisar_k}}, ensure_ascii=False))

if __name__ == "__main__":
    main()
