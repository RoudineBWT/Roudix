# Installation

## Automated Installation

**Download the roudix-installer script**

```bash
nix-shell -p wget --run "wget https://github.com/RoudineBWT/Roudix/raw/refs/heads/main/roudix-installer.sh"
chmod +x roudix-installer.sh
./roudix-installer.sh
```

The installer handles everything interactively:
- Clones the repo, generates `hardware-configuration.nix`, creates all local config files
- **Detects other OSes automatically** via EFI NVRAM (`efibootmgr`) — no manual PARTUUID lookup needed
- **Detects GPU and CPU automatically** (`lspci` / `/proc/cpuinfo`) — pre-selects and asks for confirmation
- **Detects if running in a VM** (`systemd-detect-virt`) — pre-enables VM guest mode and warns that GPU/CPU detection may be inaccurate
- Asks about kernel, desktop, browser, locale, timezone, keymap, and optional modules
- Builds and applies the configuration

---

## Manual Installation

> ⚠️ **Follow every step carefully before rebuilding.**

### 1. Clone the repo

> **If `git` is not installed** (fresh NixOS install):

```bash
nix-shell -p git --run "git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix"
```

> **Otherwise:**

```bash
git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix
cd ~/.config/roudix
```

### 2. Set your username

Create the `username.nix` file with your username:

```bash
echo '"yourusername"' > ~/.config/roudix/hosts/roudix/username.nix
```

> This file is gitignored — it will never be overwritten by a `git pull`.

### 3. Replace hardware-configuration.nix

```bash
sudo cp /etc/nixos/hardware-configuration.nix ~/.config/roudix/hosts/roudix/hardware-configuration.nix
```

### 4. Create your local configs

**Never edit `configuration.nix` or `home/common.nix` directly** — they get overwritten on `git pull`.
Instead, create your local override files (all gitignored):

```bash
cp hosts/roudix/local.nix.example hosts/roudix/local.nix
cp home/local.nix.example home/local.nix
cp modules/system/boot.local.nix.example modules/system/boot.local.nix
```

Edit `hosts/roudix/local.nix` to match your hardware:

```nix
{ lib, ... }:
{
  roudix.desktop.type = "niri";               # "niri", "hyprland", "gnome" or "kde"
  hardware.myGpu      = "amd";                # "amd", "nvidia" or "intel"
  hardware.myCpu      = "intel";              # "intel" or "amd"
  hardware.myKernel   = "cachyos-lts-lto-v3"; # see below
  roudix.browsers     = [ "helium" ];         # "brave", "helium", "vivaldi", "firefox", "librewolf", "chromium" or []
  roudix.zen.enable   = false;                # set to true to also install Zen Browser

  # ── Locale / Timezone ───────────────────────────────────────────────────────
  time.timeZone                   = "Europe/Brussels"; # see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
  environment.sessionVariables.TZ = "Europe/Brussels"; # must match time.timeZone
  i18n.defaultLocale              = "en_US.UTF-8";     # system locale
  console.keyMap                  = "us";              # console keyboard layout
}
```

**Common timezone values:**

| Timezone | Region |
|----------|--------|
| `Europe/Brussels` | Belgium |
| `Europe/Paris` | France |
| `Europe/London` | United Kingdom |
| `Europe/Berlin` | Germany |
| `Europe/Amsterdam` | Netherlands |
| `America/New_York` | US East |
| `America/Los_Angeles` | US West |
| `Asia/Tokyo` | Japan |
| `UTC` | Universal |

**Common locale values:**

| Locale | Language |
|--------|----------|
| `en_US.UTF-8` | English (US) |
| `en_GB.UTF-8` | English (UK) |
| `fr_BE.UTF-8` | Français (Belgique) |
| `fr_FR.UTF-8` | Français (France) |
| `de_DE.UTF-8` | Deutsch |
| `nl_BE.UTF-8` | Nederlands (België) |
| `nl_NL.UTF-8` | Nederlands |
| `es_ES.UTF-8` | Español |
| `pt_BR.UTF-8` | Português (Brasil) |
| `it_IT.UTF-8` | Italiano |
| `ru_RU.UTF-8` | Русский |
| `ja_JP.UTF-8` | 日本語 |
| `zh_CN.UTF-8` | 中文 (简体) |
| `ko_KR.UTF-8` | 한국어 |

**Common console keymap values:**

