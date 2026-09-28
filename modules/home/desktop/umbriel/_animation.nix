## _animation.nix — Umbriel: [animation] and its per-event sub-tables.
##
## niri has no equivalent granular animation system, so these settings
## are Umbriel-specific, chosen to be subtle and consistent with each other.
##
## Two selectable effect setups (roudix.umbriel.effects, declared in
## modules/system/desktop/umbriel.nix):
##   "roudix"           — subtle default (_effects/roudix/)
##   "sakura-overdrive" — Ly-sec's full shader suite: animated border, screen
##                        and cursor effects + per-event animations
##                        (_effects/sakura-overdrive/, from Ly-sec/nixos).
##                        Its presets read Umbriel's palette, supplied by the
##                        Noctalia include, so it only looks right on Noctalia.
##   "sakura-roudix"    — the same suite in Catppuccin Mocha + Peach. Same
##                        shaders, but [colors] is set here (see `mocha`
##                        below); values in the main config override the ones
##                        Noctalia's included file provides, so the effects
##                        stay Catppuccin whatever the wallpaper.
##
## Docs: https://docs.noctalia.dev/umbriel/animation/
{ lib, pkgs, osConfig, ... }:
let
  setup = osConfig.roudix.umbriel.effects or "roudix";

  # ── sakura-roudix: Catppuccin Mocha, Peach ────────────────────────────────
  # Presets with `palette = true` read [colors].accent_primary,
  # accent_secondary, warning and error (umbriel_palette_at 0.0/0.25/0.5/0.75).
  # What each slot paints in the Sakura shaders:
  #   accent_primary   ("blush")   petals, cursor, focus glow      → Peach
  #   accent_secondary ("fuchsia") petal rim, glints               → Maroon
  #   warning          ("gold")    flower centers                  → Yellow
  #   error            ("rose")    vine body (branches + leaves)   → Peach
  # The vine body is built from the LAST slot ("rose"), so if it stays red/pink
  # the whole border looks pink even when the petals are Peach.
  mocha = {
    accent_primary   = "#fab387"; # Peach
    accent_secondary = "#eba0ac"; # Maroon
    warning          = "#f9e2af"; # Yellow
    error            = "#fab387"; # Peach (vine body)
  };

  # The shaders also hard-code a dark plum (vec3(0.035, 0.008, 0.028)) that is
  # mixed into the "rose" slot for shadows/branches. Swap it for Catppuccin
  # Crust (#11111b) in a private copy, so "sakura-overdrive" stays untouched.
  crust = "vec3(0.067, 0.067, 0.106)";

  sakuraSrc = ./_effects/sakura-overdrive;

  sakuraRoudixEffects = pkgs.runCommand "umbriel-sakura-roudix-effects" { } ''
    cp -r ${sakuraSrc} $out
    chmod -R u+w $out
    sed -i 's/vec3(0\.035, 0\.008, 0\.028)/${crust}/g' $out/*.glsl
  '';

  # Config shared by both Sakura variants (only the effect.toml differs).
  sakuraCommon = {
    appearance.outer_border_width = 0;
    effects = {
      border = "sakura-vine";
      window = "";
      screen = "sakura-dream";
      cursor = "mahou-twinkle";
      max_fps = 60;
      in_capture = false;
    };
    animation = {
      beziers = {
        window_flow = [ 0.20 0.75 0.25 1.0 ];
      };
      windows_in = {
        effect = "sakura-materialize";
        duration_ms = 620;
        curve = "linear";
      };
      windows_out = {
        effect = "sakura-materialize";
        duration_ms = 500;
        curve = "linear";
      };
      windows_move = {
        duration_ms = 240;
        curve = "window_flow";
        effect = "sakura-rush";
      };
      workspaces.effect = "sakura-shift";
      scratchpad.effect = "magic-summon";
      border = {
        enabled = true;
        duration_ms = 210;
        curve = "linear";
        effect = "sakura-focus";
      };
      windows_drag.physics = true;
    };
  };

  # Every effect.toml is copied to the store with its directory, so the
  # relative `shader = "x.glsl"` paths inside it resolve.
  setups = {
    roudix = {
      files = [ "${./_effects/roudix}/effect.toml" ];
      animation = { };
    };

    sakura-overdrive = sakuraCommon // {
      files = [ "${sakuraSrc}/effect.toml" ];
    };

    sakura-roudix = sakuraCommon // {
      files = [ "${sakuraRoudixEffects}/effect.toml" ];
      colors = mocha;
    };
  };

  selected = setups.${setup} or (throw "unknown roudix.umbriel.effects: ${setup}");

  baseAnimation = {
    enabled = true;
    duration_ms = 250;
    curve = "easeout";

    windows_in = {
      enabled = true;
      duration_ms = 150;
      curve = "easeout";
      effect = "roudix-window-in"; # _effects/roudix/windows-in.glsl (replaces popin)
    };

    windows_out = {
      enabled = true;
      duration_ms = 150;
      curve = "easeout";
      effect = "roudix-window-out"; # _effects/roudix/windows-out.glsl (replaces fade)
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
      effect = "roudix-scratchpad"; # _effects/roudix/scratchpad.glsl (slide+fade)
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
in
{
  programs.umbriel.settings = {
    # Merges with the include list in _include-noctalia.nix.
    include.files = selected.files;
    animation = lib.recursiveUpdate baseAnimation selected.animation;
  }
  // lib.optionalAttrs (selected ? appearance) { inherit (selected) appearance; }
  // lib.optionalAttrs (selected ? effects) { inherit (selected) effects; }
  // lib.optionalAttrs (selected ? colors) { inherit (selected) colors; };
}
