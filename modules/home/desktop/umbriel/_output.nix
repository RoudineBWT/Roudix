## _output.nix — Umbriel: [output.NAME] + [[workspace]] (règles par
## workspace).
##
## TODO: lance `umbriel outputs` une fois en session et remplace DP-1/DP-3
## ci-dessous par les vrais noms de connecteur si besoin (ex: DP-1, HDMI-A-1
## — Umbriel veut le nom du connecteur physique, pas "Marque Modèle Série"
## comme niri).
##
## Doc : https://docs.noctalia.dev/umbriel/outputs/
##       https://docs.noctalia.dev/umbriel/workspaces/#workspace-rules
{ ... }:
{
  programs.umbriel.settings = {
  output = {
    "DP-1" = { # Lenovo Legion 27Q-10, 2560x1440@240
      mode = "2560x1440@240.000";
      position = [ 1920 0 ];
      scale = 1;
      vrr = "fullscreen"; # niri: variable-refresh-rate on-demand=true
      # Nouveau (bonus jeux compétitifs) : autorise le tearing asynchrone
      # sur cet output. C'est un "safety gate" : Umbriel ne l'utilise que
      # pour une fenêtre plein écran qui le demande (ou via window_rule
      # tearing=true dans _rules.nix). Retire cette ligne si tu vois du
      # tearing visible en dehors des jeux.
      tearing = true;
      # 5 workspaces nommés, dans l'ordre de ton rules.kdl d'origine :
      workspaces = [ "󰈹" "" "" "󰊗" "󰉋" ];
    };

    "DP-3" = { # HKC 24E4, 1920x1080@165
      mode = "1920x1080@165.001";
      position = [ 0 0 ];
      scale = 1;
      workspaces = [ "" "󰝚" "" ];
    };
  };

  # ── Règles de workspace ──────────────────────────────────────────────────
  # Fonctionnalité sans équivalent niri direct dans ta config d'origine.
  # Ici : pas de gap sur le workspace "jeux" (position 4 sur DP-1), vu que
  # Steam/Heroic/PrismLauncher/Minecraft s'y ouvrent déjà maximisés ou en
  # plein écran (voir _rules.nix) — évite un liseré de gap visible en jeu.
  workspace = [
    {
      output = "DP-1";
      index = 4;
      layout.gap = 0;
    }
  ];
  };
}
