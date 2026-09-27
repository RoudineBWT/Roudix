*[English version](desktop.md)*

# Environnements de bureau

Changez de bureau à tout moment avec `roudix-switch <de>` ou via l'interface **Roudix Customizer** (paquet `roudix-switcher`) — pas besoin d'un hôte séparé. L'interface a évolué au-delà du simple changement de bureau : elle couvre désormais Bureau, Gaming (bascules par application), Éditeur, Terminal, Navigateur, Shell de connexion, Gestionnaire de fichiers, Client de chat (Discord/Matrix) et Intégration (stack keyring/portal) dans une seule application.

| Valeur | Bureau | Notes |
|-------|---------|-------|
| `niri` | Niri + (Noctalia, DMS) | Par défaut — tiling scrollable Wayland |
| `hyprland` | Hyprland + (Noctalia, DMS, Caelestia) | Tiling dynamique Wayland — lancé via UWSM |
| `mangowc` | MangoWC + (Noctalia, DMS) | Compositeur Wayland |
| `umbriel` | Umbriel + Noctalia | Tiling scrollable — le compositeur natif propre à Noctalia, Noctalia uniquement (pas de changement de shell) |
| `gnome` | GNOME 49.5 | |
| `kde` | KDE Plasma 6 | plasma-login-manager, KDE Connect |

Pour changer de façon permanente, modifiez `hosts/roudix/local.nix` :

```nix
roudix.desktop.type = "niri"; # "niri", "hyprland", "mangowc", "gnome" ou "kde"
```

Ou utilisez la fonction fish — elle modifie la config et rebuild en une seule étape :

```fish
roudix-switch kde
```

> **Note :** `roudix-switch` utilise `nh os boot` — les changements s'appliquent au prochain redémarrage.

---

## Shells graphiques (Niri, Hyprland & MangoWC uniquement)

Pour les compositeurs Wayland (Niri, Hyprland, MangoWC), vous pouvez changer la stack shell/barre indépendamment du compositeur. Pour Hyprland, **un seul arbre de configuration** (`dotfiles/hyprland/`) contient les binds communs et sélectionne le shell à partir de `roudix.desktop.shell`.

| Valeur | Shell | Hyprland |
|-------|-------|----------|
| `noctalia` | Noctalia | `dotfiles/hyprland/` |
| `dms` | DankMaterialShell | `dotfiles/hyprland/` |
| `caelestia` | Caelestia | `dotfiles/hyprland/` |

**Note :** Caelestia n'est disponible que sur Hyprland. Le shell est injecté dans la session via `ROUDIX_HYPR_SHELL`, donc il n'y a pas de copie séparée `hyprland-dms/` ou `hyprland-caelestia/` à maintenir.

### Démarrage automatique du shell

Le démarrage dépend du shell et du compositeur, avec une seule méthode active par shell :

- **Hyprland + Noctalia :** `noctalia` depuis le hook Lua `hyprland.start`.
- **Hyprland + Caelestia :** `caelestia-shell` depuis le hook Lua `hyprland.start`.
- **Hyprland + DMS :** service systemd utilisateur DMS ; Hyprland exporte l’environnement vers systemd au démarrage.
- **MangoWC + Noctalia :** `noctalia` depuis `autostart_sh`.
- **MangoWC + DMS :** service systemd utilisateur DMS, démarré via `mango-session.target` ; MangoWC n’exécute donc pas `dms run`.

DMS ne doit pas être lancé à la fois par systemd et par le compositor : sa documentation officielle recommande de supprimer `dms run` lorsqu’on utilise le service systemd. citeturn1search0turn1search2


Pour changer, modifiez `hosts/roudix/local.nix` :

```nix
roudix.desktop.shell = "noctalia"; # "noctalia", "dms" ou "caelestia"
```

Puis rebuild :

```fish
rebuild
```

Ou utilisez la fonction fish (disponible sur Niri, Hyprland & MangoWC uniquement) — elle modifie la config et rebuild en une seule étape :

```fish
roudix-shell-switch dms
```

> **Note :** `roudix-shell-switch` utilise `nh os boot` — les changements s'appliquent au prochain redémarrage.

---

## Surcharges personnelles du compositeur

