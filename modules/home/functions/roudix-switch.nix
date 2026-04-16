{ ... }: {
  fish = ''
    set de $argv[1]
    set config_file "$NH_FLAKE/hosts/roudix/local.nix"

    if test -z "$de"
      echo "Usage: roudix-switch [niri|gnome|kde|hyprland|mangowc]"
      echo ""
      echo "Available desktop environments:"
      echo "  niri     — Niri scrollable tiling compositor + Noctalia"
      echo "  gnome    — GNOME desktop environment"
      echo "  kde      — KDE Plasma"
      echo "  hyprland — Dynamic tiling Wayland compositor + Noctalia shell"
      echo "  mangowc  — Lightweight dynamic tiling Wayland compositor"
      return 1
    end

    if not contains $de niri gnome kde hyprland mangowc
      echo "Unknown desktop environment: $de"
      echo "Available: niri, gnome, kde, hyprland, mangowc"
      return 1
    end

    echo "Switching desktop environment to: $de"
    sed -i "s/roudix\.desktop\.type = \"[^\"]*\"/roudix.desktop.type = \"$de\"/" $config_file

    echo "Rebuilding configuration..."
    nh os boot --accept-flake-config path:$NH_FLAKE
  '';

  bash = ''
    roudix-switch() {
      local de="$1"
      local config_file="$NH_FLAKE/hosts/roudix/local.nix"

      if [[ -z "$de" ]]; then
        echo "Usage: roudix-switch [niri|gnome|kde|hyprland|mangowc]"
        echo ""
        echo "Available desktop environments:"
        echo "  niri     — Niri scrollable tiling compositor + Noctalia"
        echo "  gnome    — GNOME desktop environment"
        echo "  kde      — KDE Plasma"
        echo "  hyprland — Dynamic tiling Wayland compositor + Noctalia shell"
        echo "  mangowc  — Lightweight dynamic tiling Wayland compositor"
        return 1
      fi

      case "$de" in
        niri|gnome|kde|hyprland|mangowc) ;;
        *)
          echo "Unknown desktop environment: $de"
          echo "Available: niri, gnome, kde, hyprland, mangowc"
          return 1
          ;;
      esac

      echo "Switching desktop environment to: $de"
      sed -i "s/roudix\.desktop\.type = \"[^\"]*\"/roudix.desktop.type = \"$de\"/" "$config_file"

      echo "Rebuilding configuration..."
      nh os boot --accept-flake-config path:"$NH_FLAKE"
    }
  '';
}
