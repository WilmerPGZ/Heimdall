#!/usr/bin/env python3
"""Pruebas de verificar_informe.py v1.9 (stdlib unittest).

Textos genéricos: sin datos de pacientes, sin nombres de personas ni de instituciones.
Las Opiniones de los ejemplos (E1–E6, integración) son las de la instrucción del copiloto v2.0.

Uso:  python3 -m unittest discover -s tests -v      (desde la carpeta de la skill)
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(AQUI)
SCRIPT = os.path.join(SKILL, "scripts", "verificar_informe.py")
sys.path.insert(0, os.path.join(SKILL, "scripts"))

import verificar_informe as vi  # noqa: E402

NUEVOS = ("OPINIÓN · la idea abre con un descriptor", "OPINIÓN · «en el contexto de»", "OPINIÓN · frase idéntica",
          "OPINIÓN · dos opciones unidas", "BLOQUE ·", "SIGLA ·", "RANGO ·", "ideas: ¿cada una", "OPINIÓN · idea de")


def alertas(salida, borrador=None):
    return vi.verificar(salida, borrador)


def con(lista, fragmento):
    return [a for a in lista if fragmento in a]


def palabras(n, semilla):
    """Frase de relleno neutra de n palabras (sin lados, cifras ni términos que disparen chequeos)."""
    base = semilla.split()
    return " ".join((base * (n // len(base) + 1))[:n])


# ---------------------------------------------------------------- ejemplos de la instrucción v2.0
EJ = {
    "E1": ("Hallazgos\nEn la región pericecal derecha hay tejido inflamatorio con una colección de pared realzante.\n\n"
           "El apéndice no es visible.\n\nEl colon no tiene engrosamiento parietal.\n",
           {"sobria": "Proceso inflamatorio pericecal con una colección, probablemente un plastrón apendicular con absceso, "
                      "que explica el dolor de la fosa ilíaca derecha; una neoplasia cecal complicada es menos probable porque "
                      "el colon no tiene engrosamiento parietal.",
            "asertiva": "Plastrón apendicular con absceso, que explica el dolor de la fosa ilíaca derecha y la fiebre. "
                        "El colon no tiene engrosamiento parietal, lo que hace menos probable una neoplasia cecal."}),
    "E2": ("Hallazgos\nLas arterias pulmonares no tienen defectos de llenado.\n\nLa relación VD/VI es normal.\n\n"
           "En el pulmón hay un nódulo sólido de 5 mm.\n",
           {"": "1. Sin signos de tromboembolismo pulmonar ni dilatación del ventrículo derecho.\n"
                "2. Nódulo pulmonar sólido incidental, sin relación con el cuadro; según Fleischner 2017, no requiere "
                "seguimiento en un paciente de bajo riesgo."}),
    "E3": ("Hallazgos\nLa amígdala derecha está aumentada de tamaño.\n\nEl ganglio del nivel IIA derecho tiene centro "
           "hipodenso y realce periférico.\n\nNo hay colección periamigdalina.\n",
           {"sobria": "Aumento de tamaño de la amígdala derecha con una adenopatía necrótica del nivel IIA derecho, "
                      "probablemente amigdalitis con adenitis supurada; un origen metastásico es menos probable por el cuadro "
                      "febril agudo. No hay absceso periamigdalino.",
            "asertiva": "Amigdalitis derecha con adenitis supurada del nivel IIA, que explica la odinofagia y la fiebre. "
                        "No hay absceso periamigdalino."}),
    "E4": ("Hallazgos\nEl vidrio esmerilado es nuevo, peribroncovascular, con gradiente ápico-basal.\n\nHay derrame pleural "
           "bilateral y líquido en las cisuras.\n\nNo hay consolidación.\n",
           {"sobria": "Opacidades pulmonares nuevas con derrame pleural bilateral, probablemente edema por sobrecarga hídrica "
                      "en un paciente en hemodiálisis; una neumonía viral o atípica es menos probable porque no hay consolidación.",
            "asertiva": "Edema pulmonar por sobrecarga hídrica, con derrame pleural bilateral y líquido en las cisuras, que "
                        "explica la disnea en un paciente en hemodiálisis. La ausencia de consolidación hace menos probable "
                        "una neumonía."}),
    "E5": ("Hallazgos\nEn la zona periférica posterolateral izquierda de la región media hay una lesión de 12 mm, "
           "hipointensa en T2, con ADC bajo y realce precoz.\n\nNo hay extensión extraprostática.\n",
           {"": "Lesión en la zona periférica posterolateral izquierda de la región media, PI-RADS 4, sin signos de extensión "
                "extraprostática. Se sugiere biopsia dirigida por fusión de RM y ecografía para confirmación histológica."}),
    "E6": ("Hallazgos\nAlrededor del páncreas hay una colección necrótica.\n\nLa vena esplénica está trombosada.\n\n"
           "El riñón tiene un quiste simple.\n\nLas bases pulmonares muestran bronquiectasias residuales.\n",
           {"": "Pancreatitis aguda necrosante con una colección necrótica aguda peripancreática y trombosis de la vena esplénica."}),
    "INT": ("Hallazgos\nEl hígado tiene una laceración grado IV de la AAST.\n\nLa vena cava inferior infrahepática muestra "
            "extravasación activa.\n\nEl riñón derecho tiene una laceración grado III.\n\nEl hemoperitoneo es moderado.\n\n"
            "El trayecto entra por el flanco derecho.\n",
            {"": "Herida por arma de fuego en el flanco derecho con sangrado activo de la vena cava inferior infrahepática, la "
                 "lesión de mayor riesgo inmediato. La herida también lacera el hígado, con grado IV de la AAST, y el riñón "
                 "derecho, con grado III, y deja un hemoperitoneo moderado."}),
}


def informe(hall, ops):
    if len(ops) == 2:
        return f"{hall}\nOpinión · sobria\n{ops['sobria']}\n\nOpinión · asertiva\n{ops['asertiva']}\n"
    return f"{hall}\nOpinión\n{list(ops.values())[0]}\n"


# ---------------------------------------------------------------- regresión v1.8 (spec §5.1)
class RegresionV18(unittest.TestCase):
    def test_informe_limpio(self):
        self.assertEqual(alertas("Hallazgos\nEl hígado es de tamaño y atenuación normales.\n\nOpinión\nSin signos de lesión hepática focal.\n"), [])

    def test_retirados(self):
        self.assertTrue(con(alertas("Opinión\nNódulo hepático compatible con hemangioma."), "TÉRMINO · certeza retirada «compatible con»"))

    def test_percepcion(self):
        self.assertTrue(con(alertas("Hallazgos\nSe observa un quiste cortical en el riñón."), "PERCEPCIÓN"))

    def test_decimal(self):
        self.assertTrue(con(alertas("Hallazgos\nEl quiste mide 1.5 cm."), "DECIMAL"))

    def test_x_minuscula(self):
        self.assertTrue(con(alertas("Hallazgos\nEl nódulo mide 12 X 10 mm."), "FORMATO"))

    def test_espacio(self):
        self.assertTrue(con(alertas("Hallazgos\nEl nódulo mide 6mm."), "ESPACIO"))

    def test_tildes(self):
        self.assertTrue(con(alertas("Hallazgos\nLa lesion es sólida."), "TILDE · «lesion» → «lesión»"))

    def test_hay_tres_veces(self):
        s = "Hallazgos\nHay un quiste.\n\nEn el bazo hay un granuloma.\n\nEn la pelvis hay líquido libre.\n"
        self.assertTrue(con(alertas(s), "REPETICIÓN · «hay» aparece 3 veces"))

    def test_nominal(self):
        self.assertTrue(con(alertas("Hallazgos\nEn el hilio hepático hay una masa, compresión de la vena porta."), "VOZ · sustantivo tras coma"))

    def test_relleno(self):
        self.assertTrue(con(alertas("Hallazgos\nHay un quiste a nivel del polo superior."), "VOZ · relleno"))

    def test_procedimiento(self):
        self.assertTrue(con(alertas("Opinión\nMasa renal sólida.\n\nSe sugiere biopsia."), "PROCEDIMIENTO"))

    def test_cifra_nueva_y_perdida(self):
        a = alertas("Hallazgos\nEl nódulo mide 7 mm.", "Hallazgos\nEl nódulo mide 6 mm.")
        self.assertTrue(con(a, "CIFRA · «7» es nueva"))
        self.assertTrue(con(a, "CIFRA · «6» está en el borrador"))

    def test_corchete(self):
        self.assertTrue(con(alertas("Hallazgos\nEl nódulo mide [COMPLETAR: medida]."), "MARCADOR"))


# ---------------------------------------------------------------- §1 · lo que se relaja
class Relajado(unittest.TestCase):
    CINCO = ["Colelitiasis sin signos de colecistitis.", "Esteatosis hepática difusa.", "Hernia hiatal por deslizamiento.",
             "Diverticulosis del colon sigmoide, sin signos de diverticulitis.", "Ateromatosis aórtica calcificada."]

    def test_1_1_ideas_por_parrafo(self):
        ideas = vi.ideas_de("1. Primera idea. Con otra frase.\n\n2. Segunda idea.\n\n[nota]\n\nTercera idea\nque sigue en otra línea.")
        self.assertEqual(len(ideas), 3)
        self.assertEqual(ideas[2], ["Tercera idea", "que sigue en otra línea."])

    def test_1_1_lineas_numeradas_seguidas_son_ideas(self):
        self.assertEqual(len(vi.ideas_de("1. Una.\n2. Dos.\n3. Tres.")), 3)

    def test_1_2_cinco_ideas_no_alerta(self):
        s = "Opinión\n" + "\n\n".join(f"{i}. {t}" for i, t in enumerate(self.CINCO, 1))
        self.assertEqual(alertas(s), [])

    def test_1_2_cinco_lineas_numeradas_sin_blanco_no_alerta(self):
        s = "Opinión\n" + "\n".join(f"{i}. {t}" for i, t in enumerate(self.CINCO, 1))
        self.assertEqual(alertas(s), [])

    def test_1_2_seis_ideas_alerta(self):
        s = "Opinión\n" + "\n\n".join(f"{i}. {t}" for i, t in enumerate(self.CINCO + ["Granuloma calcificado esplénico."], 1))
        self.assertEqual(con(alertas(s), "OPINIÓN · 6 ideas"),
                         ["OPINIÓN · 6 ideas: ¿cada una es un proceso distinto? (N7: ideas ≤ procesos)"])

    def test_1_3_idea_1_de_85_palabras_no_alerta(self):
        f1 = "Pancreatitis aguda edematosa con líquido peripancreático y sin colecciones organizadas, que explica el dolor epigástrico."
        f2 = palabras(40, "La glándula conserva su realce y no muestra necrosis del parénquima ni trombosis venosa")
        f3 = palabras(85 - len(f1.split()) - 40, "El origen biliar es probable por la colelitiasis descrita en la vesícula")
        idea = f"{f1} {f2}. {f3}."
        self.assertEqual(len(idea.split()), 85)
        self.assertEqual(con(alertas("Opinión\n" + idea), "palabras"), [])

    def test_1_3_idea_2_de_55_palabras_alerta(self):
        idea2 = palabras(55, "Esteatosis hepática difusa sin lesiones focales ni signos de hepatopatía crónica")
        s = f"Opinión\n1. Colelitiasis sin signos de colecistitis.\n\n2. {idea2}."
        a = con(alertas(s), "OPINIÓN · idea de 55 palabras")
        self.assertEqual(len(a), 1)
        self.assertIn("(guía: idea 1 ≈60, el resto cortas; es una señal, no un tope)", a[0])

    def test_1_3_idea_2_de_50_no_alerta(self):
        idea2 = palabras(50, "Esteatosis hepática difusa sin lesiones focales ni signos de hepatopatía crónica")
        self.assertEqual(con(alertas(f"Opinión\n1. Colelitiasis.\n\n2. {idea2}."), "palabras"), [])

    def test_1_4_frase_de_razonamiento(self):
        op = ("Opinión\nProceso inflamatorio pericecal con una colección, probablemente un plastrón apendicular con absceso, "
              "que explica el dolor de la fosa ilíaca derecha; una neoplasia cecal complicada es menos probable porque el colon "
              "no tiene engrosamiento parietal.")
        a = alertas(op)
        self.assertEqual([x for x in a if x.startswith(("ORDEN", "OPINIÓN"))], [])
        self.assertEqual(alertas("Hallazgos\nEn la fosa ilíaca derecha hay una colección pericecal.\n\n" + op), [])

    def test_1_4_variantes_menos_probable(self):
        for op in ["Edema pulmonar por sobrecarga hídrica. La ausencia de consolidación hace menos probable una neumonía.",
                   "Amigdalitis con adenitis supurada; un origen metastásico es menos probable por el cuadro febril agudo.",
                   "Plastrón apendicular con absceso, lo que hace menos probable una neoplasia cecal."]:
            self.assertEqual(alertas("Opinión\n" + op), [], op)

    def test_1_5_negaciones_de_la_opinion_no_cuentan(self):
        borr = "Hallazgos\nLa amígdala está aumentada de tamaño, sin colección.\n"
        sal = ("Hallazgos\nLa amígdala está aumentada de tamaño, sin colección.\n\nOpinión\nAmigdalitis aguda. "
               "No hay absceso periamigdalino.\n\nSin signos de extensión extraprostática.\n")
        self.assertEqual(con(alertas(sal, borr), "NEGACIÓN"), [])

    def test_1_6_verificar_lado_ya_no_exceptua(self):
        a = alertas("Hallazgos\nHay un quiste renal.\n\nOpinión\nQuiste renal derecho [VERIFICAR LADO].")
        self.assertTrue(con(a, "LADO · «derecho»"))
        self.assertTrue(con(a, "MARCADOR"))
        self.assertFalse(hasattr(vi, "MARCADOR_OK"))


# ---------------------------------------------------------------- §2 · lo que se añade
class Anadido(unittest.TestCase):
    def test_2_1_descriptor_alerta(self):
        a = alertas("Opinión\nPérdida de altura de los cuerpos vertebrales dorsales descritos.")
        self.assertEqual(len(con(a, "OPINIÓN · la idea abre con un descriptor y no nombra un diagnóstico")), 1)
        self.assertIn("«Pérdida de altura de los cuerpos vertebrales dorsales descri»", a[0])

    def test_2_1_descriptor_traducido_no_alerta(self):
        self.assertEqual(alertas("Opinión\nFracturas por acuñamiento de los cuerpos vertebrales dorsales descritos."), [])

    def test_2_1_descriptor_que_es_el_hallazgo_con_diagnostico(self):
        a = alertas("Opinión\nOpacidades pulmonares nuevas con derrame pleural bilateral, probablemente edema por sobrecarga hídrica.")
        self.assertEqual(con(a, "descriptor"), [])

    def test_2_1_otros_descriptores(self):
        for op in ["Acuñamiento del cuerpo vertebral.", "1. Engrosamiento parietal del colon descendente.",
                   "Hipodensidades hepáticas.", "Alteración de la señal medular.", "La imagen nodular pulmonar."]:
            self.assertTrue(con(alertas("Opinión\n" + op), "descriptor"), op)

    def test_2_1_descriptor_con_certeza_o_categoria(self):
        for op in ["Engrosamiento parietal del colon descendente, probablemente colitis.", "Realce leptomeníngeo, sospechoso de carcinomatosis.",
                   "Hipodensidad renal, Bosniak II.", "Aumento de la densidad de la grasa, sin signos de perforación."]:
            self.assertEqual(con(alertas("Opinión\n" + op), "descriptor"), [], op)

    def test_2_2_contexto_sin_respuesta_alerta(self):
        a = alertas("Opinión\nOpacidades en vidrio esmerilado bilaterales en el contexto de la sospecha de neumonía.")
        self.assertEqual(len(con(a, "OPINIÓN · «en el contexto de» no sustituye la respuesta")), 1)
        self.assertEqual(con(a, "descriptor"), [])  # una sola señal por idea

    def test_2_2_contexto_con_respuesta_no_alerta(self):
        a = alertas("Opinión\nNódulo extratiroideo posterior al lóbulo derecho, probablemente un adenoma paratiroideo en el contexto del hiperparatiroidismo.")
        self.assertEqual(con(a, "contexto"), [])

    def test_2_3_frase_copiada_alerta(self):
        f = "El bazo presenta una laceración de 2 cm de profundidad en el polo inferior."
        a = alertas(f"Hallazgos\n{f}\n\nOpinión\n{f}")
        self.assertEqual(len(con(a, "OPINIÓN · frase idéntica a una de Hallazgos")), 1)

    def test_2_3_frase_copiada_sin_tildes_ni_puntuacion(self):
        a = alertas("Hallazgos\nEl bazo presenta una laceración de 2 cm de profundidad en el polo inferior.\n\n"
                    "Opinión\nHemoperitoneo moderado; el bazo presenta una laceracion de 2 cm, de profundidad en el polo inferior.")
        self.assertTrue(con(a, "frase idéntica"))

    def test_2_3_sintesis_no_alerta(self):
        a = alertas("Hallazgos\nEl bazo presenta una laceración de 2 cm de profundidad en el polo inferior.\n\nOpinión\nLaceración esplénica con hemoperitoneo.")
        self.assertEqual(a, [])

    def test_2_3_frase_corta_igual_no_alerta(self):
        self.assertEqual(alertas("Hallazgos\nNo hay absceso periamigdalino.\n\nOpinión\nAmigdalitis aguda. No hay absceso periamigdalino."), [])

    def test_2_4_barra_alerta(self):
        a = alertas("Opinión\nPatrón bronquiolar infeccioso/inflamatorio.")
        self.assertEqual(con(a, "OPINIÓN · dos opciones unidas por «/»"),
                         ["OPINIÓN · dos opciones unidas por «/»: ordénalas con su certeza («probablemente X; Y menos probable») (N7, N9) · «infeccioso/inflamatorio»"])

    def test_2_4_barra_no_alerta(self):
        self.assertEqual(alertas("Hallazgos\nRelación VD/VI de 1,2.\n\nOpinión\nCategoría PE-RADS 2/E."), [])
        self.assertEqual(con(alertas("Hallazgos\nEl ADC medio es de 0,8 x 10-3 mm²/s.\n\nOpinión\nLesión focal, PI-RADS 4, y/o con flujo 3/4."), "«/»"), [])

    def test_2_4_barra_solo_en_opinion(self):
        self.assertEqual(con(alertas("Hallazgos\nPatrón infeccioso/inflamatorio.\n\nOpinión\nBronquiolitis."), "«/»"), [])

    def test_2_5_rotulo_de_bloque_alerta(self):
        a = alertas("Hallazgos\nEl hígado es normal.\n\nFaltó: márgenes y segundo eje.")
        self.assertEqual(con(a, "BLOQUE"), ["BLOQUE · «Faltó» pertenece a los bloques 2–3, no al informe (N3, N6)"])

    def test_2_5_otros_rotulos(self):
        for linea, rot in [("Descripción: masa en el hígado → masa en el segmento VI · faltó margen", "Descripción"),
                           ("Considerar añadir, si lo confirmas en las imágenes: ...", "Considerar añadir"),
                           ("**Antes de pegar:** lado del quiste → derecho / izquierdo.", "Antes de pegar"),
                           ("Opinión propuesta: apendicitis aguda.", "Opinión propuesta"),
                           ("Lección: el lado se verifica en el título.", "Lección"),
                           ("Firmante: ABCDE · huella cargada · vale para el chat.", "Firmante"),
                           ("→ Maestro: celda diagonal de una categoría: pregunta conceptual", "→ Maestro")]:
            self.assertTrue(con(alertas(f"Hallazgos\nEl hígado es normal.\n\n{linea}"), f"BLOQUE · «{rot}»"), linea)

    def test_2_5_palabra_dentro_de_frase_no_alerta(self):
        a = alertas("Hallazgos\nEl hígado es normal, sin cambios respecto al previo; faltó la fase portal en la adquisición.")
        self.assertEqual(con(a, "BLOQUE"), [])

    def test_2_5_rotulo_de_plantilla_descripcion_no_alerta(self):
        self.assertEqual(con(alertas("Descripción: El hígado es de tamaño normal."), "BLOQUE"), [])

    def test_2_6_sigla_aislada_alerta(self):
        a = alertas("ABCDE\n\nHallazgos\nEl hígado es normal.")
        self.assertEqual(con(a, "SIGLA"), ["SIGLA · «ABCDE» aislado al inicio del bloque 1: si es la sigla del firmante, quítala (Δ-R8); el nombre o la sigla nunca entran al informe"])

    def test_2_6_titulo_o_sigla_clinica_no_alerta(self):
        self.assertEqual(alertas("TC DE ABDOMEN Y PELVIS CON CONTRASTE\n\nHallazgos\nEl hígado es normal."), [])
        self.assertEqual(alertas("FLAIR\n\nEl cuerpo calloso es normal."), [])
        self.assertEqual(con(alertas("Hallazgos\nABCDE\nEl hígado es normal."), "SIGLA"), [])  # solo la primera línea

    def test_2_7_uh_fuera_de_rango(self):
        for s in ["La colección tiene una densidad media de 8150 UH.", "La colección tiene una densidad media de 8 150 UH.",
                  "La colección tiene una densidad media de 8 150 UH.", "El contenido mide −1200 UH."]:
            a = con(alertas("Hallazgos\n" + s), "RANGO")
            self.assertEqual(len(a), 1, s)
            self.assertIn("fuera del rango físico", a[0])

    def test_2_7_porcentaje_mayor_de_100(self):
        self.assertEqual(con(alertas("Hallazgos\nLa estenosis es del 130 %."), "RANGO"), ["RANGO · «130 %» mayor de 100"])

    def test_2_7_valores_validos_no_alerta(self):
        self.assertEqual(alertas("Hallazgos\nEl contenido tiene 170 UH.\n\nLa grasa tiene -85 UH.\n\nLa estenosis es del 98 %.\n"), [])
        self.assertEqual(con(alertas("Hallazgos\nEl cortical óseo tiene 1200 UH y el aire -1000 UH."), "RANGO"), [])
        self.assertEqual(con(alertas("Hallazgos\nEl nódulo tiene un aumento de tamaño del 150 % respecto al previo."), "RANGO"), [])


# ---------------------------------------------------------------- §3 · rótulos sobria / asertiva
class DosOpiniones(unittest.TestCase):
    def test_3_orden_solo_en_asertiva(self):
        s = ("Hallazgos\nEn el hígado hay una masa de 4 cm.\n\nOpinión · sobria\nMasa hepática, sospechosa de neoplasia.\n\n"
             "Opinión · asertiva\nProbable neoplasia hepática primaria.\n")
        a = alertas(s)
        self.assertEqual(len(a), 1)
        self.assertTrue(a[0].startswith("[asertiva] ORDEN · "))

    def test_3_cada_opinion_por_separado(self):
        s = ("Hallazgos\nEn el hígado hay una masa de 4 cm.\n\nOpinión · sobria\nMasa hepática: sospechosa de neoplasia.\n\n"
             "Opinión · asertiva\nNeoplasia hepática primaria de 4 cm.\n")
        a = alertas(s)
        self.assertTrue(con(a, "[sobria] OPINIÓN · dos puntos"))
        self.assertTrue(con(a, "[asertiva] OPINIÓN · medida en la Opinión"))
        self.assertFalse(con(a, "[asertiva] OPINIÓN · dos puntos"))

    def test_3_rotulos_reconocidos(self):
        hall, ops = vi.opiniones("Hallazgos\nX.\n\nOPINIÓN · SOBRIA\nA.\n\nopinion - asertiva:\nB.\n")
        self.assertEqual([e for e, _ in ops], ["sobria", "asertiva"])
        self.assertEqual(hall.strip(), "Hallazgos\nX.")

    def test_3_una_opinion_sin_prefijo(self):
        a = alertas("Hallazgos\nHay una masa.\n\nOpinión\nProbable neoplasia.\n")
        self.assertTrue(a[0].startswith("ORDEN · "))

    def test_3_secciones_compatible(self):
        hall, opin = vi.secciones("Hallazgos\nX.\n\nOpinión: 1. A. 2. B.\n")
        self.assertEqual(hall.strip(), "Hallazgos\nX.")
        self.assertIn("1. A. 2. B.", opin)


# ---------------------------------------------------------------- ejemplos v2.0 y ejemplo largo (spec §5.3)
class EjemplosV20(unittest.TestCase):
    def test_ejemplos_sin_alertas_nuevas(self):
        for k, (hall, ops) in EJ.items():
            a = alertas(informe(hall, ops))
            self.assertEqual([x for x in a if any(n in x for n in NUEVOS)], [], k)

    def test_ejemplos_limpios(self):
        for k in ("E1", "E2", "E3", "E4", "E6", "INT"):
            hall, ops = EJ[k]
            self.assertEqual(alertas(informe(hall, ops)), [], k)
            for op in ops.values():
                self.assertEqual(alertas(f"{hall}\nOpinión\n{op}\n"), [], (k, op[:40]))

    def test_e5_solo_procedimiento_previo(self):
        hall, ops = EJ["E5"]
        a = alertas(informe(hall, ops))
        self.assertEqual([x.split(" · ")[0] for x in a], [])  # v1.9: «dirigida por» se acepta como «guiado por»

    def test_ejemplo_largo_ok(self):
        hall = ("Hallazgos\nEl apéndice cecal mide 11 mm de diámetro, tiene la pared engrosada y realzante y contiene un apendicolito.\n\n"
                "La grasa periapendicular muestra cambios inflamatorios, sin colecciones ni gas extraluminal.\n\n"
                "El ciego conserva un grosor parietal normal.\n\n"
                "El hígado, la vesícula biliar, el páncreas y el bazo son normales.\n\n"
                "La pared abdominal tiene una hernia umbilical que contiene grasa.\n")
        idea1 = ("1. Apendicitis aguda con apendicolito y cambios inflamatorios periapendiculares, sin signos de perforación ni "
                 "colecciones, que explica el dolor abdominal y la fiebre. Una neoplasia apendicular o cecal es menos probable "
                 "porque el ciego conserva un grosor parietal normal; el apendicolito y el cuadro agudo favorecen el origen "
                 "obstructivo e inflamatorio, que es la causa más frecuente de este patrón en un paciente joven y sin antecedentes quirúrgicos abdominales previos conocidos.")
        self.assertEqual(len(idea1.split()) - 1, 70)
        s = f"{hall}\nOpinión\n{idea1}\n\n2. Hernia umbilical con contenido graso, sin signos de complicación.\n"
        self.assertEqual(alertas(s, s), [])


# ---------------------------------------------------------------- CLI y empaquetado
class Cli(unittest.TestCase):
    def correr(self, *textos):
        rutas = []
        for t in textos:
            f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
            f.write(t)
            f.close()
            rutas.append(f.name)
        try:
            return subprocess.run([sys.executable, SCRIPT, *rutas], capture_output=True, text=True, encoding="utf-8")
        finally:
            for r in rutas:
                os.unlink(r)

    def test_ok(self):
        r = self.correr("Hallazgos\nEl hígado es normal.\n", "Hallazgos\nhigado normal\n")
        self.assertEqual((r.returncode, r.stdout), (0, "OK · sin alertas\n"))

    def test_alertas_formato(self):
        r = self.correr("ABCDE\n\nHallazgos\nLa colección tiene 8 150 UH.\n")
        lineas = r.stdout.splitlines()
        self.assertEqual(r.returncode, 0)
        self.assertEqual(lineas[0], f"ALERTAS · {len(lineas) - 1}")
        self.assertTrue(lineas[1].startswith("SIGLA · "))

    def test_uso_sin_argumentos(self):
        r = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0)
        self.assertIn("v2.2 (2026-10-22)", r.stdout)
        self.assertIn("Uso:", r.stdout)
        self.assertNotIn("Historial", r.stdout)

    def test_skill_md_lleva_el_mismo_script(self):
        md = os.path.join(SKILL, "SKILL.md")
        if not os.path.exists(md):
            self.skipTest("sin SKILL.md")
        with open(md, encoding="utf-8") as f:
            texto = f.read()
        with open(SCRIPT, encoding="utf-8") as f:
            script = f.read()
        m = re.search(r"^#BEGIN_SCRIPT\n(.*?)^#END_SCRIPT$", texto, re.S | re.M)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), script)
        self.assertIn("v2.2 (2026-10-22)", texto.split("#BEGIN_SCRIPT")[0])


if __name__ == "__main__":
    unittest.main()


class TestDirigidaPor(unittest.TestCase):
    def test_biopsia_dirigida_por_fusion_no_alerta(self):
        import importlib, sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        v = importlib.import_module('verificar_informe')
        txt = "OPINIÓN:\n\n1. Lesión de la zona periférica del lóbulo derecho altamente sospechosa de cáncer clínicamente significativo, PI-RADS 5. Se sugiere biopsia dirigida por fusión para confirmación histológica.\n"
        out = v.verificar(txt) if hasattr(v, 'verificar') else ''
        self.assertNotIn('PROCEDIMIENTO', str(out))
