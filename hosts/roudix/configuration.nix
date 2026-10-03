{ pkgs, inputs, config, lib, username, ... }:
{
  imports = [
    ./hardware-configuration.nix
    ../../modules/system/core
    ../../modules/system/nix
    ../../modules/system/desktop
    ../../modules/system/boot
    ../../modules/system/gaming
    ../../modules/system/apps
    ../../modules/system/packaging
    ../../modules/system/gpu
    ../../modules/system/rgb
    ../../modules/system/power
    ../../modules/system/audio
    ../../modules/system/virtualization
     inputs.brave-previews.nixosModules.default
  ] ++ lib.optional (builtins.pathExists ./local.nix) ./local.nix
  ++ lib.optional (builtins.pathExists ../../modules/system/gpu/undervolt.nix) ../../modules/system/gpu/undervolt.nix;


  # ── Browser ──────────────────────────────────────────────────────────────
  # None by default: pick yours in local.nix (see local.nix.example).
  roudix.browsers = lib.mkDefault [];

  # ── Hardware ────────────────────────────────────────────────────────────
  hardware.myGpu    = lib.mkDefault "amd";              # "amd", "nvidia" or "intel"
  hardware.myCpu    = lib.mkDefault "intel";            # "intel" or "amd"
  hardware.myKernel = lib.mkDefault "cachyos-lts-lto-v3"; # xddxdd — used when hardware.myGpu != "nvidia", see README
  hardware.myKernelChaotic = lib.mkDefault "cachyos";     # Chaotic-Nyx — used only when hardware.myGpu == "nvidia"
  roudix.rgb        = lib.mkDefault "none";           # "openlinkhub" (full Corsair), "openrgb" (mixed/other brands) or "none"
  roudix.memory.enable  = lib.mkDefault false;          # true to enable RAM RGB
  roudix.memory.type    = lib.mkDefault "ddr5";         # "ddr4" or "ddr5"
  roudix.memory.smBus   = lib.mkDefault "i2c-0";        # found via: i2cdetect -l
  roudix.memory.sku    = lib.mkDefault "CMH64GX5M2B5200C40"; # found via: sudo dmidecode -t memory | grep 'Part Number'
  # ── Features ────────────────────────────────────────────────────────────
  roudix.boot.bootloader = lib.mkDefault "limine"; # "limine" or "systemd-boot"
  roudix.terminal        = lib.mkDefault "ghostty"; # "ghostty", "kitty", "alacritty", "foot" or "wezterm"
  roudix.gaming.enable         = lib.mkDefault false;
  roudix.gaming.ananicy.enable = lib.mkDefault false;
  roudix.flatpak.enable        = lib.mkDefault false;
  roudix.fstrim.enable         = lib.mkDefault true;
  roudix.virtualization.enable = lib.mkDefault false;
  roudix.podman.enable         = lib.mkDefault false;
  roudix.distrobox.enable      = lib.mkDefault false;
  roudix.vmGuest.enable        = lib.mkDefault false; # enable only inside a VM
  roudix.hosts.gtaFix.enable   = lib.mkDefault false;
  roudix.laptop.enable         = lib.mkDefault false; # true on laptops (TLP)
  roudix.laptop.thinkpad       = lib.mkDefault false; # true on ThinkPads (charge thresholds)
  roudix.autoupdate.enable     = lib.mkDefault true;
  roudix.mesa.useGit = lib.mkDefault false;  # false = nixpkgs stable mesa
  roudix.waydroid.enable = lib.mkDefault false;
  roudix.matrixClient = lib.mkDefault "none"; # "element", "cinny" or "none"

  # ── Optional apps: everything off unless picked in local.nix ───────────
  # These mirror hosts/roudix/local.nix.example. A build without a
  # local.nix (CI, for instance) therefore gets the minimal system instead
  # of building every optional app. The module-level defaults (e.g.
  # roudix.videoPlayer = "vlc") are untouched, so other hosts keep theirs.
  roudix.editor        = lib.mkDefault "none";
  roudix.discord       = lib.mkDefault "none";
  roudix.videoPlayer   = lib.mkDefault "none";
  roudix.musicPlayer   = lib.mkDefault "none";
  roudix.telegram      = lib.mkDefault "none";
  roudix.torrentClient = lib.mkDefault "none";
  roudix.mailClient    = lib.mkDefault "none";
  roudix.passwordManager = lib.mkDefault "none";
  roudix.apps.gimp.enable        = lib.mkDefault false;
  roudix.apps.inkscape.enable    = lib.mkDefault false;
  roudix.apps.songrec.enable     = lib.mkDefault false;
  roudix.apps.easyeffects.enable = lib.mkDefault false;
  roudix.apps.signal.enable      = lib.mkDefault false;
  roudix.apps.zapzap.enable      = lib.mkDefault false;
  roudix.apps.fluxer.enable      = lib.mkDefault false;
  roudix.zen.enable              = lib.mkDefault false;
  roudix.contentCreation.enable  = lib.mkDefault false;
  roudix.contentCreation.obs.enable = lib.mkDefault false;
  roudix.contentCreation.videoEditor = lib.mkDefault "none";
  roudix.contentCreation.virtualCamera.enable = lib.mkDefault false;
  roudix.gaming.apps.lutris.enable        = lib.mkDefault false;
  roudix.gaming.apps.heroic.enable        = lib.mkDefault false;
  roudix.gaming.apps.faugus.enable        = lib.mkDefault false;
  roudix.gaming.apps.prismlauncher.enable = lib.mkDefault false;
  roudix.gaming.apps.modrinth.enable      = lib.mkDefault false;
  roudix.gaming.apps.vintagestory.enable  = lib.mkDefault false;
  roudix.gaming.apps.mangohud.enable      = lib.mkDefault false;
  # Umbriel only: Discord/Telegram/Spotify as named scratchpads (show/
  # hide/toggle via keybind) instead of tiled in a fixed spot. See
  # modules/system/desktop/umbriel.nix for the full description.
  roudix.umbriel.scratchpadApps = lib.mkDefault false;
  # ── Network ─────────────────────────────────────────────────────────────
  networking.hostName = "roudix";
}
