*[English version](desktop.md)*

# Environnements de bureau

Changez de bureau à tout moment avec `roudix-switch <de>` ou via l'interface **Roudix Settings** (paquet `roudix-switcher`) — pas besoin d'un hôte séparé. L'interface a évolué au-delà du simple changement de bureau : elle couvre désormais Bureau, Gaming (bascules par application), Éditeur, Terminal, Navigateur, Shell de connexion, Gestionnaire de fichiers, Client de chat (Discord/Matrix) et Intégration (stack keyring/portal) dans une seule application.

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

Pour les compositeurs Wayland (Niri, Hyprland, MangoWC), vous pouvez changer la stack shell/barre indépendamment du compositeur. Chaque shell a son propre dossier de dotfiles.

| Valeur | Shell | Dossiers de dotfiles |
|-------|-------|-----------------|
| `noctalia` | Noctalia | `dotfiles/niri/` · `dotfiles/hyprland/` · `dotfiles/mangowc/` |
| `dms` | DankMaterialShell | `dotfiles/niri-dms/` · `dotfiles/hyprland-dms/` · `dotfiles/mangowc-dms/` |
| `caelestia` | Caelestia | `dotfiles/hyprland-caelestia/` |

**Note :** caelestia n'est disponible que sur Hyprland. Umbriel n'apparaît pas dans ce tableau — c'est le compositeur propre à Noctalia et il ne supporte pas le changement de shell.

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

> **Note :** Si le dossier de dotfiles spécifique au shell n'existe pas encore dans le dépôt, Nix retombe automatiquement sur le dossier Noctalia pour que le build ne casse jamais.

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

**Hyprland fonctionne différemment.** Comme le langage de config d'Hyprland change trop souvent (`.conf` → `.lua` → allez savoir la suite), Nix ne génère plus aucun fichier d'entrée pour lui. Tout le dossier de dotfiles est copié tel quel — vous gérez le format vous-même. Mettez le `hyprland.conf`, `hyprland.lua`, ou tout autre point d'entrée que vous voulez directement dans `dotfiles/hyprland/cfg/` (ou `dotfiles/hyprland-dms/cfg/`, etc.) et Hyprland le prendra en compte.

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

> `lib.mkForce` est nécessaire pour surcharger les valeurs par défaut définies dans `home/kde.nix`.
