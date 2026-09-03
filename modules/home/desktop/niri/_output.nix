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

    workspaces = {
      "${ws.web}"      = { open-on-output = legion; };
      "${ws.code}"     = { open-on-output = legion; };
      "${ws.chat}"     = { open-on-output = hkc; };
      "${ws.term}"     = { open-on-output = legion; };
      "${ws.games}"    = {
        open-on-output = legion;
        # Nouveau (niri 25.11) : override de layout par workspace nommé.
        # Pas de gap sur le workspace jeux — Steam/Heroic/PrismLauncher/
        # Minecraft s'y ouvrent déjà maximisés ou en plein écran (voir
        # _rules-*.nix), un gap visible en jeu n'a pas de sens ici.
        layout.gaps = 0;
      };
      "${ws.files}"    = { open-on-output = legion; };
      "${ws.music}"    = { open-on-output = hkc; };
      "${ws.browser2}" = { open-on-output = hkc; };
    };
  };
}
