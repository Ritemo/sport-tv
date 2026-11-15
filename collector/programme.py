"""Robot du programme TV sport.

Télécharge le guide XMLTV public de xmltvfr.fr, garde uniquement les
programmes de sport des prochains jours, devine la discipline et écrit
data/programme.json (lu par l'appli) et data/meta.json (journal).
Aucune dépendance : uniquement la bibliothèque standard de Python.
"""
import gzip
import io
import json
import re
import sys
import time
import unicodedata
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CONFIG = json.loads((RACINE / "config.json").read_text(encoding="utf-8"))
DATA = RACINE / "data"

# Discipline -> mots clés (sans accents, en minuscules). L'ordre compte :
# la première discipline trouvée gagne, du plus précis au plus général.
SPORTS = [
    ("Handball", ["handball", "starligue", "proligue", "ligue butagaz", "hand "]),
    ("Rugby", ["rugby", "top 14", "pro d2", "six nations", "6 nations", "champions cup", "challenge cup", "xv de france", "super rugby"]),
    ("Basket", ["basket", "nba", "betclic elite", "euroligue", "euroleague", "wnba", "eurocup"]),
    ("Volley", ["volley", "beach-volley"]),
    ("Tennis", ["tennis", "atp", "wta", "roland-garros", "roland garros", "wimbledon", "open d'australie", "coupe davis", "billie jean king", "masters 1000", "padel"]),
    ("Cyclisme", ["cyclisme", "tour de france", "giro", "vuelta", "paris-roubaix", "cyclo-cross", "cyclocross", "vtt", "criterium du dauphine", "paris-nice", "milan-san remo", "tour des flandres", "liege-bastogne"]),
    ("Équitation", ["equitation", "hippisme", "course hippique", "courses hippiques", "turf", "trot", "galop", "pmu", "jumping", "dressage"]),
    ("Sports mécaniques", ["formule 1", "formula 1", "f1", "grand prix", "motogp", "moto gp", "rallye", "wrc", "nascar", "indycar", "endurance", "24 heures du mans", "superbike", "formule e", "dakar", "motocross", "supercross", "karting", "sport auto", "sports mecaniques"]),
    ("Golf", ["golf", "pga", "ryder cup", "lpga", "dp world tour"]),
    ("Sports d'hiver", ["biathlon", "ski", "slalom", "descente", "super-g", "snowboard", "saut a ski", "combine nordique", "patinage", "luge", "bobsleigh", "curling", "freestyle"]),
    ("Hockey", ["hockey sur glace", "nhl", "ligue magnus", "hockey"]),
    ("Sports US", ["nfl", "football americain", "super bowl", "mlb", "baseball"]),
    ("Combat", ["boxe", "mma", "ufc", "pfl", "judo", "karate", "taekwondo", "lutte", "kickboxing", "muay thai", "catch", "wwe", "escrime"]),
    ("Athlétisme", ["athletisme", "marathon", "diamond league", "trail", "decathlon", "cross-country", "triathlon"]),
    ("Natation", ["natation", "plongeon", "water-polo", "water polo", "nage"]),
    ("Sports nautiques", ["voile", "vendee globe", "route du rhum", "surf", "aviron", "canoe", "kayak"]),
    ("Fléchettes et billard", ["flechettes", "darts", "snooker", "billard", "petanque"]),
    ("Gymnastique", ["gymnastique", "trampoline"]),
    ("Football", ["football", "foot", "ligue 1", "ligue 2", "ligue des champions", "champions league", "ligue europa", "europa league", "conference league", "premier league", "liga", "serie a", "bundesliga", "coupe de france", "coupe du monde", "arkema", "futsal", "mls", "telefoot", "eredivisie", "fa cup"]),
]
AUTRE = "Autres sports"

# Indices qu'un programme est du sport, quand la catégorie est vague.
MOTS_SPORT = ["sport", "match", "championnat", "coupe", "tournoi", "grand prix", "jeux olympiques", "jeux paralympiques", "finale", "demi-finale", "etape"]
MOTS_PAS_SPORT = ["film", "serie", "telefilm", "jeunesse", "dessin anime", "documentaire animalier", "telerealite", "jeu", "meteo", "feuilleton", "programme indetermine", "fin des programmes"]
MOTS_MAGAZINE = ["magazine", "debat", "talk", "journal", "info", "plateau", "emission", "actualite", "information", "late show", "reportage", "documentaire", "resume", "best of", "zapping"]
TITRES_MAGAZINE = ["mag", "magazine", "jt", "journal", "matinale", "club", "l'equipe du soir", "l'equipe de greg", "stade 2", "tout le sport", "telefoot", "l'essentiel", "debrief", "quotidienne", "late football club", "after foot", "zapsport", "le match dans le match", "c'est de la balle", "intergalactique", "reportage", "portrait", "les grands matchs", "resume", "highlights", "best of", "on board", "lundi grand prix", "documentaire", "serie documentaire"]
MOTS_EVENEMENT = ["retransmission", "en direct", "diffusion d'un match", "match", "course", "manche", "etape", "grand prix", "finale", "demi-finale", "slalom", "sprint", "poursuite", "combat", "journee", "tournoi", "qualifications", "essais", "qualifs", "rencontre", "affronte", "recoit", "se deplace", "championnat du monde", "coupe du monde"]
MOTS_DIRECT = ["en direct", "direct", "live"]
MOTS_REDIF = ["rediffusion", "redif", "differe", "replay", "multidiffusion", "en integralite"]


