{ username, ... }:
{
  programs.bash = {
    enable = true;
    shellAliases = {
      rebuild  = "nh os switch --accept-flake-config path:$NH_FLAKE";
      update   = "sudo nix flake update --flake $NH_FLAKE && nh os switch --accept-flake-config path:$NH_FLAKE";
      cleanup  = "sudo nix-env --delete-generations +3 --profile /nix/var/nix/profiles/system && sudo nix-collect-garbage";
      noctalia-reload = "pkill quickshell; sleep 1; noctalia-shell --no-duplicate & disown";
    };

    # ── roudix-switch ─────────────────────────────────────────────────────
    initExtra = ''
      roudix-switch() {
        local de="$1"
        local config_file="$NH_FLAKE/hosts/roudix/local.nix"

        if [ -z "$de" ]; then
          echo "Usage: roudix-switch [niri|gnome|kde|hyprland]"
          echo ""
          echo "Available desktop environments:"
          echo "  niri  — Niri scrollable tiling compositor + Noctalia"
          echo "  gnome — GNOME desktop environment"
          echo "  kde   — KDE Plasma"
          echo "  hyprland   — Dynamic tiling Wayland compositor + Noctalia shell"
          return 1
        fi

        case "$de" in
          niri|gnome|kde) ;;
          *)
            echo "Unknown desktop environment: $de"
            echo "Available: niri, gnome, kde, hyprland"
            return 1
            ;;
        esac

        echo "Switching desktop environment to: $de"
        sed -i "s/roudix\.desktop\.type = \"[^\"]*\"/roudix.desktop.type = \"$de\"/" $config_file

        echo "Rebuilding configuration..."
        nh os boot --accept-flake-config path:$NH_FLAKE
      }
    '';
  };
}
