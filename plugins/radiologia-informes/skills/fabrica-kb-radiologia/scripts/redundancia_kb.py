#!/usr/bin/env python3
"""redundancia_kb.py · v1.0 (2026-10-05) · candidatos a borrar o fusionar en una carpeta de archivos KB. Solo informa.

Uso: python3 redundancia_kb.py CARPETA [--despacho instrucciones.md] > candidatos.md
Detecta:
  FICHAS_GEMELAS  fichas de archivos distintos con ≥50 % de texto compartido (shingles de 5 palabras) → un dueño, el otro apunta.
  ARCHIVO_SOLAPADO  pares de archivos con ≥25 % de su texto compartido → fusionar o repartir.
  PEQUEÑO  archivo <800 palabras (la tarjeta pesa demasiado) → fusionar con su archivo hermano.
  HUERFANO  archivo que ninguna fila del despacho ni ningún otro archivo nombra (si se da --despacho).
"""
import os, re, sys, itertools, collections

def sh(t, k=5):
    w = re.findall(r"\w+", t.lower())
    return {" ".join(w[i:i + k]) for i in range(max(0, len(w) - k + 1))}

def fichas(t):
    out = {}
    for m in re.finditer(r"(?ms)^## ([34]\.\d+) · (.+?)$(.*?)(?=^## |\Z)", t):
        out[m.group(1) + " " + re.sub(r"\s*·\s*[a-z0-9-]+$", "", m.group(2))] = m.group(3)
    return out

def main():
    d = sys.argv[1]
    desp = open(sys.argv[sys.argv.index("--despacho") + 1], encoding="utf-8").read() if "--despacho" in sys.argv else None
    docs = {}
    for n in sorted(os.listdir(d)):
        if n.endswith(".md") and not n.startswith("_"):
            docs[n[:-3]] = open(os.path.join(d, n), encoding="utf-8").read()
    S = {k: sh(v) for k, v in docs.items()}
    F = {k: {f: sh(c) for f, c in fichas(v).items() if len(c.split()) > 60} for k, v in docs.items()}
    print("# Candidatos a borrar o fusionar (solo informe; decide el radiólogo o la Fábrica)\n")
    print("## ARCHIVO_SOLAPADO (≥25 % compartido)")
    pares = []
    for a, b in itertools.combinations(docs, 2):
        i = len(S[a] & S[b])
        if i:
            r = i / min(len(S[a]), len(S[b]))
            if r >= 0.25:
                pares.append((r, a, b))
    for r, a, b in sorted(pares, reverse=True):
        print(f"- {a} ↔ {b} · {r:.0%} del más corto")
    print("\n## FICHAS_GEMELAS (≥50 % compartido)")
    ahorro = 0
    for a, b in itertools.combinations(docs, 2):
        for fa, sa in F[a].items():
            for fb, sb in F[b].items():
                i = len(sa & sb)
                if i and i / min(len(sa), len(sb)) >= 0.5:
                    print(f"- {a} §{fa} ↔ {b} §{fb} · {i / min(len(sa), len(sb)):.0%}")
                    ahorro += min(len(sa), len(sb))
    print(f"\nAhorro aproximado si cada par queda con un solo dueño: ~{ahorro} palabras")
    print("\n## PEQUEÑO (<800 palabras)")
    for k, v in docs.items():
        if len(v.split()) < 800:
            print(f"- {k} · {len(v.split())} palabras")
    if desp is not None:
        print("\n## HUERFANO (nadie lo nombra)")
        todo = desp + "\n".join(docs.values())
        for k in docs:
            otros = todo.replace(docs[k], "")
            if k not in otros:
                print(f"- {k}")

if __name__ == "__main__":
    main()
