*[English version](aliases.md)*

# Alias & fonctions

## Disponibles partout

| Alias | Action |
|-------|--------|
| `rebuild` | Applique la configuration immédiatement |
| `update` | Met à jour les entrées de la flake + applique |
| `cleanup` | Supprime les anciennes générations + garbage collect |
| `noctalia-reload` | Redémarre Noctalia sans se déconnecter |
| `dms-reload` | Redémarre Quickshell sans se déconnecter |
| `caelista-reload` | Redémarre Quickshell sans se déconnecter |
| `roudix-switch <de>` | Change d'environnement de bureau (s'applique au prochain redémarrage) |
| `roudix-kernel-switch <kernel>` | Change de variante de kernel (s'applique au prochain redémarrage) |

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
