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
| `collector/programme.py` | Le robot. Télécharge le guide (environ 80 Mo), garde le sport, devine la discipline (Football, Rugby, Handball...), repère les directs, rediffusions et magazines |
| `config.json` | Les réglages : adresses du guide, nombre de jours, chaînes gardées (`chaines_generalistes`, où seul le sport est gardé, et `chaines_sport`), écrans de remplissage à écarter (`titres_remplissage`), ordre d'affichage |
| `.github/workflows/collecte.yml` | Lance le robot vers 4h40 et 16h15 (heure d'hiver ; une heure de plus en été) |
| `.github/workflows/tests.yml` | Vérifie le robot à chaque modification |
| `index.html`, `sw.js`, `manifest.webmanifest`, `icons/` | L'appli |
| `data/meta.json` | Journal du dernier passage : heure, nombre de programmes, nombre par sport |

## Mise en ligne (une seule fois)

1. Sur github.com, créer le dépôt **Ritemo/sport-tv** en **public** (nécessaire pour GitHub Pages gratuit).
2. Y mettre tous les fichiers : *Add file > Upload files*, glisser le contenu du dossier (y compris les dossiers `.github`, `collector`, `data`, `icons`, `tests`).
3. **Settings > Actions > General > Workflow permissions** : cocher « Read and write permissions », puis *Save*.
4. **Actions > Mise à jour du programme > Run workflow** pour le premier passage (2 à 3 minutes).
5. **Settings > Pages** : Source « Deploy from a branch », branche `main`, dossier `/ (root)`.
6. L'appli est sur `https://ritemo.github.io/sport-tv/`. Sur Android : menu de Chrome > « Ajouter à l'écran d'accueil ». Pour un APK, passer l'adresse dans PWABuilder.

## Utilisation

- **Réglages** (bouton à curseurs en haut à droite) : cocher ses sports, décocher les chaînes qu'on ne reçoit pas (« TNT gratuite seulement » en un geste). C'est gardé sur le téléphone.
- **Jours** : aujourd'hui et les 7 suivants. Les programmes terminés disparaissent, celui en cours est encadré avec une barre de progression.
- **Puces de sport** : pour ne voir qu'un sport un moment.
- **Matchs et courses** (cache les magazines et émissions de plateau) et **Sans rediffs** : filtres rapides, gardés aussi. Le badge « Direct » apparaît quand le guide le précise.
- **Loupe** : chercher une équipe ou une compétition (« PSG », « Starligue ») sur toute la semaine.
- Toucher un programme affiche sa description.

## Gestes courants

- **Un sport mal classé** : ajouter le mot clé dans la liste `SPORTS` en haut de `collector/programme.py` (mots en minuscules, sans accents). L'ordre compte : le premier sport trouvé gagne.
- **Une chaîne manque** : l'ajouter dans `config.json` à `chaines_sport` (chaîne de sport) ou à `chaines_generalistes` (chaîne généraliste), avec son identifiant xmltvfr (exemple : `Eurosport1.fr`).
- **Un faux programme s'affiche** (écran d'attente, pub maison) : ajouter un morceau de son titre, en minuscules sans accents, à `titres_remplissage`.
- **Changer l'ordre des chaînes** : `ordre_chaines` dans `config.json`.
- **Après une modification de l'appli** : changer la version dans `sw.js` (`sport-tv-v1` devient `sport-tv-v2`), sinon les téléphones gardent l'ancienne.

## En cas de souci

Si le robot échoue, GitHub envoie un mail et le passage apparaît en rouge dans l'onglet *Actions*. L'appli affiche aussi un bandeau si le programme a plus de 36 heures.

- « Aucune source disponible » : le site xmltvfr.fr était injoignable. Le robot réessaie au passage suivant ; l'appli garde le dernier programme et affiche un bandeau s'il a plus de 36 heures. Si ça dure plusieurs jours, vérifier sur https://xmltvfr.fr que les adresses de `sources` dans `config.json` sont toujours les bonnes.
- « Seulement N programmes de sport » : le guide est arrivé incomplet. Même chose, attendre le passage suivant.
- « Tests en échec » : la dernière modification a cassé le robot. Onglet *Actions*, ouvrir le passage en rouge pour lire l'erreur, ou demander à Claude.

## Source des données

Guide XMLTV du projet libre XML TV Fr (https://xmltvfr.fr, code sur github.com/racacax/XML-TV-Fr). Les horaires peuvent bouger au dernier moment : le robot repasse l'après-midi pour en tenir compte.
