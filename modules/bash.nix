{ username, ... }:
{
  programs.bash = {
    enable = true;
    shellAliases = {
      rebuild  = "nh os switch /home/${username}/.config/roudix";
      update   = "sudo nix flake update --flake /home/${username}/.config/roudix && nh os switch /home/${username}/.config/roudix";
      cleanup  = "sudo nix-env --delete-generations +3 --profile /nix/var/nix/profiles/system && sudo nix-collect-garbage";
      noctalia-reload = "pkill quickshell; sleep 1; noctalia-shell --no-duplicate & disown";
    };

    # ── roudix-switch ─────────────────────────────────────────────────────
    initExtra = ''
      roudix-switch() {
        local de="$1"
        local config_file="/home/${username}/.config/roudix/hosts/roudix/configuration.nix"

        if [ -z "$de" ]; then
          echo "Usage: roudix-switch [niri|gnome|kde]"
          echo ""
          echo "Available desktop environments:"
          echo "  niri  — Niri scrollable tiling compositor + Noctalia"
          echo "  gnome — GNOME desktop environment"
          echo "  kde   — KDE Plasma"
          return 1
        fi

        case "$de" in
          niri|gnome|kde) ;;
          *)
            echo "Unknown desktop environment: $de"
            echo "Available: niri, gnome, kde"
            return 1
            ;;
        esac

        echo "Switching desktop environment to: $de"
        sed -i "s/roudix\.desktop\.type = \".*\"/roudix.desktop.type = \"$de\"/" "$config_file"

        echo "Rebuilding configuration..."
        nh os switch "/home/${username}/.config/roudix"
      }
    '';
  };
}
