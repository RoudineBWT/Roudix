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
- [ ] i18n propre (tout est en dur en français pour l'instant)
- [ ] Packaging dans l'ISO : ajouter `roudix-installer` aux paquets du live env
      et un raccourci bureau/autostart à la place de Calamares

## Tester en local (hors ISO)

```bash
nix develop   # ou nix run .# une fois le flake complet
```

Attention : `progress.py` appelle réellement `disko` et `nixos-install` —
à tester en VM, pas sur ta machine principale.
