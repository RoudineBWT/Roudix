# Roudix Installer

Remplace Calamares. Même logique que `roudix-installer.sh`, mais avec
une interface GTK4/libadwaita et **disko** au lieu de KPMCore pour le
partitionnement.

## Pourquoi

Calamares + son module Python `nixos.py` + `packagechooser` YAML
forçaient à contourner le système de modules `roudix.*` pour exposer
des options simples (bootloader, matrixClient, waydroid...). KPMCore
ajoutait en prime des bugs de détection de partitions et de chemin
`hardware-configuration.nix`.

Ici :
- **Partitionnement** → disko décrit le layout en Nix, converti en
  `parted`/`mkfs`/mount par le paquet `disko` lui-même. Fiable, versionné,
  testable hors ISO.
- **Config système** → `config_gen.py` écrit directement le bloc
  `roudix.*` que ton script bash générait déjà, sans passer par les
  hacks Calamares.
- **UI** → wizard GTK4/libadwaita en 5 écrans (Welcome → Disk → Options
  → Summary → Progress), thème Catppuccin Mocha Peach pour matcher le
  reste de la branding Roudix.

## Structure

```
src/roudix_installer/
  main.py           # fenêtre + navigation entre pages
  state.py          # InstallState, un seul objet partagé entre les pages
  i18n.py           # gettext : tr() / trc() / tr_noop(), langue changeable à chaud
  disko_gen.py       # DiskChoice -> disko.nix
  config_gen.py      # InstallState -> bloc roudix.* pour configuration.nix
  pages/
    welcome.py
    disk.py           # sélection disque, mode simple/avancé
    options.py         # desktop/shell/kernel/bootloader/matrix/waydroid
    summary.py
    progress.py         # exécute disko puis nixos-install, logs en direct
  style.css
data/disko/
  simple-efi-swap-root.nix   # layout de référence, éditable en mode avancé
po/
  roudix-installer.pot       # modèle (généré, ne pas éditer à la main)
  fr.po                      # traduction française
```

## État actuel (scaffold)

Ce qui marche déjà dans le squelette :
- Navigation complète entre les 5 pages
- Détection réelle des disques via `lsblk`
- Génération réelle de `disko.nix` (mode simple) et du bloc `roudix.*`
- `progress.py` appelle vraiment `disko` puis `nixos-install` en sous-processus,
  avec les logs streamés dans l'UI

Ce qu'il reste à faire avant que ce soit utilisable en vrai :
- [ ] Écran mot de passe utilisateur (actuellement `password_hash` vide → pas de mdp)
- [ ] Vérifs de garde-fous (pas de disque sélectionné, pas assez d'espace...)
- [ ] Écrire le flake cible complet (`flake.nix#nixosConfigurations.roudix`), pas
      juste le fichier d'options — `config_gen.py` ne produit qu'un module à importer
- [ ] Gestion d'erreur disko (ex: disque déjà monté, LUKS si un jour tu veux du chiffrement)
- [x] i18n propre (gettext, voir « Traductions » ci-dessous)
- [ ] Packaging dans l'ISO : ajouter `roudix-installer` aux paquets du live env
      et un raccourci bureau/autostart à la place de Calamares

## Tester en local (hors ISO)

```bash
nix develop   # ou nix run .# une fois le flake complet
```

Attention : `progress.py` appelle réellement `disko` et `nixos-install` —
à tester en VM, pas sur ta machine principale.

## Traductions

Les textes sont écrits **en anglais** dans le code : `tr("Some text")`. Les traductions
vivent dans `po/<langue>.po` : `fr` (langue de référence, 100 % obligatoire en CI), `es`, `pt_BR`,
`ru`, `zh_CN`, `hi` et `ar`. L'anglais n'a pas de catalogue (c'est la langue source).
La liste proposée sur la page d'accueil est `LANGUAGES` dans `src/roudix_installer/i18n.py`.

| Fonction | Usage |
|----------|-------|
| `tr("text")` | traduit `text` |
| `trc("contexte", "text")` | idem, quand un même mot anglais a deux traductions (ex. « none » → « aucun » / « aucune ») |
| `tr_noop("text")` | marque un texte à extraire sans le traduire (tableaux), puis `tr()` à l'affichage |

Pour un texte avec des valeurs, garde des champs nommés dans le texte traduit et
formate **après** la traduction : `tr("Branch '{branch}' selected").format(branch=b)`.
N'utilise pas de f-string pour le texte à traduire (`xgettext` ne lit pas dedans).

```bash
nix develop                       # fournit gettext, just…
scripts/i18n.sh update            # après avoir ajouté/modifié des tr(...) : met à jour .pot et .po
# → traduis les entrées vides ou « fuzzy » de po/fr.po (les autres langues peuvent rester
#   en retard : l'anglais s'affiche pour les entrées manquantes, la CI ne l'exige que pour fr)
scripts/i18n.sh check             # vérifie que tout est complet (lancé aussi par la CI)
scripts/i18n.sh compile           # nécessaire pour lancer l'installeur depuis les sources
scripts/i18n.sh new de            # nouvelle langue : ajoute-la ensuite à LANGUAGES (i18n.py) ;
                                  # écriture de droite à gauche (ar, he…) : aussi à RTL_LANGS
```

Nix compile les `.po` en `.mo` à la construction du paquet (`preBuild` dans `flake.nix`).
Si un catalogue manque dans le paquet, l'installeur le dit sur stderr au lieu
de s'afficher en anglais sans rien dire.
