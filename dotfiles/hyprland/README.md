# Roudix Hyprland

Configuration Hyprland Lua modulaire pour Roudix (Hyprland 0.55+).

## Structure

- `hyprland.lua` — point d'entrée.
- `config/colors.lua` — palette Roudix.
- `config/defaults.lua` — applications par défaut et écran principal.
- `config/monitors.lua` — sorties et modes des moniteurs.
- `config/workspaces.lua` — workspaces nommés et affectation aux écrans.
- `config/layout.lua` / `animations.lua` / `decorations.lua` / `misc.lua` — comportement et apparence.
- `config/binds/common.lua` — raccourcis communs.
- `config/shell.lua` + `config/shells/` — intégration Noctalia, DMS et Caelestia.
- `config/rules/` — règles communes, applications et gaming.
- `config/autostart.lua` — environnement de session et démarrage optionnel de Discord.
- `scripts/gamemode.sh` — bascule du mode jeu.

## Shell

Le shell est choisi par `roudix.desktop.shell` dans `hosts/roudix/local.nix`.

La valeur est exposée à Hyprland via `ROUDIX_HYPR_SHELL` :

```nix
roudix.desktop.shell = "noctalia"; # noctalia | dms | caelestia
```

Le shell est géré par les intégrations systemd/Nix correspondantes ; `config/autostart.lua` ne relance donc pas le shell.

## Plugins

`borders-plus-plus` est fourni par Nix et chargé au début de `hyprland.lua` via `config/nix-plugins.lua`, généré par le module Hyprland. Les réglages du plugin sont dans `config/decorations.lua`.

`dynamic_cursors` est protégé par un test : la configuration reste valide si le plugin n'est pas installé.

## Personnalisation

Les fichiers sont copiés tels quels vers `~/.config/hypr/` par le module Home Manager. Les valeurs les plus susceptibles d'être adaptées à une machine sont :

- `config/monitors.lua`
- `config/defaults.lua`
- `config/input.lua`
- `config/workspaces.lua`

Après modification :

```bash
rebuild
```

Un redémarrage de session peut être nécessaire après un changement de shell ou d'environnement.
## Shell autostart

The shell selected by `roudix.desktop.shell` is started once by Hyprland:

- `noctalia` → `noctalia`
- `dms` → service systemd utilisateur DMS (pas de `dms run` dans Hyprland)
- `caelestia` → `caelestia-shell`

Home Manager systemd startup for these shells is disabled in the Hyprland module, so there is no second shell instance. MangoWC follows the same model for Noctalia and DMS through `autostart_sh`.