Niri et Umbriel sont configurés nativement en Nix (`programs.niri.settings` / `programs.umbriel.settings`) — de vrais attrsets typés, pas un fichier texte généré. Cela veut dire que les surcharges sont juste du Nix : ajouter une clé qui n'existe pas encore se fusionne automatiquement ; toucher une clé déjà définie par le dépôt (même sortie, même raccourci) nécessite `lib.mkForce`, sinon Nix refusera de build avec une erreur de « définitions conflictuelles ».

MangoWC et Hyprland restent basés sur du texte (voir ci-dessous).

Vous pouvez mettre les surcharges directement dans `home/local.nix`, mais si vous personnalisez beaucoup un compositeur, un fichier dédié garde les choses plus propres — `home/local.nix` importe automatiquement `home/niri-custom.nix`, `home/umbriel-custom.nix` et `home/mango-custom.nix` s'ils existent (copiez le fichier `*.example` correspondant pour démarrer ; ils sont ignorés par git comme `local.nix`).

**Niri**

```nix
# Changer un écran déjà défini par niri-flake (nécessite lib.mkForce)
# — lancez `niri msg outputs` en session pour le vrai nom du connecteur
programs.niri.settings.outputs."Lenovo Group Limited Legion 27Q-10 UNA07260".mode =
  lib.mkForce { width = 3840; height = 2160; refresh = 144.0; };

# Remapper un raccourci déjà défini par le dépôt (nécessite lib.mkForce)
programs.niri.settings.binds."Mod+T" = lib.mkForce {
  action.spawn = [ "alacritty" ];
};

# Ajouter un raccourci qui n'existe pas encore (pas besoin de mkForce)
programs.niri.settings.binds."Mod+Shift+V".action.spawn = [ "pavucontrol" ];

# Ajouter une règle de fenêtre — les listes se CONCATÈNENT entre fichiers, donc ceci
# s'ajoute simplement aux règles du dépôt, pas besoin de mkForce
programs.niri.settings.window-rules = [
  { matches = [ { app-id = "mpv"; } ]; open-floating = true; }
];
```

**Umbriel**

```nix
# Changer une sortie (nécessite lib.mkForce — lancez `umbriel outputs` pour le vrai nom)
programs.umbriel.settings.output."DP-1".mode = lib.mkForce "3840x2160@144";

# Remapper un raccourci déjà défini par le dépôt
programs.umbriel.settings.keybinds."Mod+C" = lib.mkForce "spawn:some-command";

# Ajouter un raccourci qui n'existe pas encore
programs.umbriel.settings.keybinds."Mod+Shift+V" = "spawn:pavucontrol";

# Ajouter une règle de fenêtre
programs.umbriel.settings.window_rule = [
  { match.app_id = "^mpv$"; default_floating = true; }
];
```

**MangoWC** utilise toujours un fichier de surcharge personnel généré par home-manager, tout à la fin de sa config — **jamais touché par `git pull`** — car il n'a pas de schéma Nix typé en pratique :

- MangoWC → `~/.config/mango/user.conf`

```nix
xdg.configFile."mango/user.conf".text = lib.mkForce ''
  monitorrule=name:DP-1,width:2560,height:1440,refresh:144,x:0,y:0,scale:1,vrr:1,rr:0,tearing:1
'';
```

Comme c'est un gros bloc de texte plutôt que quelques lignes Nix, ça a plus sa place dans son propre fichier — voir `home/mango-custom.nix.example`.

**Hyprland utilise maintenant une configuration Lua modulaire fournie dans `dotfiles/hyprland/`.** Le fichier d'entrée est `dotfiles/hyprland/hyprland.lua`, qui charge les modules `config/` pour les écrans, layouts, animations, binds, règles de fenêtres et intégrations shell. Nix copie cet arbre tel quel dans `~/.config/hypr/`.

La configuration actuelle cible Hyprland 0.55+ et utilise les layouts natifs `dwindle`, `master` et `scrolling`. Le module Nix génère un petit chargeur `config/nix-plugins.lua` avant le point d'entrée ; `borders-plus-plus` est inclus dans la configuration Roudix. Le bloc `dynamic_cursors` reste optionnel et ne s'applique que si le plugin est présent.

