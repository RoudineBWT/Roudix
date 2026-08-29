## _output.nix — niri: [output.NAME] + [workspaces] (identique entre
## noctalia et dms).
##
## TODO: lance `niri msg outputs` pour confirmer les noms de connecteur.
{ ... }:
let
  ws = import ./_ws.nix { };
  legion = "Lenovo Group Limited Legion 27Q-10 UNA07260";
  hkc    = "HKC OVERSEAS LIMITED 24E4 0000000000001";
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
        variable-refresh-rate.on-demand = true;
      };
    };

    workspaces = {
      "${ws.web}"      = { open-on-output = legion; };
      "${ws.code}"     = { open-on-output = legion; };
      "${ws.chat}"     = { open-on-output = hkc; };
      "${ws.term}"     = { open-on-output = legion; };
      "${ws.games}"    = { open-on-output = legion; };
      "${ws.files}"    = { open-on-output = legion; };
      "${ws.music}"    = { open-on-output = hkc; };
      "${ws.browser2}" = { open-on-output = hkc; };
    };
  };
}
