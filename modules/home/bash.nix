{ username, osConfig, lib, ... }:
let
  onNiri      = (osConfig.roudix.desktop.type or "") == "niri";
  onHyprland  = (osConfig.roudix.desktop.type or "") == "hyprland";
  onTilingDE  = onNiri || onHyprland;
  shellType           = osConfig.roudix.desktop.shell or "noctalia";
  availableShells     = if onHyprland then "noctalia|dms|caelestia" else "noctalia|dms";
  availableShellsList = if onHyprland then "noctalia, dms, caelestia" else "noctalia, dms";
in
{
  programs.bash = {
    enable = true;
    shellAliases = {
      rebuild  = "nh os switch --accept-flake-config path:$NH_FLAKE";
      update   = "sudo nix flake update --flake $NH_FLAKE && nh os switch --accept-flake-config path:$NH_FLAKE";
      cleanup  = "sudo nix-env --delete-generations +3 --profile /nix/var/nix/profiles/system && sudo nix-collect-garbage";
    } // lib.optionalAttrs (shellType == "noctalia") {
      noctalia-reload  = "pkill -f noctalia-shell; sleep 1; noctalia-shell --no-duplicate & disown";
    } // lib.optionalAttrs (shellType == "dms") {
      dms-reload       = "dms restart";
    } // lib.optionalAttrs (shellType == "caelestia") {
      caelestia-reload = "pkill -f caelestia-shell; sleep 1; caelestia-shell & disown";
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
          niri|gnome|kde|hyprland) ;;
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
    '' + lib.optionalString onTilingDE ''

      # ── roudix-shell-switch (niri & hyprland only) ────────────────────────
      roudix-shell-switch() {
        local shell="$1"
        local config_file="$NH_FLAKE/hosts/roudix/local.nix"

        if [ -z "$shell" ]; then
          echo "Usage: roudix-shell-switch [${availableShells}]"
          echo ""
          echo "Available graphical shells:"
          echo "  noctalia  — Roudix default shell"
          echo "  dms       — DankMaterialShell"
          ${lib.optionalString onHyprland ''echo "  caelestia  — Caelestia shell"''}
          return 1
        fi

        case "$shell" in
          ${availableShells}) ;;
          *)
            echo "Unknown shell: $shell"
            echo "Available: ${availableShellsList}"
            return 1
            ;;
        esac

        echo "Switching graphical shell to: $shell"
        if grep -q 'roudix\.desktop\.shell' "$config_file"; then
          sed -i "s/roudix\.desktop\.shell = \"[^\"]*\"/roudix.desktop.shell = \"$shell\"/" "$config_file"
        else
          sed -i "s/\(roudix\.desktop\.type = \"[^\"]*\";\)/\1\n  roudix.desktop.shell = \"$shell\";/" "$config_file"
        fi

        echo "Rebuilding configuration..."
        nh os boot --accept-flake-config path:$NH_FLAKE
      }
    '';
  };
}
