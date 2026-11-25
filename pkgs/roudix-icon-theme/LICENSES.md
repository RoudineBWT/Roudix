# Licences

Le thème mélange plusieurs sources, avec des licences différentes.

| Partie | Fichiers | Licence |
|---|---|---|
| Icônes **converties depuis Tela / Papirus** | `scalable/apps/roudix-*.svg` (hors `roudix-generic-*`) — liste dans `mapping.json` → `apps_imported` | **GPL-3.0** (œuvres dérivées de Tela et Papirus, voir `COPYING-GPL-3.0`) |
| Logos de marques (simple-icons) | `scalable/apps/<slug>.svg` | SVG sous CC0 ; les marques restent la propriété de leurs détenteurs |
| Glyphes génériques (Lucide) | `roudix-generic-*`, catégories, périphériques, lieux, types MIME | ISC |
| Dossiers, tuiles, pages, marques redessinées (VS Code, Slack, Edge, Chromium, Office, Teams, Skype…), scripts | le reste | MIT, comme Roudix |
| Logo Roudix | `start-here` & alias | licence du dépôt Roudix |

## Important pour le dépôt Roudix (MIT)
Les ~700 icônes converties de Tela/Papirus sont sous **GPL-3.0** : en les redistribuant, ce sous-ensemble reste GPL-3.0
(listé dans le `THIRD_PARTY.md` à la racine). Si tu veux un thème 100 % permissif, génère-le sans elles :

    ROUDIX_NO_IMPORT=1 python3 tools/build_roudix.py <Tela> <simple-icons/package> <lucide-static/package> <logo.svg> <sortie>

Les apps concernées retombent alors sur les glyphes génériques Lucide.

## Icônes d'interface Papirus (actions / panel / status)
`Roudix/{16x16,22x22,24x24}/{actions,panel,status}` (Papirus-Dark) et `Roudix-Light/…` (Papirus-Light) sont copiés (puis recolorés en orange Roudix) depuis Papirus Icon Theme — **GPL-3.0** (voir `COPYING-GPL-3.0`). Source : https://github.com/PapirusDevelopmentTeam/papirus-icon-theme
