{ osConfig, lib, ... }:
let
  terminalCmd = osConfig.roudix.terminal or "ghostty";
  fileManagerCmd = osConfig.roudix.fileManager or "nautilus";

  # Same "resolved from roudix.*" pattern as niri/umbriel (see
  # umbriel/default.nix) — no lib.mkForce needed here: mango's `bind` is a
  # flat list of "MODS,KEY,ACTION,ARGS" strings, not an attrsOf, so there's
  # no per-key merge to win, just entries to append.
  browserDefault = osConfig.roudix.browser.default or null;
  browserCmd     = osConfig.roudix.browser.command or null;
  browserList    = osConfig.roudix.browser.commands or [ ];
  extraBrowsers  = lib.filter (b: b.name != browserDefault) browserList;
in
{
  wayland.windowManager.mango.settings = {
    bind = [
      "SUPER,Return,spawn,${terminalCmd}"
      "SUPER,E,spawn,${fileManagerCmd}"
      "SUPER+SHIFT,B,spawn,zen-twilight"
      "SUPER,Q,killclient"
      "SUPER,F,togglefullscreen"
      "SUPER,T,togglefloating"
      "SUPER,C,centerwin"

      "SUPER,H,focusdir,left"
      "SUPER,Left,focusdir,left"
      "SUPER,L,focusdir,right"
      "SUPER,Right,focusdir,right"
      "SUPER,K,focusdir,up"
      "SUPER,Up,focusdir,up"
      "SUPER,J,focusdir,down"
      "SUPER,Down,focusdir,down"

      "SUPER+CTRL,H,exchange_client,left"
      "SUPER+CTRL,Left,exchange_client,left"
      "SUPER+CTRL,L,exchange_client,right"
      "SUPER+CTRL,Right,exchange_client,right"
      "SUPER+CTRL,K,exchange_client,up"
      "SUPER+CTRL,Up,exchange_client,up"
      "SUPER+CTRL,J,exchange_client,down"
      "SUPER+CTRL,Down,exchange_client,down"

      "SUPER+SHIFT,Left,focusmon,left"
      "SUPER+SHIFT,Right,focusmon,right"
      "SUPER+SHIFT,Up,focusmon,up"
      "SUPER+SHIFT,Down,focusmon,down"

      "SUPER+SHIFT+CTRL,Left,tagmon,left"
      "SUPER+SHIFT+CTRL,Right,tagmon,right"
      "SUPER+SHIFT+CTRL,Up,tagmon,up"
      "SUPER+SHIFT+CTRL,Down,tagmon,down"

      "SUPER,minus,resizewin,-100,0"
      "SUPER,equal,resizewin,100,0"
      "SUPER+SHIFT,minus,resizewin,0,-100"
      "SUPER+SHIFT,equal,resizewin,0,100"

      "SUPER,1,view,1"
      "SUPER,2,view,2"
      "SUPER,3,view,3"
      "SUPER,4,view,4"
      "SUPER,5,view,5"
      "SUPER,6,view,6"
      "SUPER,7,view,7"
      "SUPER,8,view,8"
      "SUPER,9,view,9"

      "SUPER+CTRL,1,tag,1"
      "SUPER+CTRL,2,tag,2"
      "SUPER+CTRL,3,tag,3"
      "SUPER+CTRL,4,tag,4"
      "SUPER+CTRL,5,tag,5"
      "SUPER+CTRL,6,tag,6"
      "SUPER+CTRL,7,tag,7"
      "SUPER+CTRL,8,tag,8"
      "SUPER+CTRL,9,tag,9"

      "SUPER,Tab,view,-1"
      "SUPER+SHIFT,G,togglegaps"
      "SUPER+SHIFT,minus,incgaps,-5"
      "SUPER+SHIFT,equal,incgaps,5"
      "SUPER+ALT,Space,switch_layout"
      "SUPER+ALT,P,switch_proportion_preset"
      "SUPER+SHIFT,R,reload_config"
      "SUPER+SHIFT,P,toggle_monitor,current"
      "CTRL+ALT,Delete,quit"
    ]
    ++ lib.optional (browserCmd != null) "SUPER,B,spawn,${browserCmd}"
    # Un bind par navigateur roudix.browsers au-delà du défaut (Mod+B) —
    # même principe que le Mod+Ctrl+Alt+N de niri/umbriel. Mod+Shift+B reste
    # câblé sur zen-twilight ci-dessus, indépendamment de cette liste.
    ++ (lib.imap1 (i: b: "SUPER+CTRL+ALT,${toString i},spawn,${b.command}") extraBrowsers);

    mousebind = [
      "SUPER,btn_left,moveresize,curmove"
      "SUPER,btn_right,moveresize,curresize"
    ];

    axisbind = [
      "SUPER,UP,viewtoleft"
      "SUPER,DOWN,viewtoright"
    ];
  };
}
