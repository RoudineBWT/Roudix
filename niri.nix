{ pkgs, ... }:
{
  # ── Niri + UWSM ─────────────────────────────────────────────────────────
  programs.niri = {
    enable = true;
    # La config est gérée par home-manager (xdg.configFile."niri/config.kdl")
    # donc on ne définit pas settings ici
  };

  programs.uwsm = {
    enable = true;
    waylandCompositors.niri = {
      prettyName = "Niri";
      comment     = "Niri scrollable tiling compositor";
      binPath     = "/run/current-system/sw/bin/niri";
    };
  };
}
