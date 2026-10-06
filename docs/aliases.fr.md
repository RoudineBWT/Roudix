*[English version](aliases.md)*

# Alias & fonctions

## Disponibles partout

| Alias | Action |
|-------|--------|
| `rebuild` | Applique la configuration immédiatement |
| `update` | Pull la config, rebuild + switch, met à jour les Flatpaks (voir [ci-dessous](#update)) |
| `cleanup` | Supprime les anciennes générations + garbage collect |
| `noctalia-reload` | Redémarre Noctalia sans se déconnecter |
| `dms-reload` | Redémarre Quickshell sans se déconnecter |
| `caelista-reload` | Redémarre Quickshell sans se déconnecter |
| `roudix-switch <de>` | Change d'environnement de bureau (s'applique au prochain redémarrage) |
| `roudix-kernel-switch <kernel>` | Change de variante de kernel (s'applique au prochain redémarrage) |

### `update`

Équivalent manuel de l'[auto-update](autoupdate.fr.md) : même dépôt, même branche suivie, même règle fast-forward uniquement (tes commits locaux ne sont jamais touchés). Il tourne avec ton utilisateur normal et n'utilise `sudo` que là où c'est nécessaire.

1. `git pull --ff-only` de la branche suivie (ignoré si tu es sur une autre branche, par ex. une branche de feature)
2. `nh os switch` (ou `nh os boot` avec `--boot`)
3. Mise à jour des Flatpaks, utilisateur et système (jamais bloquant)

Le `flake.lock` récupéré via git est celui que la CI a déjà buildé et validé : un simple `update` ne met donc **pas** à jour les entrées de la flake.

| Option | Effet |
|--------|-------|
| `-i`, `--inputs [nom…]` | Met aussi à jour les entrées de la flake en local (toutes, ou seulement celles nommées). Si le build échoue, `flake.lock` est restauré |
| `-b`, `--boot` | Applique au prochain démarrage au lieu de switcher maintenant |
| `-c`, `--check` | Indique seulement si de nouveaux commits sont disponibles |
| `--no-inputs` | Saute le bump des entrées (utile avec `roudix.update.bumpInputs = true`) |
| `--no-pull` / `--no-flatpak` | Saute le pull / la mise à jour Flatpak |

```fish
update                    # pull + rebuild + switch
update --inputs           # met à jour toutes les entrées, puis rebuild
update --inputs nixpkgs   # met à jour uniquement nixpkgs
```

Sur une machine qui suit `dev` et veut toujours des entrées fraîches, mets `roudix.update.bumpInputs = true;` dans `local.nix` : un simple `update` se comporte alors comme `update --inputs`.

> Après `update --inputs`, `flake.lock` est une modification locale : commit et push-le (ou `git checkout flake.lock`), sinon le prochain pull de l'auto-update peut refuser de tourner si la CI a touché le lock entre-temps.

## Niri, Hyprland & MangoWC uniquement

| Alias | Action |
|-------|--------|
| `roudix-shell-switch <shell>` | Change de shell graphique (s'applique au prochain redémarrage) |

### Utilisation

```fish
# Changer d'environnement de bureau
roudix-switch niri
roudix-switch hyprland
roudix-switch mangowc
roudix-switch umbriel
roudix-switch gnome
roudix-switch kde

# Changer de variante de kernel — la liste dépend de hardware.myGpu, voir docs/installation.fr.md
# AMD/Intel (xddxdd) :
roudix-kernel-switch cachyos-latest-v3
roudix-kernel-switch cachyos-lts-lto-v3
roudix-kernel-switch cachyos-bore
# Nvidia (Chaotic-Nyx — jeu plus restreint, nécessaire pour le cache binaire nvidia_cachyos) :
roudix-kernel-switch cachyos
roudix-kernel-switch cachyos-lts
# Kernels nixpkgs bruts — disponibles sur les deux chemins GPU, en dehors de l'overlay CachyOS
# (sur Nvidia, ceux-ci retombent sur un module Nvidia recompilé localement, pas de cache nvidia_cachyos) :
roudix-kernel-switch zen
roudix-kernel-switch nixpkgs-lts
roudix-kernel-switch nixpkgs-latest
roudix-kernel-switch nixpkgs-testing

# Changer de shell graphique (Niri, Hyprland & MangoWC uniquement)
roudix-shell-switch noctalia
roudix-shell-switch dms
roudix-shell-switch caelestia # uniquement pour hyprland
```

Les trois commandes modifient automatiquement `hosts/roudix/local.nix` et lancent `nh os boot` — aucun rebuild manuel nécessaire. Les changements s'appliquent au prochain redémarrage.

> **Note :** `roudix-kernel-switch` écrit automatiquement dans `hardware.myKernel` ou `hardware.myKernelChaotic` selon votre `hardware.myGpu` actuel — passez le nom de la variante correspondant à la liste de votre GPU (voir tableau ci-dessus).
