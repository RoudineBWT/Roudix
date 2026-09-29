{ lib, config, username, dotfiles, osConfig, ... }:
{
  options.roudix.fastfetch = {
    useNix = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "fastfetch via nix or not";
    };
  };

  config = {
    # ── Fastfetch ────────────────────────────────────────────────────────────
    # The package is always installed, whether useNix is true or false.
    # useNix = false: keeps only the package, your own config in
    #                 ~/.config/fastfetch stays in use.
    # useNix = true : also applies the Roudix config below.
    programs.fastfetch = {
      enable = true;

      settings = lib.mkIf config.roudix.fastfetch.useNix {
        "$schema" = "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json";

        logo = {
          type = "auto";
          source = "${dotfiles}/fastfetch/roudix-ascii.txt";
          height = 38;
          "color"= {
            "1" = "#fab387";
          };
        };

        display = {
          separator = "  ";
          color = "#fab387";
        };

        modules = [
          { type = "break"; }
          { type = "custom"; format = "─────────── System ───────────"; }
          { type = "os";       key = "󱄅 OS";        keyColor = "#fab387"; }
          { type = "kernel";   key = " Kernel";     keyColor = "#fab387"; }
          { type = "uptime";   key = "󰔟 Uptime";    keyColor = "#fab387"; }
          {
            type = "command";
            key = "󱎫 OS Age";
            keyColor = "#fab387";
            text = "b=$(stat -c %W /); n=$(date +%s); echo $(( (n - b) / 86400 )) days";
          }
          { type = "custom"; format = "────────── Hardware ──────────"; }
          { type = "cpu";    key = " CPU";  showPeCoreCount = true; keyColor = "#fab387"; }
          { type = "gpu";    key = "󰍛 GPU";  keyColor = "#fab387"; }
          { type = "memory"; key = " Memory"; keyColor = "#fab387"; }
          { type = "custom"; format = "────────── Software ─────────"; }
          { type = "wm";       key = "󰇄 Compositor"; keyColor = "#fab387"; }
          { type = "terminal"; key = " Terminal";    keyColor = "#fab387"; }
          { type = "shell";    key = " Shell";       keyColor = "#fab387"; }
          { type = "packages"; key = " Packages";   keyColor = "#fab387"; }
          { type = "custom"; format = "───────────────────────────────"; }
          { type = "custom"; format = "─────────── Challenge ───────────"; }
          {
            type = "command";
            key = "󰔸 Challenge";
            keyColor = "#fab387";
            text = ''
              start=$(stat -c %W /); end=$((start + 63072000)); now=$(date +%s)
              elapsed=$(( now - start )); total=$(( end - start ))
              pct=$(( elapsed * 100 / total ))
              days_done=$(( elapsed / 86400 )); days_left=$(( (end - now) / 86400 ))
              filled=$(( pct * 20 / 100 )); empty=$(( 20 - filled ))
              bar=$(printf '█%.0s' $(seq 1 $filled 2>/dev/null))$(printf '░%.0s' $(seq 1 $empty 2>/dev/null))
              echo "[$bar] $pct% — $days_done days / 730 days ($days_left remaining)"
            '';
          }
          { type = "custom"; format = "───────────────────────────────"; }
          { type = "break"; }
        ];
      };
    };

    # Roudix branding file: only relevant when using the Nix config.
    xdg.configFile."fastfetch/roudix.txt" = lib.mkIf config.roudix.fastfetch.useNix {
      source = "${dotfiles}/fastfetch/roudix.txt";
    };

    # Runs fastfetch on every interactive fish shell, regardless of useNix.
    xdg.configFile."fish/conf.d/fastfetch.fish" = {
      text = ''
        fastfetch
      '';
    };
  };
}
