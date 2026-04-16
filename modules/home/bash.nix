{ username, osConfig, lib, ... }:
let
  onNiri      = (osConfig.roudix.desktop.type or "") == "niri";
  onHyprland  = (osConfig.roudix.desktop.type or "") == "hyprland";
  onTilingDE  = onNiri || onHyprland;
  shellType           = osConfig.roudix.desktop.shell or "noctalia";
  availableShells     = if onHyprland then "noctalia|dms|caelestia" else "noctalia|dms";
  availableShellsList = if onHyprland then "noctalia, dms, caelestia" else "noctalia, dms";

  fnArgs = { inherit lib onHyprland availableShells availableShellsList; };
  switchFn       = import ./functions/roudix-switch.nix       fnArgs;
  kernelSwitchFn = import ./functions/roudix-kernel-switch.nix fnArgs;
  shellSwitchFn  = import ./functions/roudix-shell-switch.nix  (fnArgs // {
    shellList = availableShellsList;
  });
in
{
  programs.bash = {
    enable = true;
    shellAliases = {
      rebuild  = "nh os switch --accept-flake-config path:$NH_FLAKE";
      update   = "sudo nix flake update --flake $NH_FLAKE && nh os switch --accept-flake-config path:$NH_FLAKE";
      cleanup  = "sudo nix-env --delete-generations +3 --profile /nix/var/nix/profiles/system && sudo nix-collect-garbage";
    } // lib.optionalAttrs (shellType == "noctalia") {
      noctalia-reload  = "pkill -f quickshell; sleep 1; noctalia-shell --no-duplicate & disown";
    } // lib.optionalAttrs (shellType == "dms") {
      dms-reload       = "dms restart";
    } // lib.optionalAttrs (shellType == "caelestia") {
      caelestia-reload = "pkill -f caelestia-shell; sleep 1; caelestia-shell & disown";
    };

    initExtra = switchFn.bash + kernelSwitchFn.bash
      + lib.optionalString onTilingDE shellSwitchFn.bash;
  };
}
