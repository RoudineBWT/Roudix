{ inputs, lib, osConfig, ... }:
let
  # ── Zen Browser variant ────────────────────────────────────────────────
  # `homeModules.<n>` bakes the channel in at import time (it can't be
  # switched via a config option inside `programs.zen-browser`), so we pick
  # which HM module to import based on `roudix.zen.variant`. Options
  # declared in modules/system/apps/browser/browser.nix
  zenVariant = osConfig.roudix.zen.variant or "twilight";
  zenHomeModules = {
    beta     = inputs.zen-browser.homeModules.beta;
    twilight = inputs.zen-browser.homeModules.twilight;
  };

  # ── Zen tweaks (roudix.zen.tweaks.*) ───────────────────────────────────
  # user.js prefs come from ./zen-prefs.nix, policies from ./zen-policies.json
  tw       = osConfig.roudix.zen.tweaks;
  zenPrefs = import ./zen-prefs.nix;

  tweakCats = [ "base" ]
    ++ lib.optional tw.performance         "performance"
    ++ lib.optional tw.privacy             "privacy"
    ++ lib.optional tw.disableSafeBrowsing "safebrowsing"
    ++ lib.optional tw.ui                  "ui";
  selected = map (c: zenPrefs.${c}) tweakCats;

  # Later categories win on a (never expected) duplicate name.
  tweakPrefs  = lib.foldl' (acc: c: acc // c.prefs) { } selected;
  lockedNames = lib.concatMap (c: c.locked) selected;

  # Prefixes accepted by Firefox's `Preferences` policy — anything else is
  # rejected (error in the console), so locked prefs outside this list stay
  # user.js-only. (telemetry/studies are covered by DisableTelemetry etc.)
  policyPrefixes = [
    "accessibility." "apz.overscroll." "browser." "datareporting.policy."
    "dom." "extensions." "general.autoScroll" "general.smoothScroll" "geo."
    "gfx." "javascript." "layers." "layout." "mathml." "media." "network."
    "places." "pdfjs." "print." "privacy." "security." "services.sync."
    "signon." "spellchecker." "ui." "widget."
  ];
  policyPrefs = lib.listToAttrs (map
    (n: lib.nameValuePair n { Value = tweakPrefs.${n}; Status = "locked"; })
    (lib.filter (n: lib.any (p: lib.hasPrefix p n) policyPrefixes) lockedNames));

  tweakPolicies =
    (builtins.fromJSON (builtins.readFile ./zen-policies.json)).policies
    // { Preferences = policyPrefs; };
in
{
  imports = [
    # Zen Browser HM module — imported unconditionally (lazy), only builds
    # anything when `programs.zen-browser.enable` is actually true below.
    # Which channel gets imported is driven by `roudix.zen.variant`.
    zenHomeModules.${zenVariant}
  ]
  # Widevine CDM pointer for Helium (DRM playback), only when helium is
  # actually one of the selected browsers.
  ++ lib.optional (lib.elem "helium" osConfig.roudix.browsers) ./helium-widevine.nix;

  # Note: Zen Browser is not added as a raw home.packages entry — see
  # `programs.zen-browser` below, driven by `osConfig.roudix.zen.*`.
  programs.zen-browser = lib.mkIf osConfig.roudix.zen.enable {
    enable = true;
    profiles.default = {
      sine = {
        enable = osConfig.roudix.zen.sine.enable;
        mods   = osConfig.roudix.zen.sine.mods;
      };
      mods = lib.mkIf (!osConfig.roudix.zen.sine.enable) osConfig.roudix.zen.mods;

      # user.js — see roudix.zen.tweaks
      settings = lib.mkIf tw.enable (lib.mapAttrs (_: lib.mkDefault) tweakPrefs);
    };

    # policies.json — see roudix.zen.tweaks.policies
    policies = lib.mkIf (tw.enable && tw.policies) tweakPolicies;
  };
}
