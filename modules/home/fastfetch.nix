{ username, dotfiles, ... }:
{
  # ── Fastfetch ────────────────────────────────────────────────────────────
  programs.fastfetch = {
    enable = true;

    settings = {
      "$schema" = "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json";

      logo = {
        type = "file";
        source = "${dotfiles}/fastfetch/roudix.txt";
        height = 15;
        padding = {
          right = 5;
        };
      };

      display = {
        separator = "  ";
        color = "33";
      };

      modules = [
        { type = "break"; }
        { type = "custom"; format = "─────────── System ───────────"; }
        { type = "os";       key = "󱄅 OS";        keyColor = "33"; }
        { type = "kernel";   key = " Kernel";     keyColor = "33"; }
        { type = "uptime";   key = "󰔟 Uptime";    keyColor = "33"; }
        {
          type = "command";
          key = "󱎫 OS Age";
          keyColor = "33";
          text = "b=$(stat -c %W /); n=$(date +%s); echo $(( (n - b) / 86400 )) days";
        }
        { type = "custom"; format = "────────── Hardware ──────────"; }
        { type = "cpu";    key = " CPU";  showPeCoreCount = true; keyColor = "36"; }
        { type = "gpu";    key = "󰍛 GPU";  keyColor = "36"; }
        { type = "memory"; key = " Memory"; keyColor = "36"; }
        { type = "custom"; format = "────────── Software ─────────"; }
        { type = "wm";       key = "󰇄 Compositor"; keyColor = "33"; }
        { type = "terminal"; key = " Terminal";    keyColor = "33"; }
        { type = "shell";    key = " Shell";       keyColor = "33"; }
        { type = "packages"; key = " Packages";   keyColor = "33"; }
        { type = "custom"; format = "───────────────────────────────"; }
        { type = "custom"; format = "─────────── Challenge ───────────"; }
        {
          type = "command";
          key = " Challenge";
          keyColor = "35";
          text = ''
            start=$(stat -c %W /); end=$((start + 63072000)); now=$(date +%s)
            elapsed=$(( now - start )); total=$(( end - start ))
            pct=$(( elapsed * 100 / total ))
            days_done=$(( elapsed / 86400 )); days_left=$(( (end - now) / 86400 ))
            filled=$(( pct * 20 / 100 )); empty=$(( 20 - filled ))
            bar=$(printf '█%.0s' $(seq 1 $filled 2>/dev/null))$(printf '░%.0s' $(seq 1 $empty 2>/dev/null))
            echo "[$bar] $pct% — $days_done j / 730 j ($days_left restants)"
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
