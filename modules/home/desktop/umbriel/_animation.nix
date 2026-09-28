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
##   "sakura-roudix"    — the same suite recolored to Catppuccin Mocha + Peach.
##                        Colors are baked into the shaders at build time
##                        (see `mocha` below), so it doesn't need Noctalia's
##                        palette and stays the same whatever the wallpaper.
##
## Docs: https://docs.noctalia.dev/umbriel/animation/
{ lib, pkgs, osConfig, ... }:
let
  setup = osConfig.roudix.umbriel.effects or "roudix";

  # ── sakura-roudix: Catppuccin Mocha, Peach accent ─────────────────────────
  # The Sakura shaders read 4 palette slots through umbriel_palette_at():
  #   0.0 → primary (was "blush")   0.25 → secondary (was "fuchsia")
  #   0.5 → warm accent (was "gold") 0.75 → strong accent (was "rose")
  # plus a very dark base (`vine_wine`, mixed into the rose for shadows).
  # Edit the hex values here to recolor; rebuild to apply.
  mocha = {
    primary   = "fab387"; # Peach
    secondary = "cba6f7"; # Mauve
    warm      = "f9e2af"; # Yellow
    strong    = "f38ba8"; # Red
    base      = "11111b"; # Crust
  };

  hexVec3 = hex:
    let ch = i: toString (lib.fromHexString (builtins.substring i 2 hex) / 255.0);
    in "vec3(${ch 0}, ${ch 2}, ${ch 4})";

  recolor = text: builtins.replaceStrings
    [
      "umbriel_palette_at(0.0).rgb"  "umbriel_palette_at(0.25).rgb"
      "umbriel_palette_at(0.5).rgb"  "umbriel_palette_at(0.75).rgb"
      "umbriel_palette_at(0.0)"      "umbriel_palette_at(0.25)"
      "umbriel_palette_count > 0"
      "vec3(0.035, 0.008, 0.028)"
    ]
    [
      (hexVec3 mocha.primary)  (hexVec3 mocha.secondary)
      (hexVec3 mocha.warm)     (hexVec3 mocha.strong)
      "vec4(${hexVec3 mocha.primary}, 1.0)" "vec4(${hexVec3 mocha.secondary}, 1.0)"
      "true"
      (hexVec3 mocha.base)
    ]
    text;

  sakuraSrc  = ./_effects/sakura-overdrive;
  sakuraGlsl = builtins.attrNames
    (lib.filterAttrs (n: t: t == "regular" && lib.hasSuffix ".glsl" n) (builtins.readDir sakuraSrc));

  # Same directory layout as sakura-overdrive (effect.toml + relative shaders),
  # with the palette calls replaced by the constants above. Preset names are
  # unchanged, which is fine: only one effects setup is loaded at a time.
  sakuraRoudixEffects = pkgs.runCommand "umbriel-sakura-roudix-effects" { } ''
    mkdir -p $out
    cp ${sakuraSrc}/effect.toml ${sakuraSrc}/LICENSE-Barrulus-MIT.txt $out/
    ${lib.concatMapStringsSep "\n" (f:
      "cp ${pkgs.writeText f (recolor (builtins.readFile (sakuraSrc + "/${f}")))} $out/${f}") sakuraGlsl}
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
  // lib.optionalAttrs (selected ? effects) { inherit (selected) effects; };
}
