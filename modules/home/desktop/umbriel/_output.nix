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
      # ⚠ Bug Mod+1..9 : un nom de workspace purement numérique ("4", "5"...)
      # qui n'existe QUE sur cet output devient un nom global unique. La
      # doc (docs.noctalia.dev/umbriel/actions/) précise que les sélecteurs
      # de workspace résolvent d'abord les noms exacts globalement, et
      # qu'un nom unique saute sur SON output -- même si un autre moniteur a
      # le focus. C'était le cas de "4"/"5" côté DP-3 (uniques) : Mod+4 et
      # Mod+5 sautaient toujours sur le HKC. Les "6".."9" préfixés L/H
      # ci-dessous ne sont plus des noms numériques exacts, donc
      # Mod+1..9 retombe systématiquement sur la résolution "position N du
      # moniteur focus" que tu veux, indépendamment par écran.
      workspaces = [ "󰈹" "" "" "󰊗" "󰉋" "L6" "L7" "L8" "L9"  ];
    };

    "DP-3" = { # HKC 24E4, 1920x1080@165
      mode = "1920x1080@165.001";
      position = [ 0 0 ];
      scale = 1;
      workspaces = [ "" "󰝚" "" "H4" "H5" "H6" "H7" "H8" "H9" ];
    };
  };

  # ── Règles de workspace ──────────────────────────────────────────────────
  # Mode global (_layout.nix) : "scrolling". Chaque workspace reçoit ici sa
  # propre règle layout.mode ("scrolling", "dwindle" ou "master").
  #
  # Web (DP-1/1, DP-3/3)      → scrolling
  # Zed (DP-1/2)              → dwindle
  # Term (DP-1/3)             → dwindle
  # Jeux (DP-1/4)             → master
  # Fichiers (DP-1/5)         → dwindle
  # Chat (DP-3/1)             → master
  # Musique (DP-3/2)          → dwindle
  workspace = [
    {
      output = "DP-1";
      index = 1; # web (firefox / zen / brave-origin-beta)
      layout.mode = "scrolling";
    }
    {
      output = "DP-1";
      index = 2; # zed
      layout.mode = "dwindle";
    }
    {
      output = "DP-1";
      index = 3; # term (kitty / ptyxis)
      layout.mode = "dwindle";
    }
    {
      output = "DP-1";
      index = 4; # jeux — pas de gap vu que Steam/Heroic/PrismLauncher/
                 # Minecraft s'ouvrent déjà maximisés ou en plein écran
                 # (voir _rules.nix) — évite un liseré de gap visible en jeu.
      layout.mode = "scrolling";
      layout.gap = 0;
    }
    {
      output = "DP-1";
      index = 5; # fichiers (nautilus / gnome-text-editor)
      layout.mode = "dwindle";
    }
    {
      output = "DP-3";
      index = 1; # chat (discord / element / telegram — déjà en floating
                 # dans _rules.nix, donc le mode n'affecte que ce que tu
                 # ouvrirais en plus en tuilé sur ce workspace)
      layout.mode = "master";
    }
    {
      output = "DP-3";
      index = 2; # musique (spotify / easyeffects)
      layout.mode = "dwindle";
    }
    {
      output = "DP-3";
      index = 3; # web (brave-browser)
      layout.mode = "scrolling";
    }
  ];
  };
}