def sans_accents(txt):
    txt = unicodedata.normalize("NFD", txt or "")
    return "".join(c for c in txt if unicodedata.category(c) != "Mn").lower()


def contient(txt, mots):
    """Mot clé présent comme mot entier (pas 'f1' dans 'f12')."""
    for m in mots:
        if re.search(r"(?<![a-z0-9])" + re.escape(m.strip()) + r"(?![a-z0-9])", txt):
            return True
    return False


def discipline(categories, titre, sous_titre, desc):
    """Renvoie la discipline, en regardant d'abord les catégories puis le titre."""
    for zone in (categories, titre + " " + sous_titre, desc[:250]):
        for nom, mots in SPORTS:
            if contient(zone, mots):
                return nom
    return AUTRE


def est_sport(categories, titre, sous_titre, chaine_sport):
    if contient(categories, MOTS_PAS_SPORT) and "sport" not in categories:
        return False
    if "sport" in categories:
        return True
    zone = categories + " " + titre + " " + sous_titre
    if any(contient(categories, mots) for _, mots in SPORTS):
        return True
    if chaine_sport:
        # Sur une chaîne de sport, tout est sport sauf le remplissage.
        return not contient(zone, ["fin des programmes", "programme non communique", "pause", "teleachat"])
    return contient(titre + " " + sous_titre, ["football", "rugby", "handball", "basket", "tennis", "cyclisme", "biathlon", "formule 1", "ligue des champions", "ligue 1", "top 14", "jeux olympiques", "tour de france", "roland-garros", "six nations", "motogp"])


def affiche(titre, sous_titre):
    """'Football : Ligue 1 | PSG / OM' -> titre 'PSG / OM', sous-titre 'Ligue 1'."""
    if " | " not in titre:
        return titre, sous_titre
    avant, apres = titre.split(" | ", 1)
    competition = avant.split(" : ", 1)[1] if " : " in avant else avant
    return apres.strip(), " · ".join(x for x in (competition.strip(), sous_titre) if x)


def date_xmltv(txt):
    """'20261115201000 +0100' -> secondes depuis 1970 (UTC)."""
    txt = (txt or "").strip()
    m = re.match(r"(\d{14})\s*([+-]\d{4})?", txt)
    if not m:
        return None
    d = datetime.strptime(m.group(1), "%Y%m%d%H%M%S")
    dec = m.group(2) or "+0000"
    signe = 1 if dec[0] == "+" else -1
    minutes = signe * (int(dec[1:3]) * 60 + int(dec[3:5]))
    return int(d.replace(tzinfo=timezone.utc).timestamp()) - minutes * 60


CHAINES = set(CONFIG["chaines_generalistes"]) | set(CONFIG["chaines_sport"])


def chaine_exclue(cid):
    """Seules les chaînes listées dans config.json sont gardées."""
    return cid not in CHAINES


def remplissage(titre):
    """Écrans d'attente des chaînes événementielles, pubs maison, etc."""
    return any(re.search(m, titre) for m in CONFIG["titres_remplissage"])


def telecharger():
    """Essaie chaque source dans l'ordre ; renvoie un flux XML lisible."""
    erreurs = []
    for url in CONFIG["sources"]:
        for essai in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "sport-tv (appli perso, github.com/Ritemo)"})
                with urllib.request.urlopen(req, timeout=180) as r:
                    brut = r.read()
                if url.endswith(".gz"):
                    brut = gzip.decompress(brut)
                elif url.endswith(".zip"):
                    with zipfile.ZipFile(io.BytesIO(brut)) as z:
                        nom = next(n for n in z.namelist() if n.endswith(".xml"))
                        brut = z.read(nom)
                if b"<tv" not in brut[:2000]:
                    raise ValueError("ce n'est pas un fichier XMLTV")
                return url, io.BytesIO(brut)
            except Exception as e:  # noqa: BLE001
                erreurs.append(f"{url} (essai {essai + 1}) : {e}")
                time.sleep(10)
    raise RuntimeError("Aucune source disponible :\n" + "\n".join(erreurs))


