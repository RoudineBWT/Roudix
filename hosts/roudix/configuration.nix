{ pkgs, inputs, config, lib, username, ... }:
{
  imports = [
    ./hardware-configuration.nix
    ../../modules/system/shell.nix
    ../../modules/system/autoupdate.nix
    ../../modules/system/common.nix
    ../../modules/system/desktop
    ../../modules/system/environment.nix
    ../../modules/system/browser.nix
    ../../modules/system/boot.nix
    ../../modules/system/kernel.nix
    ../../modules/system/gaming.nix
    ../../modules/system/content-creation.nix
    ../../modules/system/apps.nix
    ../../modules/system/spicetify.nix
    ../../modules/system/scx.nix
    ../../modules/system/flatpak.nix
    ../../modules/system/gpu
    ../../modules/system/roudix-rgb.nix
    ../../modules/system/cpu.nix
    ../../modules/system/pipewire.nix
    ../../modules/system/fstrim.nix
    ../../modules/system/virtualization.nix
    ../../modules/system/vm-guest.nix
    ../../modules/system/update.nix
    ../../modules/system/hosts-gta.nix
    ../../modules/system/mesa-git.nix
    ../../modules/system/waydroid.nix
    ../../modules/system/matrix.nix
    ../../modules/system/telegram.nix
    ../../modules/system/video-player.nix
    ../../modules/system/torrent-client.nix
    ../../modules/system/appimage.nix
    ../../modules/system/filemanager.nix
    ../../modules/system/terminal.nix
    ../../modules/system/editor.nix
    ../../modules/system/desktop-integration.nix
    ../../modules/system/icon-theme.nix
    ../../modules/system/keyboard.nix
    ../../modules/system/discord.nix
     inputs.brave-previews.nixosModules.default
  ] ++ lib.optional (builtins.pathExists ./local.nix) ./local.nix
  ++ lib.optional (builtins.pathExists ../../modules/system/gpu/undervolt.nix) ../../modules/system/gpu/undervolt.nix;


  # ── Choose your favorite chromium base browser ───────────────────────────
  roudix.browsers = lib.mkDefault ["helium"]; # brave or helium or vivaldi

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
  roudix.gaming.enable         = lib.mkDefault true;
  roudix.gaming.ananicy.enable = lib.mkDefault true;
  roudix.flatpak.enable        = lib.mkDefault false;
  roudix.fstrim.enable         = lib.mkDefault true;
  roudix.virtualization.enable = lib.mkDefault false;
  roudix.vmGuest.enable        = lib.mkDefault false; # enable only inside a VM
  roudix.hosts.gtaFix.enable   = lib.mkDefault false;
  roudix.autoupdate.enable     = lib.mkDefault true;
  roudix.mesa.useGit = lib.mkDefault false;  # false = nixpkgs stable mesa
  roudix.waydroid.enable = lib.mkDefault false;
  roudix.matrixClient = lib.mkDefault "none"; # "element", "cinny" or "none"
  # Umbriel only: Discord/Telegram/Spotify as named scratchpads (show/
  # hide/toggle via keybind) instead of tiled in a fixed spot. See
  # modules/system/desktop/umbriel.nix for the full description.
  roudix.umbriel.scratchpadApps = lib.mkDefault false;
  # ── Network ─────────────────────────────────────────────────────────────
  networking.hostName = "roudix";
}