| Keymap | Layout |
|--------|--------|
| `us` | English (US) QWERTY |
| `us-acentos` | English (US) International |
| `uk` | English (UK) QWERTY |
| `be-latin1` | Belge AZERTY |
| `fr` | Français AZERTY |
| `de` | Allemand QWERTZ |
| `nl` | Néerlandais QWERTY |
| `es` | Espagnol QWERTY |
| `dvorak` | Dvorak (US) |
| `colemak` | Colemak |

> **Note:** `environment.sessionVariables.TZ` must always match `time.timeZone` — they both control the timezone, one at the system level and one at the session level.

Edit `home/local.nix` for personal home-manager overrides (extra packages, dotfiles, aliases, fastfetch...):

```nix
{ pkgs, lib, osConfig, ... }:
{
  # home.packages = with pkgs; [ vlc telegram-desktop ];
}
```

> See `home/local.nix.example` for all available override options including fastfetch customization.

### 5. Configure kernel

**Available kernel variants:**

| Variant | Description |
|---------|-------------|
| `cachyos-latest` | Standard latest CachyOS kernel |
| `cachyos-latest-v2` | x86_64-v2 optimized |
| `cachyos-latest-v3` | x86_64-v3 optimized (recommended for modern CPUs) |
| `cachyos-latest-v4` | x86_64-v4 optimized (AVX-512, very recent CPUs only) |
| `cachyos-latest-zen4` | AMD Zen 4 optimized |
| `cachyos-latest-lto` | LTO build for better performance |
| `cachyos-latest-lto-v2` | LTO + x86_64-v2 |
| `cachyos-latest-lto-v3` | LTO + x86_64-v3 (best performance, modern CPUs only) |
| `cachyos-latest-lto-v4` | LTO + x86_64-v4 (AVX-512) |
| `cachyos-latest-lto-zen4` | LTO + AMD Zen 4 |
| `cachyos-lts` | Long-term support CachyOS kernel |
| `cachyos-lts-v2` | LTS + x86_64-v2 |
| `cachyos-lts-v3` | LTS + x86_64-v3 optimized |
| `cachyos-lts-v4` | LTS + x86_64-v4 (AVX-512) |
| `cachyos-lts-zen4` | LTS + AMD Zen 4 |
| `cachyos-lts-lto` | LTS + LTO |
| `cachyos-lts-lto-v2` | LTS + LTO + x86_64-v2 |
| `cachyos-lts-lto-v3` | LTS + LTO + x86_64-v3 (stable + performance) |
| `cachyos-lts-lto-v4` | LTS + LTO + x86_64-v4 (AVX-512) |
| `cachyos-lts-lto-zen4` | LTS + LTO + AMD Zen 4 |
| `cachyos-bmq` | BMQ scheduler |
| `cachyos-bmq-lto` | BMQ scheduler + LTO |
| `cachyos-bore` | BORE scheduler (better interactivity) |
| `cachyos-bore-lto` | BORE scheduler + LTO |
| `cachyos-deckify` | Steam Deck optimized |
| `cachyos-deckify-lto` | Steam Deck optimized + LTO |
| `cachyos-eevdf` | EEVDF scheduler |
| `cachyos-eevdf-lto` | EEVDF scheduler + LTO |
| `cachyos-hardened` | Security hardened kernel |
| `cachyos-hardened-lto` | Security hardened + LTO |
| `cachyos-rc` | Release candidate — bleeding edge, potentially unstable |
| `cachyos-rc-lto` | Release candidate + LTO |
| `cachyos-rt-bore` | Real-time + BORE scheduler |
| `cachyos-rt-bore-lto` | Real-time + BORE + LTO |
| `cachyos-server` | Server optimized (no desktop tuning) |
| `cachyos-server-lto` | Server optimized + LTO |

> **NVIDIA note:** Only GTX 20xx / RTX series and newer are supported. Open drivers enabled by default for RTX 20xx+ (Turing+). GTX 10xx/16xx are not supported.

> **Spicetify Comfy theme note:** After your first build, copy the color.ini manually:
> ```bash
> cp ~/.config/spicetify/Themes/Comfy/color.ini ~/.config/roudix/modules/home/spicetify/Comfy/color.ini
> ```
> Then run `rebuild` to apply.

### 6. Update the disk mount

In `hosts/roudix/local.nix`, add a `lib.mkForce` block with your own UUID (or skip if no secondary disk):

