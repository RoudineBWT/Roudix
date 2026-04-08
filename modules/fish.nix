{ pkgs, username, ... }:
{
  # ── Fish ─────────────────────────────────────────────────────────────────
  programs.fish = {
    enable = true;
    shellAliases = {
      update   = "sudo nix flake update --flake $NH_FLAKE && nh os switch --accept-flake-config $NH_FLAKE";
      rebuild  = "nh os switch --accept-flake-config $NH_FLAKE";
      cleanup  = "sudo nix-env --delete-generations +3 --profile /nix/var/nix/profiles/system && sudo nix-collect-garbage";
      noctalia-reload = "pkill quickshell; sleep 1; noctalia-shell --no-duplicate & disown";
    };

    # ── roudix-switch: change desktop environment and rebuild ─────────────
    functions.roudix-switch = {
      description = "Switch desktop environment (niri, gnome, kde)";
      body = ''
        set de $argv[1]
        set config_file "$NH_FLAKE/hosts/roudix/local.nix"

        if test -z "$de"
          echo "Usage: roudix-switch [niri|gnome|kde]"
          echo ""
          echo "Available desktop environments:"
          echo "  niri  — Niri scrollable tiling compositor + Noctalia"
          echo "  gnome — GNOME desktop environment"
          echo "  kde   — KDE Plasma"
          return 1
        end

        if not contains $de niri gnome kde
          echo "Unknown desktop environment: $de"
          echo "Available: niri, gnome, kde"
          return 1
        end

        echo "Switching desktop environment to: $de"
        sed -i "s/roudix\.desktop\.type = \".*\"/roudix.desktop.type = \"$de\"/" $config_file

        echo "Rebuilding configuration..."
        nh os boot --accept-flake-config $NH_FLAKE
      '';
    };
  };

  # ── Starship ─────────────────────────────────────────────────────────────
  programs.starship = {
    enable = true;
    enableFishIntegration = true;
  };
}
