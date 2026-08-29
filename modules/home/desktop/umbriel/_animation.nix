## _animation.nix — Umbriel: [animation] et ses sous-tables par événement.
##
## ⚠ Cette section n'existait PAS du tout dans ta config.toml traduite
## depuis niri (niri n'a pas de système d'animation aussi granulaire).
## C'est exactement le genre de "ce qui manque" — ajoutée ici from scratch
## avec des réglages sobres et cohérents entre eux.
##
## Doc : https://docs.noctalia.dev/umbriel/animation/
{ ... }:
{
  programs.umbriel.settings = {
  animation = {
    enabled = true;
    duration_ms = 250;
    curve = "easeout";

    windows_in = {
      enabled = true;
      duration_ms = 150;
      curve = "easeout";
      style = "popin";
      scale = 0.85;
    };

    windows_out = {
      enabled = true;
      duration_ms = 150;
      curve = "easeout";
      style = "fade";
    };

    windows_move = {
      enabled = true;
      duration_ms = 250;
      curve = "snappy";
    };

    workspaces = {
      enabled = true;
      duration_ms = 250;
      curve = "easeout";
    };

    overview = {
      enabled = true;
      duration_ms = 250;
      curve = "easeout";
    };

    # Pour le jour où tu utilises les scratchpads (voir _binds.nix) :
    # petit fondu + assombrissement du fond, sans forcer de taille/état.
    scratchpad = {
      enabled = true;
      duration_ms = 200;
      curve = "easeout";
      dim = 0.5;
      blur = true;
      scale = 0.0;        # 0 = garde la géométrie mémorisée de la fenêtre
      maximize = false;
      fullscreen = false;
    };

    border = {
      enabled = true;
      duration_ms = 150;
      curve = "easeout";
    };

    # Nouveau (sans équivalent niri) : assombrit légèrement les fenêtres
    # non-focus pour renforcer visuellement le focus courant.
    dim_unfocused = {
      enabled = true;
      duration_ms = 200;
      curve = "easeout";
      dim = 0.15;
    };

    layers = {
      enabled = true;
      duration_ms = 200;
      curve = "easeout";
    };
  };
  };
}
