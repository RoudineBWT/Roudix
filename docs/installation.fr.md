*[English version](installation.md)*

# Installation

Il y a trois façons de faire tourner Roudix, selon votre point de départ :

| Situation | Utiliser |
|-----------|-----|
| Machine vierge, rien d'installé | **ISO Roudix** — démarre directement sur un installeur graphique (partitionnement inclus) |
| NixOS déjà installé (ISO stock, install NixOS d'une autre distro, une VM…) | **`roudix-installer.sh`** — installe la flake Roudix sur votre install existante |
| Vous voulez le contrôle total sur chaque étape, ou le script ne couvre pas votre cas | **Installation manuelle** (ci-dessous) |

## Option A — ISO Roudix (recommandé pour une install neuve)

L'ISO embarque notre propre installeur graphique GTK4/libadwaita (`roudix-installer`) au-dessus d'une session GNOME live, et gère le partitionnement disque pour vous via [disko](https://github.com/nix-community/disko) — pas besoin d'installer NixOS au préalable.

1. Récupérez la dernière ISO : allez dans l'onglet **Actions** du dépôt → workflow **💿 Build Roudix ISO** → lancez-le (`workflow_dispatch`) si aucun build récent n'est listé, puis ouvrez le run et récupérez le lien de téléchargement posté dans le résumé du job (l'ISO est hébergée sur Cloudflare R2, pas comme artefact GitHub).
2. Flashez-la sur une clé USB (par ex. `dd`, Ventoy, Rufus…) et démarrez dessus.
3. La fenêtre de l'installeur s'ouvre automatiquement à la connexion (elle se relance elle-même avec `sudo` — la session live a besoin du root pour disko/`nixos-install`). Parcourez les pages : sélection du disque, kernel, bureau, navigateur, éditeur, Discord, applis gaming, locale, fuseau horaire, disposition clavier, contrôleur RGB, et modules optionnels.
4. À la confirmation, elle partitionne le disque (disko), copie la flake Roudix embarquée dans l'ISO vers `/mnt/etc/nixos`, et lance `nixos-install --flake /mnt/etc/nixos#roudix`.

> **Note :** le menu de boot propose aussi des spécialisations de disposition clavier (US/BE/FR/DE/CH/UK) si le clavier de votre session live ne correspond pas au vôtre — choisissez-en une avant de lancer l'installeur.

Ce chemin remplace entièrement les deux étapes ci-dessous (pas besoin de `roudix-installer.sh` ni des étapes manuelles) — passez directement à ce qui vient après l'installation une fois le redémarrage effectué.

## Option B — Vous avez déjà NixOS installé

Si NixOS est déjà installé (via l'ISO officielle stable/unstable, ou tout autre moyen) et que vous voulez juste installer Roudix par-dessus, utilisez plutôt le script d'installation bash :

> **Note :** installez d'abord NixOS avec l'ISO [stable](https://nixos.org/download/) ou [unstable](https://releases.nixos.org/nixos/unstable/nixos-26.05pre980183.4bd9165a9165), puis lancez le script ci-dessous ou suivez l'installation manuelle.

**Télécharger le script roudix-installer**

```bash
nix-shell -p wget --run "wget https://github.com/RoudineBWT/Roudix/raw/refs/heads/main/roudix-installer.sh"
chmod +x roudix-installer.sh
./roudix-installer.sh
```

L'installeur gère tout de façon interactive :
- Demande quelle branche installer et suivre (`main` = stable, `testing`, `dev`), la clone, génère `hardware-configuration.nix`, crée tous les fichiers de config locaux
- **Détecte automatiquement les autres OS** via la NVRAM EFI (`efibootmgr`) — pas besoin de chercher le PARTUUID manuellement
- **Détecte automatiquement le GPU et le CPU** (`lspci` / `/proc/cpuinfo`) — présélectionne et demande confirmation
- **Détecte si vous êtes dans une VM** (`systemd-detect-virt`) — active en avance le mode invité VM et prévient que la détection GPU/CPU peut être imprécise
- Pose des questions sur le kernel, le bureau, le navigateur, l'éditeur, Discord, les applis gaming, la locale, le fuseau horaire, la disposition clavier, le contrôleur RGB, et les modules optionnels
- Build et applique la configuration

---

## Option C — Installation manuelle

> ⚠️ **Suivez chaque étape avec attention avant de rebuild.**

### 1. Cloner le dépôt

> **Si `git` n'est pas installé** (install NixOS neuve) :

```bash
nix-shell -p git --run "git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix"
```

> **Sinon :**

```bash
git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix
cd ~/.config/roudix
```

### 2. Définir votre nom d'utilisateur

Créez le fichier `username.nix` avec votre nom d'utilisateur :

```bash
echo '"yourusername"' > ~/.config/roudix/hosts/roudix/username.nix
```

> Ce fichier est ignoré par git — il ne sera jamais écrasé par un `git pull`.

### 3. Remplacer hardware-configuration.nix

```bash
sudo cp /etc/nixos/hardware-configuration.nix ~/.config/roudix/hosts/roudix/hardware-configuration.nix
```

### 4. Créer vos configs locales

**Ne modifiez jamais `configuration.nix` ou `home/common.nix` directement** — ils sont écrasés à chaque `git pull`.
Créez plutôt vos fichiers de surcharge locaux (tous ignorés par git) :

```bash
cp hosts/roudix/local.nix.example hosts/roudix/local.nix
cp home/local.nix.example home/local.nix
cp modules/system/boot/boot.local.nix.example modules/system/boot/boot.local.nix
```

Modifiez `hosts/roudix/local.nix` pour correspondre à votre matériel :

```nix
{ lib, ... }:
{
  roudix.desktop.type = "niri";               # "niri", "hyprland", "mangowc", "umbriel", "gnome" ou "kde"
  hardware.myGpu      = "amd";                # "amd", "nvidia" ou "intel"
  hardware.myCpu      = "intel";              # "intel" ou "amd"
  hardware.myKernel        = "cachyos-lts-lto-v3"; # kernel xddxdd — utilisé quand hardware.myGpu != "nvidia"
  hardware.myKernelChaotic = "cachyos";            # kernel Chaotic-Nyx — utilisé uniquement quand hardware.myGpu == "nvidia"
  roudix.boot.bootloader = "limine";          # "limine" ou "systemd-boot"
  roudix.browsers     = [ "helium" ];         # "brave", "helium", "vivaldi", "firefox", "librewolf", "chromium" ou []
  roudix.zen.enable   = false;                # mettre à true pour aussi installer Zen Browser (Twilight)
  roudix.rgb          = "openlinkhub";        # "openlinkhub", "openrgb" ou "none" — voir ci-dessous
  roudix.mesa.useGit  = false;                # true = mesa-git (expérimental, le build peut échouer), false = nixpkgs stable
  roudix.matrixClient = "none";               # "element", "cinny" ou "none"
  roudix.discord      = "vencord";            # "vencord", "vanilla" ou "none"
  roudix.editor       = "zed";                # "zed", "vscode", "neovim" ou "none"

  # ── Applis gaming (toutes true par défaut — désactivez ce que vous ne voulez pas) ────────
  # roudix.gaming.apps.lutris.enable        = false;
  # roudix.gaming.apps.heroic.enable        = false;
  # roudix.gaming.apps.faugus.enable        = false;
  # roudix.gaming.apps.prismlauncher.enable = false;
  # roudix.gaming.apps.vintagestory.enable  = false;
  # roudix.gaming.apps.mangohud.enable      = false;

  # ── Intégration compositeur nu (niri/hyprland/mangowc/umbriel uniquement) ───────
  roudix.desktopIntegration = "gnome";        # "gnome" ou "kde" — stack keyring + xdg-desktop-portal ; aucun effet sur les sessions gnome/kde

  # ── Locale / Fuseau horaire ───────────────────────────────────────────────────────
  time.timeZone                   = "Europe/Brussels"; # voir https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
  environment.sessionVariables.TZ = "Europe/Brussels"; # doit correspondre à time.timeZone
  i18n.defaultLocale              = "en_US.UTF-8";     # locale système
  console.keyMap                  = "us";              # disposition clavier console — TTY uniquement, avant le démarrage de la session graphique

  # ── Disposition clavier graphique (Wayland) — indépendante de console.keyMap ─
  # Aucun effet sur GNOME/KDE, qui gèrent leur propre disposition via leur démon de réglages.
  roudix.keyboardLayout  = "us";              # "us", "be", "fr", "de", "ch", "nl", "es", "it", "pt", "pl", "ru", "gb", "jp"...
  roudix.keyboardVariant = "intl";            # "intl", "nodeadkeys", "bepo", "dvorak", "colemak", "" (aucun)
}
```

**Options du contrôleur RGB :**

| Valeur | Description |
|-------|-------------|
| `openlinkhub` | OpenLinkHub — setup Corsair complet (iCUE Link, Commander...) |
| `openrgb` | OpenRGB — marques mixtes (Razer, ASUS, MSI...) |
| `none` | Pas de gestion RGB |

**RGB RAM (OpenLinkHub uniquement) :**

Si vous avez choisi `openlinkhub`, vous pouvez aussi activer le contrôle RGB pour votre RAM Corsair DDR4/DDR5. Ajoutez ces lignes à `hosts/roudix/local.nix` :

```nix
roudix.memory.enable = true;                  # active le RGB RAM via SMBus
roudix.memory.type   = "ddr5";                # "ddr4" ou "ddr5"
roudix.memory.smBus  = "i2c-9";              # trouvez avec : sudo i2cdetect -l (cherchez "SMBus")
roudix.memory.sku    = "CMH64GX5M2B5200C40"; # trouvez avec : sudo dmidecode -t memory | grep 'Part Number'
```

Pour trouver les bonnes valeurs avant de les définir :

```bash
# Installez les outils requis s'ils ne sont pas disponibles (install NixOS neuve)
nix-env -iA nixos.i2c-tools
nix-env -iA nixos.dmidecode

# Trouvez votre SMBus (cherchez une ligne avec "SMBus", "i801", "piix4" ou "nforce")
sudo i2cdetect -l

# Trouvez le numéro de pièce de votre RAM
sudo dmidecode -t memory | grep 'Part Number'
```

> **Note :** `roudix.memory.enable` applique automatiquement `acpi_enforce_resources=lax` comme paramètre kernel et blackliste `spd5118` (DDR5) ou `ee1004` (DDR4) pour libérer le SMBus. Le `config.json` d'OpenLinkHub est patché automatiquement à l'activation.

**Valeurs de fuseau horaire courantes :**

| Fuseau horaire | Région |
|----------|--------|
| `Europe/Brussels` | Belgique |
| `Europe/Paris` | France |
| `Europe/London` | Royaume-Uni |
| `Europe/Berlin` | Allemagne |
| `Europe/Amsterdam` | Pays-Bas |
| `America/New_York` | USA Est |
| `America/Los_Angeles` | USA Ouest |
| `Asia/Tokyo` | Japon |
| `UTC` | Universel |

**Valeurs de locale courantes :**

| Locale | Langue |
|--------|----------|
| `en_US.UTF-8` | Anglais (US) |
| `en_GB.UTF-8` | Anglais (UK) |
| `fr_BE.UTF-8` | Français (Belgique) |
| `fr_FR.UTF-8` | Français (France) |
| `de_DE.UTF-8` | Allemand |
| `nl_BE.UTF-8` | Néerlandais (Belgique) |
| `nl_NL.UTF-8` | Néerlandais |
| `es_ES.UTF-8` | Espagnol |
| `pt_BR.UTF-8` | Portugais (Brésil) |
| `it_IT.UTF-8` | Italien |
| `ru_RU.UTF-8` | Russe |
| `ja_JP.UTF-8` | Japonais |
| `zh_CN.UTF-8` | Chinois (simplifié) |
| `ko_KR.UTF-8` | Coréen |

**Valeurs de keymap console courantes :**

| Keymap | Disposition |
|--------|--------|
| `us` | Anglais (US) QWERTY |
| `us-acentos` | Anglais (US) International |
| `uk` | Anglais (UK) QWERTY |
| `be-latin1` | Belge AZERTY |
| `fr` | Français AZERTY |
| `de` | Allemand QWERTZ |
| `nl` | Néerlandais QWERTY |
| `es` | Espagnol QWERTY |
| `dvorak` | Dvorak (US) |
| `colemak` | Colemak |

> **Note :** `environment.sessionVariables.TZ` doit toujours correspondre à `time.timeZone` — ils contrôlent tous les deux le fuseau horaire, l'un au niveau système et l'autre au niveau session.

Modifiez `home/local.nix` pour vos surcharges home-manager personnelles (paquets supplémentaires, dotfiles, alias, fastfetch...) :

```nix
{ pkgs, lib, osConfig, ... }:
{
  # home.packages = with pkgs; [ vlc telegram-desktop ];
}
```

> Voir `home/local.nix.example` pour toutes les options de surcharge disponibles, y compris la personnalisation de fastfetch.

### 5. Configurer le kernel

Roudix utilise **deux fournisseurs de kernel différents** selon votre GPU :

- **`hardware.myGpu != "nvidia"`** (AMD ou Intel) → kernel de [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel), choisi via `hardware.myKernel`. Pas de module Nvidia à gérer, donc les 32 variantes sont toutes disponibles.
- **`hardware.myGpu == "nvidia"`** → kernel de **Chaotic-Nyx**, choisi via `hardware.myKernelChaotic`. C'est nécessaire pour obtenir **`nvidia_cachyos`**, un pilote Nvidia précompilé assorti à leur kernel — sinon le module kernel Nvidia se recompile localement à chaque bump de kernel. Le jeu de variantes est volontairement plus restreint ici (Chaotic-Nyx ne publie pas autant de saveurs, et les variantes `-lto` sont plus sujettes à casser des modules hors arbre comme celui de Nvidia).

Les deux options acceptent aussi quelques **kernels nixpkgs bruts**, entièrement en dehors de leur overlay CachyOS respectif — utile si vous voulez juste un kernel stock sans aucun patch CachyOS : `zen`, `nixpkgs-lts`, `nixpkgs-latest`, `nixpkgs-testing`. Sur le chemin Nvidia, ceux-ci évitent le cache `nvidia_cachyos` et recompilent le module Nvidia localement à la place (voir `nvidia.nix`).

**Variantes de `hardware.myKernel` (xddxdd — AMD/Intel uniquement) :**

| Variante | Description |
|---------|-------------|
| `zen` | `linuxPackages_zen` brut (nixpkgs) — en dehors de l'overlay xddxdd |
| `nixpkgs-lts` | Kernel LTS par défaut de nixpkgs brut — en dehors de l'overlay xddxdd |
| `nixpkgs-latest` | Dernier kernel mainline de nixpkgs brut — en dehors de l'overlay xddxdd |
| `nixpkgs-testing` | `linux_testing` de nixpkgs brut (candidat RC/mainline) — en dehors de l'overlay xddxdd |
| `cachyos-latest` | Dernier kernel CachyOS standard |
| `cachyos-latest-v2` | Optimisé x86_64-v2 |
| `cachyos-latest-v3` | Optimisé x86_64-v3 (recommandé pour les CPU modernes) |
| `cachyos-latest-v4` | Optimisé x86_64-v4 (AVX-512, CPU très récents uniquement) |
| `cachyos-latest-zen4` | Optimisé AMD Zen 4 |
| `cachyos-latest-lto` | Build LTO pour de meilleures performances |
| `cachyos-latest-lto-v2` | LTO + x86_64-v2 |
| `cachyos-latest-lto-v3` | LTO + x86_64-v3 (meilleures performances, CPU modernes uniquement) |
| `cachyos-latest-lto-v4` | LTO + x86_64-v4 (AVX-512) |
| `cachyos-latest-lto-zen4` | LTO + AMD Zen 4 |
| `cachyos-lts` | Kernel CachyOS à support long terme |
| `cachyos-lts-v2` | LTS + x86_64-v2 |
| `cachyos-lts-v3` | LTS + x86_64-v3 optimisé |
| `cachyos-lts-v4` | LTS + x86_64-v4 (AVX-512) |
| `cachyos-lts-zen4` | LTS + AMD Zen 4 |
| `cachyos-lts-lto` | LTS + LTO |
| `cachyos-lts-lto-v2` | LTS + LTO + x86_64-v2 |
| `cachyos-lts-lto-v3` | LTS + LTO + x86_64-v3 (stabilité + performance) |
| `cachyos-lts-lto-v4` | LTS + LTO + x86_64-v4 (AVX-512) |
| `cachyos-lts-lto-zen4` | LTS + LTO + AMD Zen 4 |
| `cachyos-bmq` | Scheduler BMQ |
| `cachyos-bmq-lto` | Scheduler BMQ + LTO |
| `cachyos-bore` | Scheduler BORE (meilleure interactivité) |
| `cachyos-bore-lto` | Scheduler BORE + LTO |
| `cachyos-deckify` | Optimisé Steam Deck |
| `cachyos-deckify-lto` | Optimisé Steam Deck + LTO |
| `cachyos-eevdf` | Scheduler EEVDF |
| `cachyos-eevdf-lto` | Scheduler EEVDF + LTO |
| `cachyos-hardened` | Kernel durci pour la sécurité |
| `cachyos-hardened-lto` | Durci pour la sécurité + LTO |
| `cachyos-rc` | Release candidate — bleeding edge, potentiellement instable |
| `cachyos-rc-lto` | Release candidate + LTO |
| `cachyos-rt-bore` | Temps réel + scheduler BORE |
| `cachyos-rt-bore-lto` | Temps réel + BORE + LTO |
| `cachyos-server` | Optimisé serveur (pas de tuning desktop) |
| `cachyos-server-lto` | Optimisé serveur + LTO |

**Variantes de `hardware.myKernelChaotic` (Chaotic-Nyx — Nvidia uniquement) :**

| Variante | Description |
|---------|-------------|
| `cachyos` | Par défaut — LTO + scheduler BORE, livré avec le `nvidia_cachyos` assorti |
| `cachyos-lts` | Support long terme |
| `cachyos-server` | Optimisé serveur (pas de tuning desktop) |
| `cachyos-hardened` | Durci pour la sécurité |
| `zen` | `linuxPackages_zen` brut (nixpkgs) — module Nvidia recompilé localement |
| `nixpkgs-lts` | LTS nixpkgs brut — module Nvidia recompilé localement |
| `nixpkgs-latest` | Dernier mainline nixpkgs brut — module Nvidia recompilé localement |
| `nixpkgs-testing` | `linux_testing` nixpkgs brut (RC) — module Nvidia recompilé localement |

> **Note NVIDIA :** Seules les séries GTX 20xx / RTX et plus récentes sont supportées. Les pilotes open sont activés par défaut pour les RTX 20xx+ (Turing+). Les GTX 10xx/16xx ne sont pas supportées.

> **Note thème Spicetify Comfy :** Après votre premier build, copiez le color.ini manuellement :
> ```bash
> cp ~/.config/spicetify/Themes/Comfy/color.ini ~/.config/roudix/modules/home/spicetify/Comfy/color.ini
> ```
> Puis lancez `rebuild` pour appliquer.

### 6. Mettre à jour le montage disque

Dans `hosts/roudix/local.nix`, ajoutez un bloc `lib.mkForce` avec votre propre UUID (ou passez cette étape si pas de disque secondaire) :

```bash
lsblk -f  # trouver l'UUID de votre disque
```

```nix
fileSystems."/mnt/gaming" = lib.mkForce {
  device = "/dev/disk/by-uuid/YOUR-UUID-HERE";
  fsType = "btrfs";
  options = [ "defaults" "nofail" ];
};
```

### 7. Configurer le multi-boot Limine (optionnel)

> Passez cette étape si vous n'avez que NixOS sur votre machine.

Limine peut démarrer d'autres systèmes d'exploitation sur des disques séparés. `boot.local.nix` contrôle les entrées supplémentaires — il est ignoré par git et jamais écrasé par `git pull`.

**Ne modifiez jamais `modules/system/boot/boot.nix` directement** — il est écrasé à chaque `git pull`.

#### Si vous avez utilisé l'installeur automatisé

L'installeur a détecté vos autres OS automatiquement depuis la NVRAM EFI (`efibootmgr`) et a écrit `boot.local.nix` pour vous — aucune action manuelle nécessaire. Vous pouvez vérifier le résultat :

```bash
cat modules/system/boot/boot.local.nix
```

#### Si vous installez manuellement

**Récupérez vos PARTUUID :**

```bash
lsblk -o NAME,FSTYPE,SIZE,PARTLABEL,PARTUUID
```

Cherchez les partitions avec le type de système de fichiers `vfat` et le label `EFI system partition` — ce sont vos ESP.

**Modifiez `modules/system/boot/boot.local.nix`** et ajoutez vos entrées :

```nix
{
  extraEntries = ''
    /+Other systems and bootloaders
    //Windows
      protocol: efi
      path: uuid(YOUR-WINDOWS-ESP-PARTUUID):/EFI/Microsoft/Boot/bootmgfw.efi
    //CachyOS
      protocol: efi
      path: uuid(YOUR-CACHYOS-ESP-PARTUUID):/EFI/limine/BOOTX64.EFI
  '';
}
```

> **Astuce :** Le chemin EFI après l'UUID dépend du bootloader utilisé par l'autre OS. Chemins courants :
> - Windows : `/EFI/Microsoft/Boot/bootmgfw.efi`
> - CachyOS (Limine) : `/EFI/limine/BOOTX64.EFI`
> - Arch/Manjaro (GRUB) : `/EFI/grub/grubx64.efi`
> - N'importe quelle distro (repli) : `/EFI/BOOT/BOOTX64.EFI`

Si vous n'avez pas d'autre OS à ajouter, laissez simplement `extraEntries` vide :

```nix
{
  extraEntries = "";
}
```

> `boot.local.nix` est listé dans `.gitignore` — il ne sera jamais écrasé par un `git pull`.

### 8. Mettre à jour la config git

`modules/home/git.nix` est ignoré par git (comme `local.nix`) — copiez le template suivi et renseignez votre identité :

```bash
cp modules/home/git.nix.example modules/home/git.nix
```

```nix
{ ... }:
{
  programs.git = {
    enable = true;
    settings = {
      user.name = "yourname";
      user.email = "your@email.com";
      init.defaultBranch = "main";
      pull.rebase = false;
    };
  };
}
```

- `init.defaultBranch = "main"` — nom utilisé pour la première branche quand vous faites un `git init` sur un nouveau dépôt (n'affecte pas la branche de ce dépôt-ci, seulement ceux que vous créez vous-même).
- `pull.rebase = false` — ce que fait `git pull` quand votre branche locale et le remote ont divergé : `false` fusionne (crée un commit de merge, comportement par défaut/le plus simple), `true` rebase vos commits locaux par-dessus le remote à la place (historique linéaire, mais réécrit vos commits — à éviter si vous n'êtes pas à l'aise avec les conflits de rebase). `false` est le choix le plus sûr pour un dépôt de config personnelle.

> Si le fichier est manquant, `common.nix` le saute simplement — Home Manager ne configurera pas git du tout tant que vous ne l'avez pas copié, mais rien ne casse.

### 9. Activer/désactiver les modules optionnels

Dans `hosts/roudix/local.nix` :

```nix
roudix.gaming.enable         = true;
roudix.flatpak.enable        = true;   # Flatpak + mise à jour automatique quotidienne
roudix.fstrim.enable         = true;   # recommandé pour SSD/NVMe
roudix.virtualization.enable = false;  # activer pour QEMU/KVM
roudix.vmGuest.enable        = true;   # activer uniquement dans une VM
roudix.hosts.gtaFix.enable   = true;   # bloque la télémétrie BattlEye (fix GTA)
roudix.autoupdate.enable     = true;   # auto pull + nh os boot lors des changements
roudix.zen.enable            = false;  # installer Zen Browser (désactivé par défaut)
roudix.mesa.useGit           = false;  # true = mesa-git (expérimental, bleeding edge — le build peut échouer), false = nixpkgs stable
roudix.boot.bootloader       = "limine";  # "limine" ou "systemd-boot"
roudix.matrixClient          = "none"; # "element", "cinny" ou "none"
```

> **Rappel :** Si vous mettez `roudix.autoupdate.enable = true`, configurez aussi l'intervalle :
> ```nix
> roudix.autoupdate.interval = "1h"; # 1h, 6h, 12h, 24h...
> ```

### 10. Personnaliser fastfetch (optionnel)

Par défaut, Roudix affiche son logo ASCII dans fastfetch. Vous pouvez le surcharger dans `home/local.nix` sans toucher à git :

```nix
# Utiliser une image personnalisée (nécessite le terminal kitty)
programs.fastfetch.settings.logo = {
  type = "kitty-direct";
  source = "/home/youruser/Pictures/my-logo.png";
  padding = { top = 1; left = 3; };
  width = 38;
};

# Utiliser un fichier ASCII personnalisé
programs.fastfetch.settings.logo = {
  type = "file";
  source = "/home/youruser/.config/fastfetch/my-logo.txt";
  padding = { top = 1; left = 3; };
  width = 38;
};

# Surcharger toute la config fastfetch (remplace tout)
programs.fastfetch.settings = lib.mkForce {
  "$schema" = "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json";
  logo = { ... };
  display = { separator = "  "; color = "33"; };
  modules = [ ... ];
};
```

> `lib.mkForce` écrase toute la config par défaut de Roudix. Sans lui, vos clés sont fusionnées avec les valeurs par défaut.
> Voir `home/local.nix.example` pour plus d'exemples.

### 11. Build

> **Si les flakes et nix-command ne sont pas encore activés** (install NixOS neuve) :

```bash
nix --extra-experimental-features 'nix-command flakes' shell nixpkgs#git -c sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

> **Sinon :**

```bash
sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

Une fois le build terminé, utilisez les alias fish pour toutes les opérations futures.

> Les trois fichiers `local.nix` et `boot.local.nix` sont listés dans `.gitignore` — ils ne seront jamais écrasés par un `git pull`.
