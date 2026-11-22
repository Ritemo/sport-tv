# Sport TV

Le programme du sport à la télé en France, sans publicité, filtré sur mes sports et mes chaînes.

## Comment ça marche

```
Guide TV public xmltvfr.fr (toutes les chaînes françaises, 8 jours)
   │  robot : GitHub Actions, 2 fois par jour (Python, sans dépendance)
   ▼
data/programme.json  (seulement le sport, avec la discipline devinée)
   │
   ▼
Appli (PWA) sur GitHub Pages : https://ritemo.github.io/sport-tv/
```

| Élément | Rôle |
|---|---|
| `collector/programme.py` | Le robot. Télécharge le guide (environ 80 Mo), garde le sport, devine la discipline (Football, Rugby, Handball...), repère les directs et les magazines, et retire les rediffusions |
| `config.json` | Les réglages : adresses du guide, nombre de jours, sports gardés (`sports_gardes`), mots qui écartent un programme (`mots_exclus`, par exemple MotoGP, rallye, patinage, padel), magazines gardés ou non (`garder_magazines`), rediffusions gardées ou non (`garder_rediffusions`, non par défaut), chaînes gardées (`chaines_generalistes`, où seul le sport est gardé, et `chaines_sport`), écrans de remplissage à écarter (`titres_remplissage`), ordre d'affichage |
| `.github/workflows/collecte.yml` | Lance le robot vers 4h40 et 16h15 (heure d'hiver ; une heure de plus en été) |
| `.github/workflows/tests.yml` | Vérifie le robot à chaque modification |
| `index.html`, `sw.js`, `manifest.webmanifest`, `icons/` | L'appli |
| `data/meta.json` | Journal du dernier passage : heure, nombre de programmes, nombre par sport |
| `data/vus.json` | Mémoire du robot : les affiches déjà diffusées ces 3 dernières semaines, pour reconnaître leurs rediffusions |

## Mise en ligne (une seule fois)

1. Sur github.com, créer le dépôt **Ritemo/sport-tv** en **public** (nécessaire pour GitHub Pages gratuit).
2. Y mettre tous les fichiers : *Add file > Upload files*, glisser le contenu du dossier (y compris les dossiers `.github`, `collector`, `data`, `icons`, `tests`).
3. **Settings > Actions > General > Workflow permissions** : cocher « Read and write permissions », puis *Save*.
4. **Actions > Mise à jour du programme > Run workflow** pour le premier passage (2 à 3 minutes).
5. **Settings > Pages** : Source « Deploy from a branch », branche `main`, dossier `/ (root)`.
6. L'appli est sur `https://ritemo.github.io/sport-tv/`. Sur Android : menu de Chrome > « Ajouter à l'écran d'accueil ». Pour un APK, passer l'adresse dans PWABuilder.

## Utilisation

- **Réglages** (bouton à curseurs en haut à droite) : cocher ses sports, décocher les chaînes qu'on ne reçoit pas (« TNT gratuite seulement » en un geste). C'est gardé sur le téléphone.
- **Heures** : toujours à l'heure de Paris, même si le téléphone est réglé sur un autre fuseau.
- **Jours** : aujourd'hui et les 7 suivants. Les programmes terminés disparaissent, celui en cours est encadré avec une barre de progression.
- **Puces de sport** : pour ne voir qu'un sport un moment.
- **Matchs et courses** (cache les magazines et émissions de plateau) : filtre rapide, gardé aussi. Les rediffusions ne sont jamais affichées : le robot les retire (voir plus bas). Le badge « Direct » apparaît quand le guide le précise.
- **Loupe** : chercher une équipe ou une compétition (« PSG », « Starligue ») sur toute la semaine.
- Toucher un programme affiche sa description.
- **Doublons** : quand un même match passe sur plusieurs chaînes (Canal+, Canal+ Foot, Canal+ Live, 4K...), il n'apparaît qu'une fois. L'étiquette montre la chaîne principale, « +3 » signale les autres, listées sous le titre (« Aussi sur... »). Si tu décoches la chaîne principale dans les réglages, c'est une des autres qui s'affiche.
- **Aujourd'hui** : « En ce moment » montre pour chaque programme une frise (début, avancement, fin) et le temps restant. Ceux qui ont le plus de temps devant eux sont en haut ; ceux qui finissent dans moins de 15 minutes sont grisés en bas (« Bientôt fini »). Viennent ensuite « Ça commence bientôt » (dans les 2 heures, avec « Dans 25 min », en rouge sous 15 minutes), puis le reste de la journée. L'affichage se rafraîchit toutes les minutes.
- **Mettre à jour** (flèche ronde en haut, ou bouton en bas de liste) : recharge le dernier programme préparé par le robot et installe la nouvelle version de l'appli s'il y en a une. Le robot, lui, passe deux fois par jour.
- Chaque sport a son icône et sa couleur (liseré à gauche de la carte, barre de progression du programme en cours).

## Gestes courants

- **Ajouter ou retirer un sport** : liste `sports_gardes` dans `config.json` (noms possibles : ceux de la liste `SPORTS` du robot). Pour écarter seulement une partie d'un sport (exemple : le rallye dans les sports mécaniques), ajouter le mot à `mots_exclus`, en minuscules sans accents.

- **Un sport mal classé** : ajouter le mot clé dans la liste `SPORTS` en haut de `collector/programme.py` (mots en minuscules, sans accents). L'ordre compte : le premier sport trouvé gagne.
- **Une chaîne manque** : l'ajouter dans `config.json` à `chaines_sport` (chaîne de sport) ou à `chaines_generalistes` (chaîne généraliste), avec son identifiant xmltvfr (exemple : `Eurosport1.fr`).
- **Un faux programme s'affiche** (écran d'attente, pub maison) : ajouter un morceau de son titre, en minuscules sans accents, à `titres_remplissage`.
- **Une rediffusion passe quand même** : le robot écarte un programme quand le guide le dit (rediffusion, différé), quand le résumé l'indique (« 1ère période du match », « retransmission d'un match », date déjà passée), quand la même affiche est déjà passée plus de 3 heures avant, quand le match appartient à une journée de championnat plus ancienne qu'une journée déjà diffusée, ou quand un match de foot ou de hand passe entre 1 h et 11 h 30. Ces règles sont dans `marquer_rediffs` de `collector/programme.py`. Le robot apprend au fil des passages : un match vu en direct est reconnu ensuite dans ses rediffusions.
- **Changer l'ordre des chaînes** : `ordre_chaines` dans `config.json`.
- **Après une modification de l'appli** : changer la version dans `sw.js` (`sport-tv-v1` devient `sport-tv-v2`), sinon les téléphones gardent l'ancienne.

## En cas de souci

Si le robot échoue, GitHub envoie un mail et le passage apparaît en rouge dans l'onglet *Actions*. L'appli affiche aussi un bandeau si le programme a plus de 36 heures.

- « Aucune source disponible » : le site xmltvfr.fr était injoignable. Le robot réessaie au passage suivant ; l'appli garde le dernier programme et affiche un bandeau s'il a plus de 36 heures. Si ça dure plusieurs jours, vérifier sur https://xmltvfr.fr que les adresses de `sources` dans `config.json` sont toujours les bonnes.
- « Seulement N programmes de sport » : le guide est arrivé incomplet. Même chose, attendre le passage suivant.
- « Tests en échec » : la dernière modification a cassé le robot. Onglet *Actions*, ouvrir le passage en rouge pour lire l'erreur, ou demander à Claude.

## Source des données

Guide XMLTV du projet libre XML TV Fr (https://xmltvfr.fr, code sur github.com/racacax/XML-TV-Fr). Les horaires peuvent bouger au dernier moment : le robot repasse l'après-midi pour en tenir compte.
