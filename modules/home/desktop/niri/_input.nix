## _input.nix — niri: [input] (identique entre noctalia et dms).
{ osConfig, ... }:
{
  programs.niri.settings.input = {
    keyboard = {
      xkb = {
        layout = osConfig.roudix.keyboardLayout;
        variant = osConfig.roudix.keyboardVariant;
      };
      numlock = true;
    };

    touchpad = {
      tap = true;
      natural-scroll = true;
    };

    mouse.accel-profile = "flat";

    focus-follows-mouse.enable = true;
    workspace-auto-back-and-forth = true;
  };
}