```bash
lsblk -f  # find your disk UUID
```

```nix
fileSystems."/mnt/gaming" = lib.mkForce {
  device = "/dev/disk/by-uuid/YOUR-UUID-HERE";
  fsType = "btrfs";
  options = [ "defaults" "nofail" ];
};
```

### 7. Configure Limine multi-boot (optional)

> Skip this step if you only have NixOS on your machine.

Limine can boot other operating systems on separate disks. `boot.local.nix` controls the extra entries — it is gitignored and never overwritten by `git pull`.

**Never edit `modules/system/boot.nix` directly** — it gets overwritten on `git pull`.

#### If you used the automated installer

The installer detected your other OSes automatically from the EFI NVRAM (`efibootmgr`) and wrote `boot.local.nix` for you — no manual action needed. You can review the result:

```bash
cat modules/system/boot.local.nix
```

#### If you are installing manually

**Get your PARTUUIDs:**

```bash
lsblk -o NAME,FSTYPE,SIZE,PARTLABEL,PARTUUID
```

Look for partitions with `vfat` filesystem type and `EFI system partition` label — those are your ESPs.

**Edit `modules/system/boot.local.nix`** and add your entries:

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

> **Tip:** The EFI path after the UUID depends on the bootloader used by the other OS. Common paths:
> - Windows: `/EFI/Microsoft/Boot/bootmgfw.efi`
> - CachyOS (Limine): `/EFI/limine/BOOTX64.EFI`
> - Arch/Manjaro (GRUB): `/EFI/grub/grubx64.efi`
> - Any distro (fallback): `/EFI/BOOT/BOOTX64.EFI`

If you have no other OS to add, just leave `extraEntries` empty:

```nix
{
  extraEntries = "";
}
```

> `boot.local.nix` is listed in `.gitignore` — it will never be overwritten by a `git pull`.

### 8. Update git config

In `modules/home/git.nix`:

```nix
settings = {
  user.name = "yourname";
  user.email = "your@email.com";
};
```

### 9. Enable/disable optional modules

In `hosts/roudix/local.nix`:

```nix
roudix.gaming.enable         = true;
roudix.flatpak.enable        = true;   # Flatpak + daily auto-update
roudix.fstrim.enable         = true;   # recommended for SSD/NVMe
roudix.virtualization.enable = false;  # enable for QEMU/KVM
roudix.vmGuest.enable        = true;   # enable only inside a VM
roudix.hosts.gtaFix.enable   = true;   # block BattlEye telemetry (GTA fix)
roudix.autoupdate.enable     = true;   # auto pull + nh os boot on changes
roudix.zen.enable            = false;  # install Zen Browser (disabled by default)
```

> **Reminder:** If you set `roudix.autoupdate.enable = true`, also configure the interval:
> ```nix
> roudix.autoupdate.interval = "1h"; # 1h, 6h, 12h, 24h...
> ```

### 10. Customize fastfetch (optional)

By default Roudix shows its ASCII logo in fastfetch. You can override it in `home/local.nix` without touching git:

```nix
# Use a custom image (requires kitty terminal)
programs.fastfetch.settings.logo = {
  type = "kitty-direct";
  source = "/home/youruser/Pictures/my-logo.png";
  padding = { top = 1; left = 3; };
  width = 38;
};

# Use a custom ASCII file
programs.fastfetch.settings.logo = {
  type = "file";
  source = "/home/youruser/.config/fastfetch/my-logo.txt";
  padding = { top = 1; left = 3; };
  width = 38;
};

# Override the entire fastfetch config (replaces everything)
programs.fastfetch.settings = lib.mkForce {
  "$schema" = "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json";
  logo = { ... };
  display = { separator = "  "; color = "33"; };
  modules = [ ... ];
};
```

> `lib.mkForce` overwrites the entire Roudix default config. Without it, your keys are merged with the defaults.
> See `home/local.nix.example` for more examples.

### 11. Build

> **If flakes and nix-command are not enabled yet** (fresh NixOS install):

```bash
nix --extra-experimental-features 'nix-command flakes' shell nixpkgs#git -c sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

> **Otherwise:**

```bash
sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

Once built, use the fish aliases for all future operations.

> All three `local.nix` files and `boot.local.nix` are listed in `.gitignore` — they will never be overwritten by a `git pull`.
