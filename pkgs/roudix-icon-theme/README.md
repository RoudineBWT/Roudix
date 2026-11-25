# Roudix — thème d'icônes natif

Thème autonome fait pour Roudix, en complément de Tela-Roudix et Papirus-Roudix (qui restent inchangés).
Deux variantes : **Roudix** (tuiles sombres) et **Roudix-Light** (tuiles crème).

## Style
Repris des icônes Roudix existantes (`io.roudix.store.svg`) et de `Roudix.json` :
carré arrondi 48×48 (`rx=10`), dégradé chaud, reflet en haut, liseré fin, glyphe orange
(`#ffc878 → #ff8c42` en sombre, `#e0661a → #c98a1e` en clair).

## Comment les icônes d'apps sont produites
1. **Logos de marques** (simple-icons) : recentrés, redimensionnés d'après leur vraie boîte englobante, recolorés en dégradé orange.
   Les wordmarks illisibles en carré (zoom, vmware, kicad) sont remplacés par un glyphe Roudix.
2. **Marques absentes de simple-icons** : redessinées à la main, inspirées des formes de Tela/Papirus
   (VS Code, Slack, Edge, Chromium, Word, Excel, PowerPoint, Outlook, OneNote, Office, Teams, Skype, Messenger, Typora, Remmina).
3. **Toutes les autres apps** (~940 noms) : l'icône d'origine de **Tela** (sinon **Papirus**) est **convertie en style Roudix** :
   les couleurs du SVG sont remappées par luminance sur une rampe brun → orange → crème, puis l'icône est insérée dans la tuile Roudix.
   Chaque app garde sa forme reconnaissable, en palette Roudix, et tout reste vectoriel.
4. Les ~90 noms sans icône source exploitable (noms génériques FreeDesktop) ont un glyphe Lucide dans la tuile.

## Contenu
| Dossier | Contenu |
|---|---|
| `scalable/apps` | ~220 logos de marques + ~700 icônes converties + une quarantaine de glyphes génériques |
| `scalable/categories` | `applications-*`, `preferences-*` |
| `scalable/places` | dossiers Roudix (nu, ouvert, documents, téléchargements, musique, images, vidéos, git…), maison, bureau, corbeille (vide/pleine), réseau, **logo Roudix** en `start-here` / `distributor-logo` |
| `scalable/mimetypes` | pages Roudix avec un glyphe par famille (texte, PDF, image, audio, vidéo, archive, code, tableur, présentation, police, base de données…) |
| `scalable/devices` | disques, clé USB, optique, clavier, souris, manette, imprimante, casque, webcam, batterie, bluetooth… |

**Noms d'icônes** : pris sur Tela (fichiers + alias) ; les alias sont des liens symboliques. `mapping.json` détaille les apps
(`apps_brand`, `apps_imported`, `apps_generic`). Aperçus dans `previews/`.

## Icônes d'interface (actions / tray / statuts)
Pas redessinées : ce sont les jeux **monochromes 16/22/24 px de Papirus-Dark** (Papirus-Light pour la variante claire),
embarqués et **recolorés en orange Roudix** (primaire de `Roudix.json` : `#FF8C42` sombre, `#E0661A` clair ; rouge/vert/orange sémantiques conservés) (`16x16|22x22|24x24/{actions,panel,status}`, déclarés **avant** `scalable/*` dans `index.theme`).
Aux petites tailles (barres d'outils, tray, menus) on a donc `go-previous`, `edit-find`, `audio-volume-*`, engrenage,
écran… ; à 32 px et plus, les tuiles Roudix. Sans ça, si le thème parent ne fournit pas le nom, KDE/Qt le tronque
(`go-previous` → `go`) et tombe sur une icône d'app en tuile (gopher Go, haut-parleur Tela…).
Pour régénérer : `python3 tools/add_papirus_ui.py <dépôt papirus-icon-theme>`.

## Ce qui n'est pas dessiné
Les icônes **symboliques** (`*-symbolic`) ne sont pas embarquées : elles viennent du thème parent (Papirus dans Roudix, Adwaita/Breeze sinon).

## Utilisation dans Roudix
Le thème est un paquet Nix (`default.nix`, `nix build .#roudix-icon-theme`) branché sur l'option existante :

    roudix.iconTheme = "roudix";        # tuiles sombres
    roudix.iconTheme = "roudix-light";  # tuiles crème

(aussi dans `roudix-switcher`, page « Icon Theme »). Le défaut reste `"papirus"` ; Papirus-Roudix et Tela-Roudix
sont inchangés. Le thème hérite de Papirus-Dark (Papirus-Light pour la variante claire) pour les icônes
symboliques et tout ce qu'il ne dessine pas, donc Papirus est installé avec lui.

Hors Roudix : copier `Roudix` (et/ou `Roudix-Light`) dans `~/.local/share/icons/` ; `index.theme` y hérite
d'Adwaita/Breeze (la version Nix remplace ce `Inherits` par Papirus).

## Compatibilité Qt / KDE (important)
Qt (QtSvg = SVG Tiny 1.2, donc Plasma, Dolphin, Kickoff, le panneau…) **ignore les `<svg>` imbriqués**.
Les icônes ne doivent donc jamais contenir de `<svg x= y= width= height= viewBox=>` dans la tuile : le glyphe est
placé avec `<g clip-path><g transform="translate() scale()">` (`tools/flatten_nested_svg.py`, utilisé par
`build_roudix.py` et `extras_complete.py`). Si des tuiles s'affichent vides sous KDE, lancer :

    python3 tools/flatten_nested_svg.py Roudix Roudix-Light

## Régénérer
`pip install svgelements` puis
`python3 tools/build_roudix.py <Tela-icon-theme> <simple-icons/package> <lucide-static/package> <roudix-logo.svg> <sortie> [<Papirus>/64x64/apps]`

Puis les retouches par-dessus (à relancer après chaque régénération) :

    python3 tools/extras.py                                              # dossier Bureau, zip à fermeture éclair, .nix
    python3 tools/extras_apps.py <simple-icons/package> <lucide-static/package>   # apps manquantes + icônes io.roudix.*
    python3 tools/extras_complete.py <Tela-icon-theme> <Papirus>/64x64/apps       # tous les noms Tela/Papirus restants

## Licences
**Attention : une partie du thème est en GPL-3.0** (icônes converties depuis Tela/Papirus). Détails et option « sans GPL » dans `LICENSES.md`.
