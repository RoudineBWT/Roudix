# Roudix colours for the terminal the user picked (roudix.terminal).
#
# Colours come from assets/palette/Roudix.json (terminal section) through
# roudix.palette (theming/palette.nix). Konsole and Ptyxis are handled at
# system level (modules/system/apps/utilities/terminal.nix + roudix-branding);
# this module covers ghostty, kitty, alacritty, foot and wezterm.
#
# Same philosophy as the KDE / GNOME defaults — never clobber the user:
#   - the THEME FILE is managed by home-manager (updated with the palette);
#   - the main CONFIG FILE is only written if it doesn't exist yet, as a
#     normal editable file that points at the theme. If you already have a
#     config, add the one line shown next to each terminal below.
{ lib, config, osConfig, ... }:

let
  terminal = osConfig.roudix.terminal or "ghostty";
  pal      = config.roudix.palette;
  p        = pal.active;
  t        = p.terminal;
  noHash   = pal.lib.noHash;

  names = [ "black" "red" "green" "yellow" "blue" "magenta" "cyan" "white" ];
  ansiOf = tt: (map (n: tt.normal.${n}) names) ++ (map (n: tt.bright.${n}) names);
  indexed = list: lib.imap0 (i: c: { inherit i c; }) list;
  lines = lib.concatStringsSep "\n";

  # Writes `content` to `path` (relative to $HOME) only if nothing is there yet.
  seed = path: content: ''
    if [ ! -e "$HOME/${path}" ]; then
      mkdir -p "$(dirname "$HOME/${path}")"
      cat > "$HOME/${path}" <<'ROUDIX_SEED_EOF'
    ${content}
    ROUDIX_SEED_EOF
    fi
  '';

  # ── ghostty ──  ~/.config/ghostty/config:  theme = light:RoudixLight,dark:RoudixDark
  ghosttyTheme = pp:
    let tt = pp.terminal; in lines (
      (map (x: "palette = ${toString x.i}=${x.c}") (indexed (ansiOf tt)))
      ++ [
        "background = ${tt.background}"
        "foreground = ${tt.foreground}"
        "cursor-color = ${tt.cursor}"
        "cursor-text = ${tt.cursorText}"
        "selection-background = ${tt.selectionBg}"
        "selection-foreground = ${tt.selectionFg}"
      ]);

  # ── kitty ──  ~/.config/kitty/kitty.conf:  include themes/roudix.conf
  kittyTheme = lines (
    [
      "foreground ${t.foreground}"
      "background ${t.background}"
      "selection_foreground ${t.selectionFg}"
      "selection_background ${t.selectionBg}"
      "cursor ${t.cursor}"
      "cursor_text_color ${t.cursorText}"
    ]
    ++ map (x: "color${toString x.i} ${x.c}") (indexed (ansiOf t)));

  # ── alacritty ──  ~/.config/alacritty/alacritty.toml:
  #   [general]
  #   import = ["~/.config/alacritty/themes/roudix.toml"]
  alacrittyTheme =
    let
      block = set: lines (map (n: "${n} = \"${set.${n}}\"") names);
    in lines [
      "[colors.primary]"
      "foreground = \"${t.foreground}\""
      "background = \"${t.background}\""
      ""
      "[colors.cursor]"
      "text = \"${t.cursorText}\""
      "cursor = \"${t.cursor}\""
      ""
      "[colors.selection]"
      "text = \"${t.selectionFg}\""
      "background = \"${t.selectionBg}\""
      ""
      "[colors.normal]"
      (block t.normal)
      ""
      "[colors.bright]"
      (block t.bright)
    ];

  # ── foot ──  ~/.config/foot/foot.ini:  include=~/.config/foot/themes/roudix.ini
  footTheme =
    let
      section = if config.roudix.palette.mode == "light" then "colors-light" else "colors-dark";
    in lines (
      [
        "[${section}]"
        "foreground=${noHash t.foreground}"
        "background=${noHash t.background}"
        "selection-foreground=${noHash t.selectionFg}"
        "selection-background=${noHash t.selectionBg}"
        "cursor=${noHash t.cursorText} ${noHash t.cursor}"
      ]
      ++ map (x: "regular${toString x.i}=${noHash x.c}") (indexed (map (n: t.normal.${n}) names))
      ++ map (x: "bright${toString x.i}=${noHash x.c}")  (indexed (map (n: t.bright.${n}) names)));

  # ── wezterm ──  ~/.config/wezterm/wezterm.lua:  config.color_scheme = 'Roudix'
  weztermQuote = c: "\"${c}\"";
  weztermTheme = lines [
    "[colors]"
    "foreground = ${weztermQuote t.foreground}"
    "background = ${weztermQuote t.background}"
    "cursor_fg = ${weztermQuote t.cursorText}"
    "cursor_bg = ${weztermQuote t.cursor}"
    "cursor_border = ${weztermQuote t.cursor}"
    "selection_fg = ${weztermQuote t.selectionFg}"
    "selection_bg = ${weztermQuote t.selectionBg}"
    "ansi = [${lib.concatMapStringsSep ", " (n: weztermQuote t.normal.${n}) names}]"
    "brights = [${lib.concatMapStringsSep ", " (n: weztermQuote t.bright.${n}) names}]"
    ""
    "[metadata]"
    "name = \"Roudix\""
  ];
in
{
  config = lib.mkMerge [
    (lib.mkIf (terminal == "ghostty") {
      xdg.configFile."ghostty/themes/RoudixDark".text  = ghosttyTheme pal.dark;
      xdg.configFile."ghostty/themes/RoudixLight".text = ghosttyTheme pal.light;
      home.activation.roudixTerminalSeed = lib.hm.dag.entryAfter [ "writeBoundary" ]
        (seed ".config/ghostty/config" "theme = light:RoudixLight,dark:RoudixDark");
    })

    (lib.mkIf (terminal == "kitty") {
      xdg.configFile."kitty/themes/roudix.conf".text = kittyTheme;
      home.activation.roudixTerminalSeed = lib.hm.dag.entryAfter [ "writeBoundary" ]
        (seed ".config/kitty/kitty.conf" "include themes/roudix.conf");
    })

    (lib.mkIf (terminal == "alacritty") {
      xdg.configFile."alacritty/themes/roudix.toml".text = alacrittyTheme;
      home.activation.roudixTerminalSeed = lib.hm.dag.entryAfter [ "writeBoundary" ]
        (seed ".config/alacritty/alacritty.toml"
          "[general]\nimport = [\"~/.config/alacritty/themes/roudix.toml\"]");
    })

    (lib.mkIf (terminal == "foot") {
      xdg.configFile."foot/themes/roudix.ini".text = footTheme;
      home.activation.roudixTerminalSeed = lib.hm.dag.entryAfter [ "writeBoundary" ]
        (seed ".config/foot/foot.ini" "include=~/.config/foot/themes/roudix.ini");
    })

    (lib.mkIf (terminal == "wezterm") {
      xdg.configFile."wezterm/colors/Roudix.toml".text = weztermTheme;
      home.activation.roudixTerminalSeed = lib.hm.dag.entryAfter [ "writeBoundary" ]
        (seed ".config/wezterm/wezterm.lua"
          "local wezterm = require 'wezterm'\nlocal config = wezterm.config_builder()\nconfig.color_scheme = 'Roudix'\nreturn config");
    })
  ];
}
