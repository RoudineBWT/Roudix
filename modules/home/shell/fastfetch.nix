{ lib, config, username, dotfiles, osConfig, ... }:
{
  options.roudix.fastfetch = {
    useNix = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Use the Nix-managed Fastfetch configuration";
    };
  };

  config = {
    # ── Fastfetch ────────────────────────────────────────────────────────────
    # useNix = false: only install Fastfetch and keep the user's own config.
    # useNix = true : install Fastfetch and apply the Roudix configuration.
    programs.fastfetch = {
      enable = true;

      settings = lib.mkIf config.roudix.fastfetch.useNix {
        "$schema" = "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json";

        logo = {
          type = "auto";
          source = "${dotfiles}/fastfetch/roudix-ascii.txt";
          width = 38;
          color = {
            "1" = config.roudix.palette.dark.primary;
          };
        };

        display = {
          separator = "  ";
          color = config.roudix.palette.dark.primary;
        };

        modules = [
          { type = "break"; }

          {
            type = "custom";
            format = "─────────── System ───────────";
          }
          {
            type = "os";
            key = "󱄅 OS";
            keyColor = config.roudix.palette.dark.primary;
          }
          {
            type = "kernel";
            key = " Kernel";
            keyColor = config.roudix.palette.dark.primary;
          }
          {
            type = "uptime";
            key = "󰔟 Uptime";
            keyColor = config.roudix.palette.dark.primary;
          }
          {
            type = "command";
            key = "󱎫 OS Age";
            keyColor = config.roudix.palette.dark.primary;
            text = "b=$(stat -c %W /); n=$(date +%s); echo $(( (n - b) / 86400 )) days";
          }

          {
            type = "custom";
            format = "────────── Hardware ──────────";
          }
          {
            type = "cpu";
            key = " CPU";
            showPeCoreCount = true;
            keyColor = config.roudix.palette.dark.primary;
          }
          {
            type = "gpu";
            key = "󰍛 GPU";
            keyColor = config.roudix.palette.dark.primary;
          }
          {
            type = "memory";
            key = " Memory";
            keyColor = config.roudix.palette.dark.primary;
          }

          {
            type = "custom";
            format = "────────── Software ─────────";
          }
          {
            type = "wm";
            key = "󰇄 Compositor";
            keyColor = config.roudix.palette.dark.primary;
          }
          {
            type = "terminal";
            key = " Terminal";
            keyColor = config.roudix.palette.dark.primary;
          }
          {
            type = "shell";
            key = " Shell";
            keyColor = config.roudix.palette.dark.primary;
          }
          {
            type = "packages";
            key = " Packages";
            keyColor = config.roudix.palette.dark.primary;
          }

          {
            type = "custom";
            format = "─────────── Challenge ───────────";
          }
          {
            type = "command";
            key = "󰔸 Challenge";
            keyColor = config.roudix.palette.dark.primary;
            text = ''
              start=$(stat -c %W /)
              end=$((start + 63072000))
              now=$(date +%s)
              elapsed=$((now - start))
              total=$((end - start))
              pct=$((elapsed * 100 / total))
              days_done=$((elapsed / 86400))
              days_left=$(((end - now) / 86400))
              filled=$((pct * 20 / 100))
              empty=$((20 - filled))
              bar=$(printf '█%.0s' $(seq 1 "$filled" 2>/dev/null))$(printf '░%.0s' $(seq 1 "$empty" 2>/dev/null))
              echo "[$bar] $pct% — $days_done days / 730 days ($days_left remaining)"
            '';
          }

          {
            type = "custom";
            format = "───────────────────────────────";
          }
          {
            type = "custom";
            key = "  ";
            format = "  {#${config.roudix.palette.dark.primary}}Romeo, Oscar, Uniform, Delta, India, X-ray!{#}";
            newline = true;
          }

          { type = "break"; }
        ];
      };
    };

    # Roudix branding file used by the Nix-managed Fastfetch configuration.
    xdg.configFile."fastfetch/roudix-ascii.txt" = lib.mkIf config.roudix.fastfetch.useNix {
      source = "${dotfiles}/fastfetch/roudix-ascii.txt";
    };

    # Runs Fastfetch in every interactive Fish shell.
    xdg.configFile."fish/conf.d/fastfetch.fish" = {
      text = ''
        fastfetch
      '';
    };
  };
}
