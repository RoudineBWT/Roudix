{ username, dotfiles, ... }:
{
  # ── Fastfetch ────────────────────────────────────────────────────────────
  programs.fastfetch = {
    enable = true;

    settings = {
      "$schema" = "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json";

      logo = {
        type = "kitty-direct";
        source = "${dotfiles}/fastfetch/roudix_fox_icon_256.png";
        height = 100;
        padding = {
          right = 5;
        };
      };

      display = {
        separator = "  ";
        color = "#7aa2f7";
      };

      modules = [
        { type = "break"; }
        { type = "custom"; format = "─────────── System ───────────"; }
        { type = "os";       key = "󱄅 OS";        keyColor = "#7aa2f7"; }
        { type = "kernel";   key = " Kernel";     keyColor = "#7aa2f7"; }
        { type = "uptime";   key = "󰔟 Uptime";    keyColor = "#7aa2f7"; }
        {
          type = "command";
          key = "󱎫 OS Age";
          keyColor = "#7aa2f7";
          text = "b=$(stat -c %W /); n=$(date +%s); echo $(( (n - b) / 86400 )) days";
        }
        { type = "custom"; format = "────────── Hardware ──────────"; }
        { type = "cpu";    key = " CPU";  showPeCoreCount = true; keyColor = "#7dcfff"; }
        { type = "gpu";    key = "󰍛 GPU";  keyColor = "#7dcfff"; }
        { type = "memory"; key = " Memory"; keyColor = "#7dcfff"; }
        { type = "custom"; format = "────────── Software ─────────"; }
        { type = "wm";       key = "󰇄 Compositor"; keyColor = "#bb9af7"; }
        { type = "terminal"; key = " Terminal";    keyColor = "#bb9af7"; }
        { type = "shell";    key = " Shell";       keyColor = "#bb9af7"; }
        { type = "packages"; key = " Packages";   keyColor = "#bb9af7"; }
        { type = "custom"; format = "───────────────────────────────"; }
        { type = "custom"; format = "─────────── Challenge ───────────"; }
        {
          type = "command";
          key = " Challenge";
          keyColor = "#e0af68";
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

  xdg.configFile."fastfetch/roudix.txt".source = "${dotfiles}/fastfetch/roudix.txt";

  # Launch fastfetch on every interactive fish shell
  xdg.configFile."fish/conf.d/fastfetch.fish" = {
    text = ''
      fastfetch
    '';
  };
}
