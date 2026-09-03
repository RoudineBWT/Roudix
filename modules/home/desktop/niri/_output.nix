## _output.nix — niri: [output.NAME] + [workspaces] (identique entre
## noctalia et dms).
##
## Noms de connecteur (DP-1/DP-3) plutôt que "Marque Modèle Série" — mêmes
## identifiants que côté Umbriel, cohérent entre les deux compositeurs.
## ⚠ Contrepartie : si tu débranches/rebranches un écran sur un autre port
## DP de la carte, la conf reste attachée au PORT, pas à l'écran physique
## (contrairement au nom complet). Reconfirme avec `niri msg outputs` si
## tu changes de câblage.
{ ... }:
let
  ws = import ./_ws.nix { };
  legion = "DP-1";
  hkc    = "DP-3";
in
{
  programs.niri.settings = {
    outputs = {
      "${hkc}" = {
        mode = { width = 1920; height = 1080; refresh = 165.001; };
        scale = 1.0;
        position = { x = 0; y = 0; };
      };

      "${legion}" = {
        mode = { width = 2560; height = 1440; refresh = 240.000; };
        scale = 1.0;
        position = { x = 1920; y = 0; };
        variable-refresh-rate = "on-demand";
      };
    };

    # ⚠ niri-flake crée les workspaces nommés triés par CLÉ de l'attrset
    # (doc officielle : "Workspaces will be created in a specific order:
    # sorted by key. [...] you can use the key to order them, and a `name`
    # attribute to have a friendlier name."). Comme nos clés étaient
    # directement les glyphes Nerd Font (des codepoints Unicode), l'ordre
    # affiché dans la barre finissait trié par valeur numérique de
    # codepoint — d'où l'ordre incohérent (term, code, web, files, games
    # au lieu de web, code, term, games, files). Fix : la clé devient un
    # préfixe numérique explicite (ordre voulu, par output), et le glyphe
    # réel part dans le champ `name` — c'est `name` qui est utilisé comme
    # nom de workspace niri (donc par _rules-*.nix / _binds-*.nix via
    # `ws.xxx`), la clé ne sert plus qu'à trier.
    workspaces = {
      "1-${ws.web}"   = { name = ws.web; open-on-output = legion; };
      "2-${ws.code}"  = { name = ws.code; open-on-output = legion; };
      "3-${ws.term}"  = { name = ws.term; open-on-output = legion; };
      "4-${ws.games}" = {
        name = ws.games;
        open-on-output = legion;
        # Nouveau (niri 25.11) : override de layout par workspace nommé.
        # Pas de gap sur le workspace jeux — Steam/Heroic/PrismLauncher/
        # Minecraft s'y ouvrent déjà maximisés ou en plein écran (voir
        # _rules-*.nix), un gap visible en jeu n'a pas de sens ici.
        layout.gaps = 0;
      };
      "5-${ws.files}"    = { name = ws.files; open-on-output = legion; };

      "1-${ws.chat}"     = { name = ws.chat; open-on-output = hkc; };
      "2-${ws.music}"    = { name = ws.music; open-on-output = hkc; };
      "3-${ws.browser2}" = { name = ws.browser2; open-on-output = hkc; };
    };
  };
}