### Personnaliser Hyprland

Les valeurs propres à la machine (sorties `DP-1`/`DP-3`, écran principal, applications par défaut, clavier, etc.) se trouvent dans `dotfiles/hyprland/config/`. Modifiez-les directement si vous versionnez votre configuration avec Roudix.

Pour une surcharge personnelle sans modifier les fichiers suivis par git, utilisez `home/local.nix` avec `xdg.configFile."hypr/..."` et `lib.mkForce`.

> Après une modification de la configuration Lua, utilisez `rebuild`. Un redémarrage de session peut être nécessaire pour les changements de shell ou d'environnement.

> Voir `home/niri-custom.nix.example`, `home/umbriel-custom.nix.example`, `home/mango-custom.nix.example` et `home/local.nix.example` pour la liste complète des exemples.

---

## Surcharges GNOME

Avec `roudix.desktop.type = "gnome"`, la gestion des extensions se fait dans `hosts/roudix/local.nix` et les surcharges d'apparence dans `home/local.nix`.

**Ajouter des extensions en plus des extensions par défaut** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [
  pop-shell
];
```

**Désactiver une extension par défaut par UUID** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.disabledExtensions = [
  "arcmenu@arcmenu.com"
];
```

**Combiner les deux — par ex. remplacer ArcMenu par un autre lanceur** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [ pop-shell ];
roudix.gnome.disabledExtensions = [ "arcmenu@arcmenu.com" ];
```

**Fond d'écran** (`home/local.nix`)
```nix
dconf.settings."org/gnome/desktop/background".picture-uri =
  lib.mkForce "file:///home/youruser/Pictures/my-wallpaper.png";
dconf.settings."org/gnome/desktop/background".picture-uri-dark =
  lib.mkForce "file:///home/youruser/Pictures/my-wallpaper-dark.png";
```

**Mode clair/sombre** (`home/local.nix`)
```nix
dconf.settings."org/gnome/desktop/interface".color-scheme =
  lib.mkForce "prefer-light"; # ou "prefer-dark"
```

**Thème d'icônes** (`home/local.nix`)
```nix
dconf.settings."org/gnome/desktop/interface".icon-theme =
  lib.mkForce "Papirus";
# Autres valeurs : "Papirus-Dark", "Papirus-Light", "hicolor"
```

**Curseur** (`home/local.nix`)
```nix
dconf.settings."org/gnome/desktop/interface".cursor-theme =
  lib.mkForce "capitaine-cursors";
dconf.settings."org/gnome/desktop/interface".cursor-size =
  lib.mkForce 32;
```

> Voir `hosts/roudix/local.nix.example` et `home/local.nix.example` pour toutes les options de surcharge GNOME disponibles.

---

## Surcharges KDE Plasma

Avec `roudix.desktop.type = "kde"`, vous pouvez surcharger n'importe quel réglage plasma-manager dans `home/local.nix` :

**Fond d'écran**
```nix
programs.plasma.workspace.wallpaper = lib.mkForce "/home/youruser/Pictures/wallpaper.jpg";
```

**Thème d'icônes**
```nix
programs.plasma.workspace.iconTheme = lib.mkForce "Papirus-Dark";
# Autres valeurs : "Papirus", "Papirus-Light", "breeze-dark", "breeze"
```

**Jeu de couleurs / Look & Feel**
```nix
programs.plasma.workspace.colorScheme = lib.mkForce "BreezeDark";
programs.plasma.workspace.lookAndFeel = lib.mkForce "org.kde.breezedark.desktop";
```

**Barre des tâches / Panneaux**
```nix
programs.plasma.panels = lib.mkForce [
  {
    location = "bottom";
    widgets = [
      { kickoff.icon = "/path/to/your/icon.svg"; }
      "org.kde.plasma.icontasks"
      "org.kde.plasma.marginsseperator"
      "org.kde.plasma.systemtray"
      "org.kde.plasma.digitalclock"
      "org.kde.plasma.showdesktop"
    ];
  }
];
```

> `lib.mkForce` est nécessaire pour surcharger les valeurs par défaut définies dans `home/desktop/kde/default.nix`.
