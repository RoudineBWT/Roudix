{ lib, onHyprland, shellList, availableShells, availableShellsList, ... }: {
  fish = ''
    set shell $argv[1]
    set config_file "$NH_FLAKE/hosts/roudix/local.nix"

    if test -z "$shell"
      echo "Usage: roudix-shell-switch [${shellList}]"
      echo ""
      echo "Available graphical shells:"
      echo "  noctalia  — Roudix default shell"
      echo "  dms       — DankMaterialShell"
      ${lib.optionalString onHyprland ''echo "  caelestia  — Caelestia shell"''}
      return 1
    end

    if not contains $shell ${shellList}
      echo "Unknown shell: $shell"
      echo "Available: ${shellList}"
      return 1
    end

    echo "Switching graphical shell to: $shell"
    if grep -q 'roudix\.desktop\.shell' $config_file
      sed -i "s/roudix\.desktop\.shell = \"[^\"]*\"/roudix.desktop.shell = \"$shell\"/" $config_file
    else
      sed -i "s/\(roudix\.desktop\.type = \"[^\"]*\";\)/\1\n  roudix.desktop.shell = \"$shell\";/" $config_file
    end

    echo "Rebuilding configuration..."
    nh os boot --accept-flake-config path:$NH_FLAKE
  '';

  bash = ''
    roudix-shell-switch() {
      local shell="$1"
      local config_file="$NH_FLAKE/hosts/roudix/local.nix"

      if [[ -z "$shell" ]]; then
        echo "Usage: roudix-shell-switch [${availableShellsList}]"
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
      nh os boot --accept-flake-config path:"$NH_FLAKE"
    }
  '';
}