def texte(el, balise):
    sous = el.find(balise)
    return (sous.text or "").strip() if sous is not None and sous.text else ""


def analyser(flux, maintenant=None):
    """Lit le XMLTV en continu (fichier de ~80 Mo) et garde le sport."""
    maintenant = maintenant or int(time.time())
    limite = maintenant + CONFIG["jours"] * 86400
    sport_ids = set(CONFIG["chaines_sport"])
    chaines, progs, vus = {}, [], set()
    for _, el in ET.iterparse(flux, events=("end",)):
        if el.tag == "channel":
            cid = el.get("id", "")
            if not chaine_exclue(cid):
                chaines[cid] = {"nom": texte(el, "display-name") or cid,
                                "logo": (el.find("icon").get("src") if el.find("icon") is not None else "")}
            el.clear()
        elif el.tag == "programme":
            cid = el.get("channel", "")
            debut, fin = date_xmltv(el.get("start")), date_xmltv(el.get("stop"))
            if cid in chaines and debut and fin and fin > maintenant - 3600 and debut < limite and fin - debut >= 5 * 60:
                titre, st = texte(el, "title"), texte(el, "sub-title")
                desc = texte(el, "desc")
                cats = sans_accents(" | ".join((c.text or "") for c in el.findall("category")))
                t, s = sans_accents(titre), sans_accents(st)
                if not remplissage(t) and est_sport(cats, t, s, cid in sport_ids):
                    cle = (cid, debut)
                    if cle not in vus:
                        vus.add(cle)
                        tout = t + " " + s + " " + sans_accents(desc[:300])
                        mots_cles = sans_accents(" ".join((k.text or "") for k in el.findall("keyword")))
                        direct = contient(t + " " + s + " " + mots_cles, MOTS_DIRECT) or el.find("live") is not None
                        redif = el.find("previously-shown") is not None or contient(t + " " + s, MOTS_REDIF)
                        if direct and contient(t + " " + s, ["differe", "rediffusion"]):
                            direct = False
                        magazine = (contient(cats, MOTS_MAGAZINE) or contient(t + " " + s, TITRES_MAGAZINE) or re.search(r"saison \d", t)) and not contient(cats, ["match", "retransmission"])
                        sport = discipline(cats, t, s, sans_accents(desc))
                        if sport not in CONFIG["sports_gardes"] or contient(cats + " " + t + " " + s, CONFIG["mots_exclus"]):
                            el.clear()
                            continue
                        if magazine and not CONFIG["garder_magazines"]:
                            el.clear()
                            continue
                        titre, st = affiche(titre, st)
                        p = {"c": cid, "d": debut, "f": fin, "t": titre, "sp": sport}
                        if st:
                            p["st"] = st
                        if desc:
                            p["ds"] = desc[:220] + ("..." if len(desc) > 220 else "")
                        if direct:
                            p["live"] = 1
                        if redif and not direct:
                            p["redif"] = 1
                        if magazine:
                            p["mag"] = 1
                        # Événement : un match, une course, une étape... (pas un magazine)
                        elif direct or " / " in titre or contient(tout, MOTS_EVENEMENT):
                            p["ev"] = 1
                        progs.append(p)
            el.clear()
    utilisees = {p["c"] for p in progs}
    ordre = {c: i for i, c in enumerate(CONFIG["ordre_chaines"])}
    liste = sorted(utilisees, key=lambda c: (ordre.get(c, 999), chaines[c]["nom"].lower()))
    progs.sort(key=lambda p: (p["d"], ordre.get(p["c"], 999)))
    return {"chaines": [{"id": c, **chaines[c]} for c in liste], "programmes": progs}



def main():
    debut = time.time()
    try:
        url, flux = telecharger()
        res = analyser(flux)
        nb = len(res["programmes"])
        if nb < 50:
            raise RuntimeError(f"Seulement {nb} programmes de sport trouvés, le guide semble incomplet.")
    except Exception as e:  # noqa: BLE001
        print("ERREUR :", e, file=sys.stderr)
        sys.exit(1)
    DATA.mkdir(exist_ok=True)
    (DATA / "programme.json").write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    par_sport = {}
    for p in res["programmes"]:
        par_sport[p["sp"]] = par_sport.get(p["sp"], 0) + 1
    meta = {"maj": int(time.time()), "source": url, "programmes": nb, "chaines": len(res["chaines"]),
            "par_sport": dict(sorted(par_sport.items(), key=lambda x: -x[1])), "duree_s": round(time.time() - debut)}
    (DATA / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
