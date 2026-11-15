"""Tests du robot : python -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "collector"))
import programme as P  # noqa: E402

EXEMPLE = Path(__file__).with_name("exemple.xml")
MAINTENANT = P.date_xmltv("20261115100000 +0100")


class TestRobot(unittest.TestCase):
    def setUp(self):
        with open(EXEMPLE, "rb") as f:
            self.res = P.analyser(f, MAINTENANT)
        self.titres = {p["t"]: p for p in self.res["programmes"]}

    def test_date(self):
        self.assertEqual(P.date_xmltv("20261115201000 +0100"), P.date_xmltv("20261115191000 +0000"))

    def test_garde_le_sport_seulement(self):
        self.assertIn("Football : France / Espagne", self.titres)
        self.assertNotIn("Esprits criminels", self.titres)

    def test_exclusions(self):
        self.assertNotIn("Rugby régional", self.titres)      # France 3 régionale
        self.assertNotIn("Pro League", self.titres)          # chaîne belge
        self.assertNotIn("Football trop loin", self.titres)  # au-delà de 8 jours
        self.assertNotIn("Doublon", self.titres)             # même chaîne, même heure

    def test_disciplines(self):
        self.assertEqual(self.titres["Football : France / Espagne"]["sp"], "Football")
        self.assertEqual(self.titres["Handball : Montpellier / PSG"]["sp"], "Handball")
        self.assertEqual(self.titres["Top 14 : Toulouse / Clermont"]["sp"], "Rugby")
        self.assertEqual(self.titres["Grand Prix du Brésil"]["sp"], "Sports mécaniques")

    def test_reperes(self):
        self.assertEqual(self.titres["Handball : Montpellier / PSG"].get("live"), 1)
        self.assertEqual(self.titres["Top 14 : Toulouse / Clermont"].get("redif"), 1)
        self.assertEqual(self.titres["L'Équipe du soir"].get("mag"), 1)
        self.assertIsNone(self.titres["L'Équipe du soir"].get("ev"))
        self.assertEqual(self.titres["Football : France / Espagne"].get("ev"), 1)

    def test_chaines_dans_l_ordre(self):
        ids = [c["id"] for c in self.res["chaines"]]
        self.assertEqual(ids, ["TF1.fr", "LEquipe21.fr", "beINSPORTS1.fr"])

    def test_affiche(self):
        self.assertEqual(P.affiche("Football : Ligue 1 | PSG / OM", ""), ("PSG / OM", "Ligue 1"))
        self.assertEqual(P.affiche("Top 14", "Demi-finale"), ("Top 14", "Demi-finale"))

    def test_mot_entier(self):
        self.assertFalse(P.contient("f12 rapport", ["f1"]))
        self.assertTrue(P.contient("gp de f1 a monaco", ["f1"]))


if __name__ == "__main__":
    unittest.main()
