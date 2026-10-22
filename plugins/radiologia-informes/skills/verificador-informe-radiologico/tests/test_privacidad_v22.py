"""test_privacidad_v22.py · PRIVACIDAD del verificador v2.2 · datos 100 % sintéticos e inventados (ningún nombre, documento ni
teléfono es real). Solo biblioteca estándar: python3 -m unittest discover -s tests"""
import os, sys, unittest
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import verificar_informe as vi  # noqa: E402

H = "Hallazgos:\nHígado de tamaño normal.\n\nOpinión:\nSin alteraciones.\n"
# (nombre, salida, borrador, bloque3, tipos esperados en PRIVACIDAD (vacío = ninguna))
CASOS = [
    ("P01 rótulo Paciente con nombre", "Paciente: Ximena Quintero Lozano\n" + H, H, None, {"nombre de persona"}),
    ("P02 cédula con puntos", "CC 1.098.765.432\n" + H, H, None, {"documento de identidad"}),
    ("P03 tarjeta de identidad", "TI 1034567890\n" + H, H, None, {"documento de identidad"}),
    ("P04 pasaporte", H + "Pasaporte AB123456\n", H, None, {"documento de identidad"}),
    ("P05 historia clínica", "Historia clínica 7788123\n" + H, H, None, {"número de historia"}),
    ("P06 cama y habitación", "Cama 304B. Habitación 12.\n" + H, H, None, {"cama o habitación"}),
    ("P07 fecha de nacimiento", "Fecha de nacimiento: 03/04/1980\n" + H, H, None, {"fecha de nacimiento"}),
    ("P08 teléfono celular", H + "Contacto 310 555 0199\n", H, None, {"teléfono"}),
    ("P09 firma pegada", H + "Firmado electrónicamente por: Dr. Octavio Ríos Bermúdez\n", H, None, {"firma", "nombre de persona"}),
    ("P10 nombre antes de la edad", "Rodolfo Benítez, de 54 años, con dolor abdominal.\n" + H, H, None, {"nombre de persona"}),
    ("P11 formato AGFA APELLIDOS, NOMBRES", "QUINTERO LOZANO, XIMENA\n" + H, H, None, {"nombre de persona"}),
    ("P12 apellido de la firma del borrador", H.replace("Sin alteraciones.", "Sin alteraciones, según Arbeláez."),
     H + "\nDra. Penélope Arbeláez\n", None, {"nombre de persona"}),
    ("P13 nombre en el bloque 3", H, H, "Llamar: apendicitis aguda · avisar a la Dra. Penélope Arbeláez.", {"nombre de persona"}),
    ("P14 nombre frecuente + apellido", "Hallazgos:\nHígado normal; estudio solicitado por María Restrepo.\n\nOpinión:\nSin alteraciones.\n", H, None,
     {"nombre de persona"}),
    ("P15 comunicación no dictada", H + "Hallazgo comunicado a la Dra. Tamara Ibáñez, de cirugía, el 22/10/2026 a las 03:10, por teléfono.\n",
     H, None, {"nombre de persona"}),
    ("P16 documento sin rótulo", H + "1098765432\n", H, None, {"documento de identidad"}),
    ("N01 epónimos y escalas", "Hallazgos:\nSigno de Murphy ecográfico positivo. Quiste renal Bosniak IIF. Lesión en el segmento VII de Couinaud, "
     "adyacente a la cápsula de Glisson. Lesión de Hill-Sachs. Índice de Insall-Salvati de 1,3. Pancreatitis según Atlanta 2012; Child-Pugh B.\n\n"
     "Opinión:\nNódulo pulmonar de 5 mm; según Fleischner 2017, no requiere seguimiento.\n", None, None, set()),
    ("N02 sigla del firmante", "QXZ\n" + H, "QXZ\n" + H, None, set()),
    ("N03 comunicación dictada (N11)", H + "Hallazgo comunicado a la Dra. Tamara Ibáñez, de cirugía general, el 22/10/2026 a las 03:10, por teléfono.\n",
     H + "Hallazgo comunicado a la Dra. Tamara Ibáñez, de cirugía general, el 22/10/2026 a las 03:10, por teléfono.\n", None, set()),
    ("N04 fechas, volúmenes y densidades", "Hallazgos:\nComparación con TC del 12/09/2026. Colección de 12 x 10 x 8 mm, volumen de 1 250 mL; "
     "densidad de 8 150 UH. Disco L4-L5 y C5-C6; secuencias T1 y T2.\n\nOpinión:\nNódulo tiroideo TI-RADS 4; PI-RADS 4; ASPECTS 10/10.\n", None, None, set()),
    ("N05 demografía en el rótulo", "Paciente: Femenina de 45 años.\n" + H, None, None, set()),
    ("N06 edad sin nombre", "Mujer de 45 años con dolor. Enfermedad de Crohn de 10 años de evolución.\n" + H, None, None, set()),
    ("N07 palabras que son nombres", "Hallazgos:\nLuz intestinal conservada. Pilar posterior íntegro. Aura sin alteración.\n\nOpinión:\nSin alteraciones.\n",
     None, None, set()),
    ("N08 título en mayúsculas con coma", "TC DE ABDOMEN Y PELVIS, CON CONTRASTE\n" + H, None, None, set()),
    ("N09 nombre en el borrador que no se copia", H, "Paciente: Ximena Quintero\n" + H, None, set()),
    ("N11 línea de servicio «Firmante:» no es una firma", H + "Firmante: QXZ · huella cargada · vale para el chat.\n", H, None, set()),
    ("N10 fracturas y clasificaciones con nombre", "Hallazgos:\nFractura de Colles. Fractura de Weber B. Clasificación de Garden III y "
     "Schatzker II. Quiste de Baker. Divertículo de Meckel.\n\nOpinión:\nFractura de Colles.\n", None, None, set()),
]


class Privacidad(unittest.TestCase):
    def test_casos(self):
        for nombre, sal, bor, b3, esperado in CASOS:
            al = vi.verificar(sal, bor, None, b3)
            priv = [a for a in al if a.startswith("PRIVACIDAD")]
            with self.subTest(nombre):
                self.assertEqual({a.split(" · ", 1)[1].split(" en el ")[0] for a in priv}, esperado)
                self.assertTrue(not priv or al[0].startswith("PRIVACIDAD"))
                if esperado:
                    for dato in ("Quintero", "1.098", "Arbeláez", "Benítez", "0199", "Restrepo", "Ríos", "AB123456", "Ibáñez"):
                        self.assertNotIn(dato, " ".join(al))


if __name__ == "__main__":
    unittest.main()
