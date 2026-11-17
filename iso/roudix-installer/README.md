# Roudix Installer

Remplace Calamares. Un seul installeur, deux interfaces : un wizard
GTK4/libadwaita **ou** un wizard dans le terminal (TUI, qui remplace l'ancien
`roudix-installer.sh`). **disko** remplace KPMCore pour le partitionnement.

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
  `roudix.*`, sans passer par les hacks Calamares.
- **UI** → wizard GTK4/libadwaita en 5 écrans (Welcome → Disk → Options
  → Summary → Progress), thème sombre Catppuccin Mocha pour matcher le
  reste de la branding Roudix. Le même parcours existe en terminal (`--tui`) :
  il n'a qu'une seule logique à maintenir, `runner.py`, `questions.py` et
  `choices.py` sont partagés.

## Structure

```
src/roudix_installer/
  main.py              # point d'entrée : choisit GUI ou TUI (--gui / --tui / auto)
  gui.py               # fenêtre GTK + navigation entre pages
  tui.py               # wizard terminal (bibliothèque standard uniquement, aucun import de gi)
  runner.py            # l'installation elle-même (partition, config, nixos-install) — partagé GUI/TUI
  questions.py         # les questions d'options en données + règles de visibilité (TUI)
  choices.py           # listes de choix (noyaux, bureaux, navigateurs…) — partagées GUI/TUI
  summary_rows.py      # le récapitulatif avant installation — partagé GUI/TUI
  disks.py             # lsblk : disques et partitions — partagé GUI/TUI
  multiboot.py         # autres systèmes du menu EFI -> entrées Limine (efibootmgr), GUI et TUI
  sysutil.py           # lecture « best effort » de faits système (efibootmgr, dmidecode…)
  state.py             # InstallState, un seul objet partagé entre les pages
  i18n.py              # gettext : tr() / trc() / tr_noop(), langue changeable à chaud
  disko_gen.py         # DiskChoice -> disko.nix
  btrfs_patch.py       # adaptation du layout btrfs
  config_gen.py        # InstallState -> bloc roudix.* pour configuration.nix
  existing_nixos.py    # mode « NixOS déjà installé » (sauvegarde /etc/nixos, pré-vérifs)
  hardware_detect.py   # détection GPU / CPU / VM / écrans / SMBus et référence de la RAM
  host_defaults.py / host_profile.py   # valeurs par défaut et profil d'hôte
  ui_helpers.py
  pages/
    welcome.py · disk.py · options.py · summary.py · progress.py   # pages GTK
  style.css
data/disko/
  simple-efi-swap-root.nix · simple-btrfs-subvolumes.nix   # layouts de référence
tests/
  test_tui.py          # python3 -m unittest discover -s iso/roudix-installer/tests
po/
  roudix-installer.pot       # modèle (généré, ne pas éditer à la main)
  fr.po es.po pt_BR.po ru.po zh_CN.po hi.po ar.po
```

## Fonctionnement

- **ISO** : wizard complet (Welcome → Disk → Options → Summary → Progress), partitionnement via disko, puis `nixos-install`.
  Lancé avec un écran, c'est le wizard graphique ; sans écran (TTY, SSH) c'est le wizard terminal.
- **NixOS déjà installé** (`nix run "github:RoudineBWT/Roudix?dir=iso/roudix-installer"`) : pas de page disque, config clonée dans `~/.config/roudix`, appliquée avec `nixos-rebuild boot` ; `/etc/nixos` est sauvegardé dans `/var/backups/roudix/` avec un `RESTORE.txt`.
- **Sans les fonctionnalités expérimentales de Nix** (`experimental Nix feature 'nix-command' is disabled`) : `nix --extra-experimental-features 'nix-command flakes' run "github:RoudineBWT/Roudix?dir=iso/roudix-installer"` (branche par défaut, pas de `ref=`) ; ajoutez `-- --tui` pour la version terminal.
- Bouton *Simuler* sur la page de résumé : génère la config dans un dossier temporaire et fait évaluer le système par Nix, sans rien modifier.
- Voir [Installation](../../docs/installation.fr.md) pour le détail côté utilisateur.

## Wizard terminal (TUI)

```bash
roudix-installer              # GUI si un écran est disponible, sinon TUI
roudix-installer --tui        # force le terminal (remplace roudix-installer.sh)
roudix-installer --gui        # force le graphique
roudix-installer --dry-run    # génère et vérifie la config, ne touche à rien (GUI comme TUI)
roudix-installer --lang fr    # saute la question de la langue
ROUDIX_INSTALLER_UI=tui       # idem --tui, pour un script / une unité systemd
```

Mêmes écrans que la GUI : langue → profil → disque (ISO) → utilisateur → options → résumé →
installation. Entrée garde la valeur par défaut `[entre crochets]`, un numéro choisit dans une
liste, du texte filtre une longue liste (fuseaux, locales…), les options oui/non regroupées
(jeux, apps, plugins OBS…) sont des listes à cocher. Après le résumé, *Modifier les options* repasse
sur toutes les questions avec tes réponses comme valeurs par défaut. Ctrl-C / Ctrl-D quittent sans rien
modifier tant que l'installation n'a pas démarré.

Particularités :

- **Sans dépendance** : bibliothèque standard seulement. Sur la console Linux (`TERM=linux`) seules les langues
  en alphabet latin sont proposées (le noyau ne sait pas dessiner le reste) et les symboles ✓ ⚠ → deviennent `[ok]` `[!]` `->`.
- **NixOS déjà installé** : `sudo -v` est demandé une fois au début, puis l'installation tourne sans
  interruption (pas de polkit dans un terminal).
- **Autres systèmes (multi-boot)** : si le bootloader est Limine en UEFI, `efibootmgr -v` liste les autres
  systèmes du menu firmware et tu choisis lesquels ajouter. Ils sont écrits dans
  `modules/system/boot/boot.local.nix` (ce que faisait l'ancien script). Même choix dans la GUI : interrupteurs sous l'option Bootloader.
- **Texte libre** (SMBus, SKU, intervalle…) : refusé s'il contient `"` `'` `$` `{` `}` `\` ou un retour à
  la ligne, car il est écrit tel quel dans une chaîne Nix de `local.nix`.

> Quand tu ajoutes ou changes une option : la liste des choix va dans `choices.py` (partagée), la question
> dans `questions.py` (TUI) **et** la ligne correspondante dans `pages/options.py` (GTK) tant que la page GTK
> n'est pas reconstruite à partir de `questions.py`. `tests/test_tui.py` vérifie que chaque option de
> `host_defaults.py` a bien une question.

## Tester en local (hors ISO)

```bash
nix develop   # ou nix run .# une fois le flake complet
python3 -m unittest discover -s iso/roudix-installer/tests -v   # TUI, questions, multiboot, runner (sans GTK, sans root)
python3 -m roudix_installer.main --tui --dry-run                 # parcours complet sans rien écrire
```

Attention : `runner.py` appelle réellement `disko` et `nixos-install` —
à tester en VM, pas sur ta machine principale (ou avec `--dry-run`).

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
