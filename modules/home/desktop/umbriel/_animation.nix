## _animation.nix — Umbriel: [animation] and its per-event sub-tables.
##
## niri has no equivalent granular animation system, so these settings
## are Umbriel-specific, chosen to be subtle and consistent with each other.
##
## Docs: https://docs.noctalia.dev/umbriel/animation/
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
      style = "none"; # the shader below replaces popin/scale
      # "${...}" forces path → string coercion: Nix copies the .glsl into
      # the store and umbriel gets a ready-made absolute path.
      shader = "${./_shaders/windows-in.glsl}";
    };

    windows_out = {
      enabled = true;
      duration_ms = 150;
      curve = "easeout";
      style = "fade"; # ignored while shader is set, kept as a fallback
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

    # Applies to the 3 named scratchpads (misc/communication/music, see
    # _binds.nix and _rules.nix): a small fade + background dim, without
    # forcing size/state.
    scratchpad = {
      enabled = true;
      duration_ms = 200;
      curve = "easeout";
      shader = "${./_shaders/scratchpad.glsl}"; # slide+fade, see _shaders/scratchpad.glsl
      dim = 0.5;
      blur = true;
      scale = 0.0;        # 0 = keep the window's remembered geometry
      maximize = false;
      fullscreen = false;
    };

    border = {
      enabled = true;
      duration_ms = 150;
      curve = "easeout";
    };

    # No niri equivalent: slightly dims unfocused windows to reinforce
    # the current focus visually.
    dim_unfocused = {
      enabled = false;
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
