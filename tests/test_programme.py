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

    def test_sports_et_magazines_ecartes(self):
        self.assertNotIn("Golf : DP World Tour", self.titres)
        self.assertNotIn("MotoGP : Grand Prix de Valence", self.titres)
        self.assertNotIn("L'Équipe du soir", self.titres)
        self.assertNotIn("La Premier League sur Canal+", self.titres)

    def test_disciplines(self):
        self.assertEqual(self.titres["Football : France / Espagne"]["sp"], "Football")
        self.assertEqual(self.titres["Handball : Montpellier / PSG"]["sp"], "Handball")
        self.assertEqual(P.discipline("rugby", "top 14 : toulouse / clermont", "", ""), "Rugby")
        self.assertEqual(self.titres["Grand Prix du Brésil"]["sp"], "Sports mécaniques")

    def test_reperes(self):
        self.assertEqual(self.titres["Handball : Montpellier / PSG"].get("live"), 1)
        self.assertNotIn("Top 14 : Toulouse / Clermont", self.titres)  # rediffusion écartée
        self.assertEqual(self.titres["Football : France / Espagne"].get("ev"), 1)

    def test_rediffusions(self):
        h = lambda txt: P.date_xmltv(txt)
        progs = [
            {"c": "A", "d": h("20261115210000 +0100"), "t": "Lens / Marseille", "sp": "Football"},
            {"c": "B", "d": h("20261116180000 +0100"), "t": "Lens / Marseille", "sp": "Football"},
            {"c": "C", "d": h("20261116180500 +0100"), "t": "Lens / Marseille", "sp": "Handball"},
            {"c": "A", "d": h("20261116090000 +0100"), "t": "Nice / Lyon", "sp": "Football"},
            {"c": "A", "d": h("20261116200000 +0100"), "t": "Brest / Lorient", "sp": "Football",
             "ds": "Match de la Journée 11 du Championnat de France de Ligue 1 2026/27 opposant"},
            {"c": "A", "d": h("20261117140000 +0100"), "t": "Auxerre / Paris FC", "sp": "Football",
             "ds": "Match de la Journée 10 du Championnat de France de Ligue 1 2026/27 opposant"},
        ]
        progs.sort(key=lambda p: p["d"])
        vus = {}
        P.marquer_rediffs(progs, vus)
        r = {(p["t"], p["c"]): p.get("redif") for p in progs}
        self.assertIsNone(r[("Lens / Marseille", "A")])     # première diffusion
        self.assertEqual(r[("Lens / Marseille", "B")], 1)   # rediffusion le lendemain
        self.assertIsNone(r[("Lens / Marseille", "C")])     # autre sport
        self.assertEqual(r[("Nice / Lyon", "A")], 1)        # foot au petit matin
        self.assertEqual(r[("Auxerre / Paris FC", "A")], 1) # journée déjà passée
        self.assertIn("football|lens / marseille", vus)

    def test_indices_dans_le_resume(self):
        d = P.date_xmltv("20261117140000 +0100")
        self.assertTrue(P.date_passee("le 14 novembre 2026, l'algerie accueillera le togo", d))
        self.assertFalse(P.date_passee("le 17 novembre a rabat, le niger defiera le maroc", d))
        self.assertTrue(any(__import__("re").search(m, "1ere periode du match de la journee 10") for m in P.DESC_REDIF))

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
