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
      style = "none"; # shader remplace popin/scale ci-dessous
      # "${...}" force la coercition path → string : Nix copie le .glsl dans
      # le store et umbriel reçoit un chemin absolu tout fait (pas de
      # xdg.configFile à maintenir en plus, pas de résolution relative à
      # ~/.config/umbriel/ à garder en tête).
      shader = "${./_shaders/windows-in.glsl}";
    };

    windows_out = {
      enabled = true;
      duration_ms = 150;
      curve = "easeout";
      style = "fade"; # ignoré tant que shader est renseigné, gardé en fallback
      shader = "${./_shaders/windows-out.glsl}";
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

    # S'applique aux 3 scratchpads nommés (misc/communication/music, voir
    # _binds.nix et _rules.nix) : petit fondu + assombrissement du fond,
    # sans forcer de taille/état.
    scratchpad = {
      enabled = true;
      duration_ms = 200;
      curve = "easeout";
      shader = "${./_shaders/scratchpad.glsl}"; # slide+fade, cf. _shaders/scratchpad.glsl
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
