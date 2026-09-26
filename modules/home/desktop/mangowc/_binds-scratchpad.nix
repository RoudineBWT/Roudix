## _binds-scratchpad.nix — MangoWC: scratchpad keybinds.
##
## Mirrors the Umbriel setup (see modules/home/desktop/umbriel/_binds.nix
## and _rules.nix), adapted to MangoWC's model:
##
## - MangoWC's "standard" scratchpad (minimized/toggle_scratchpad/
##   restore_minimized) is a single shared pool for ANY window — this is
##   the equivalent of Umbriel's implicit "default"/"misc" scratchpad, and
##   is always available, independently of roudix.mangowc.scratchpadApps.
##
## - MangoWC's "named" scratchpad (toggle_named_scratchpad) only matches
##   ONE appid/title per bind, unlike Umbriel where several apps can share
##   a single named scratchpad (and a single toggle key). So there is no
##   "communication" group here — Discord, Element and Telegram each get
##   their own key. See _rules-apps.nix for the matching `isnamedscratchpad`
##   windowrule (marks the window; sets its floating size).
##
## Docs: https://github.com/mangowm/mango/wiki/scratchpad
{ osConfig, lib, ... }:
let
  scratchpadApps = osConfig.roudix.mangowc.scratchpadApps or false;
in
{
  wayland.windowManager.mango.settings = {
    bind = [
      # ─── Generic scratchpad pool ("misc") — always available ───
      "SUPER+SHIFT,space,minimized"        # send focused window to the pool
      "SUPER,space,toggle_scratchpad"      # show/hide the whole pool
      "SUPER+CTRL,space,restore_minimized" # restore next window from the pool
      # ⚠ MangoWC has no "focus next in pool" dispatch, unlike Umbriel's
      # Mod+Alt+Space (scratchpad-focus-next) — nothing to bind here.
    ]
    ++ lib.optionals scratchpadApps [
      # ─── Named scratchpads ("communication" apps + "music") ───
      # Format: bind=MOD,KEY,toggle_named_scratchpad,appid,title,command
      # `command` is only used to launch the app when it isn't running yet.
      "SUPER+ALT,D,toggle_named_scratchpad,discord,none,discord"
      "SUPER+ALT,E,toggle_named_scratchpad,Element,none,element-desktop"
      # ⚠ appid match here is a plain string, not the regex used in
      # _rules-apps.nix's windowrule — verify it also catches the Xwayland
      # fallback class "TelegramDesktop" (native Wayland appid used below).
      "SUPER+ALT,T,toggle_named_scratchpad,org.telegram.desktop,none,telegram-desktop"
      "SUPER+ALT,M,toggle_named_scratchpad,spotify,none,spotify"
    ];
  };
}
