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
  → Summary → Progress), thème sombre Catppuccin Mocha pour matcher le
  reste de la branding Roudix.

## Structure

```
src/roudix_installer/
  main.py              # fenêtre + navigation entre pages
  state.py             # InstallState, un seul objet partagé entre les pages
  i18n.py              # gettext : tr() / trc() / tr_noop(), langue changeable à chaud
  disko_gen.py         # DiskChoice -> disko.nix
  btrfs_patch.py       # adaptation du layout btrfs
  config_gen.py        # InstallState -> bloc roudix.* pour configuration.nix
  existing_nixos.py    # mode « NixOS déjà installé » (sauvegarde /etc/nixos, pré-vérifs)
  hardware_detect.py   # détection GPU / CPU / VM / écrans / autres OS
  host_defaults.py / host_profile.py   # valeurs par défaut et profil d'hôte
  ui_helpers.py
  pages/
    welcome.py · disk.py · options.py · summary.py · progress.py · main.py
  style.css
data/disko/
  simple-efi-swap-root.nix · simple-btrfs-subvolumes.nix   # layouts de référence
po/
  roudix-installer.pot       # modèle (généré, ne pas éditer à la main)
  fr.po es.po pt_BR.po ru.po zh_CN.po hi.po ar.po
```

## Fonctionnement

- **ISO** : wizard complet (Welcome → Disk → Options → Summary → Progress), partitionnement via disko, puis `nixos-install`.
- **NixOS déjà installé** (`nix run "github:RoudineBWT/Roudix?dir=iso/roudix-installer"`) : pas de page disque, config clonée dans `~/.config/roudix`, appliquée avec `nixos-rebuild boot` ; `/etc/nixos` est sauvegardé dans `/var/backups/roudix/` avec un `RESTORE.txt`.
- Bouton *Simuler* sur la page de résumé : génère la config dans un dossier temporaire et fait évaluer le système par Nix, sans rien modifier.
- Voir [Installation](../../docs/installation.fr.md) pour le détail côté utilisateur.

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
