## _rules.nix — Umbriel: [[window_rule]] et [[layer_rule]].
##
## Chaque règle qui matche contribue ses réglages ; en cas de conflit sur
## une même clé, la règle la PLUS BAS dans la liste gagne.
##
## Fix (validate : "unknown key window_rule.default_size") : `default_size`
## (taille flottante en pixels) a été retiré au profit de deux clés
## distinctes plus explicites — `default_floating_size_px` pour du
## pixel-perfect (ce qu'on utilise ci-dessous, comportement identique à
## l'ancien default_size), ou `default_floating_size` pour une taille en
## fraction de la zone utilisable (mieux si tu changes souvent de
## résolution). Contrairement à l'ancien `default_size = [w, h]` (tableau),
## la nouvelle clé attend une TABLE : `{ width = <int>; height = <int>; }`
## (confirmé par un 2e passage de `umbriel validate`, qui a d'abord accepté
## le nom de la clé puis rejeté le tableau — "expected { width = integer,
## height = integer }"). Source du renommage : PR "Default Size Refactor"
## (noctalia-dev/umbriel#229) — le README de la page Window Rules de la doc
## (docs.noctalia.dev/umbriel/window-rules/) n'a pas encore été régénéré
## avec ce changement au moment où j'écris ceci (17/09), d'où le fait qu'il
## montre encore l'ancien `default_size = [w, h]` : ton binaire umbriel
## (suivant `main` du flake) est plus à jour que cette page précise de la
## doc.
##
## Doc : https://docs.noctalia.dev/umbriel/window-rules/
{ ... }:
{
  programs.umbriel.settings = {
  # Test de l'approche rebizzz/nixos : Discord+Telegram → scratchpad
  # "communication", Spotify → "music". "misc" reprend ton scratchpad ad
  # hoc d'origine (voir _binds.nix). Déclarer NE SERAIT-CE QU'UN seul
  # scratchpad nommé désactive l'implicite "default" pour tout le monde —
  # d'où "misc" pour ne rien perdre du "j'envoie n'importe quoi, quand je
  # veux".
  scratchpad = [
    { name = "misc"; }
    { name = "communication"; }
    { name = "music"; }
  ];

  window_rule = [
    # Discord / Element : pas d'équivalent "largeur fixe en pixels tuilée"
    # côté Umbriel (default_width n'accepte qu'une fraction) → flottant
    # pour respecter la taille/position d'origine niri à l'identique.
    {
      # Anciennement default_floating = false (tuilé) : un scratchpad flotte
      # toujours, donc la clé n'a plus d'effet — retirée. La taille/position
      # sont conservées pour que Discord+Telegram réapparaissent toujours
      # côte à côte (top_left/top_right) une fois le scratchpad affiché.
      match.app_id = "^(discord|Element)$";
      default_scratchpad = "communication";
      default_output = "DP-3";
      default_workspace = 1;
      default_floating_size_px = { width = 1316; height = 1011; };
      default_position = { x = 0; y = 0; anchor = "top_left"; };
    }
    {
      match.app_id = "^org\\.telegram\\.desktop$";
      default_scratchpad = "communication";
      default_output = "DP-3";
      default_workspace = 1;
      default_floating_size_px = { width = 555; height = 1011; };
      default_position = { x = 0; y = 0; anchor = "top_right"; };
    }
    {
      match.app_id = "^com\\.mitchellh\\.ghostty$";
      default_floating = true;
      default_floating_size_px = { width = 1505; height = 755; };
      blur = true;
    }
    {
      match.app_id = "^firefox$";
      default_output = "DP-1";
      default_workspace = 1;
      default_maximize = true;
    }
    {
      match.title = "^About Mozilla Firefox$";
      default_output = "DP-1";
      default_workspace = 1;
      default_floating = true;
    }
    {
      match.app_id = "^dev\\.zed\\.Zed$";
      default_output = "DP-1";
      default_workspace = 2;
      default_maximize = true;
    }
    {
      match.app_id = "^zen-twilight$";
      default_output = "DP-1";
      default_workspace = 1;
      default_maximize = true;
      opacity = 0.95;
      blur = true;
    }
    {
      match.title = "^About Zen Twilight$";
      default_output = "DP-1";
      default_workspace = 1;
      default_floating = true;
      opacity = 0.95;
      blur = true;
    }
    {
      match.app_id = "^brave-origin-beta$";
      default_output = "DP-1";
      default_workspace = 1;
      default_maximize = true;
    }
    {
      match.app_id = "^steam$";
      default_output = "DP-1";
      default_workspace = 4;
      default_maximize = true;
    }
    {
      match.app_id = "^openrgb$";
      default_output = "DP-1";
      default_workspace = 4;
    }
    {
      match.app_id = "^kitty$";
      default_output = "DP-1";
      default_workspace = 3;
      default_floating = true;
    }
    {
      match.app_id = "^org\\.gnome\\.Ptyxis$";
      default_output = "DP-1";
      default_workspace = 3;
    }
    {
      match.app_id = "^brave-browser$";
      default_output = "DP-3";
      default_workspace = 3;
      default_maximize = true;
    }
    {
      match.app_id = "^steam_app_.*$";
      default_output = "DP-1";
      default_workspace = 4;
      default_fullscreen = true;
      # Bonus jeux : tearing autorisé côté fenêtre (nécessite tearing=true
      # sur l'output DP-1, voir _output.nix). Umbriel ne l'active que si
      # la fenêtre est effectivement plein écran.
      tearing = true;
    }
    {
      match.app_id = "^heroic$";
      default_output = "DP-1";
      default_workspace = 4;
      default_fullscreen = true;
    }
    {
      match.app_id = "^org\\.prismlauncher\\.PrismLauncher$";
      default_output = "DP-1";
      default_workspace = 4;
      default_maximize = true;
    }
    {
      match.app_id = "^Minecraft$";
      default_output = "DP-1";
      default_workspace = 4;
      default_fullscreen = true;
      tearing = true;
    }
    {
      match.app_id = "^firefox$";
      match.title = "^Picture-in-Picture$";
      default_floating = true;
    }
    {
      match.app_id = "^zen$";
      match.title = "^Picture-in-Picture$";
      default_floating = true;
    }
    {
      match.app_id = "^brave$";
      match.title = "^Picture-in-Picture$";
      default_floating = true;
    }
    # Toasts de notification Steam : repris tel quel de l'exemple officiel
    # de la doc (default_focused=false + default_pinned=true), qui règle
    # justement le problème "le toast doit rester visible même par-dessus
    # un jeu plein écran" — absent de ta première traduction.
    {
      match.title = "^notificationtoasts_\\d+_desktop$";
      default_floating = true;
      default_position = { x = 10; y = 10; anchor = "bottom_right"; };
      default_focused = false;
      default_pinned = true;
    }
    {
      match.title = "^Friends List$";
      default_output = "DP-1";
      default_workspace = 4;
      default_floating = true;
    }
    # Dialogues/utilitaires génériques — repris tel quel de l'exemple
    # officiel de la doc (docs.noctalia.dev/umbriel/rules/). S'applique à
    # N'IMPORTE QUEL parent (pas seulement Nautilus) : sélecteurs de
    # fichiers via xdg-desktop-portal, zenity, pavucontrol, calculatrice...
    # Absent de ta config d'origine puisque niri n'a pas de règle globale
    # équivalente aussi générique.
    {
      match.app_id = "^(Emulator|zenity|xdg-desktop-portal|qalculate-gtk|org\\.pulseaudio\\.pavucontrol)$";
      default_floating = true;
    }
    {
      match.title = "^(Open File|Select|Choose a wallpaper|Open Folder|Save As|Library|Choose Where to Download|File Operation Progress|Rename|Copy Files|Move Files|Search Files)";
      default_floating = true;
    }
    {
      # ⚠ Le (?i) insensible à la casse de niri n'est pas confirmé pris en
      # charge par Umbriel (regex ECMAScript, pas de mention de flags dans
      # la doc) : à vérifier si les dialogues en casse mixte sont bien
      # exclus.
      match.app_id = "^org\\.gnome\\.Nautilus$";
      match.title = "^(?!(Open|Open File|Save As|Save File|Enregistrer|Enregistrer Sous|Ouvrir|Choisir un Fichier)$).*$";
      default_output = "DP-1";
      default_workspace = 5;
      default_maximize = true;
    }
    {
      match.app_id = "^org\\.gnome\\.TextEditor$";
      default_output = "DP-1";
      default_workspace = 5;
    }
    {
      # Anciennement default_maximize = true (tuilé plein cadre) : retiré,
      # un scratchpad flotte toujours. default_floating_size en fraction
      # (plutôt que _px comme communication ci-dessus) pour rester correct
      # si tu changes de résolution/moniteur un jour.
      match.app_id = "^Spotify$";
      default_scratchpad = "music";
      default_output = "DP-3";
      default_workspace = 2;
      default_floating_size = { width = 0.8; height = 0.85; };
    }
    {
      match.app_id = "^(com\\.kde\\.easyeffects|com\\.github\\.wwmm\\.easyeffects)$";
      default_output = "DP-3";
      default_workspace = 2;
    }
    # Fenêtres Noctalia — reprises de l'exemple officiel de la doc, absentes
    # de ta traduction d'origine (tu n'avais pas encore ces fenêtres sous
    # niri).
    {
      match.app_id = "^dev\\.noctalia\\.Noctalia$";
      default_floating = true;
      default_floating_size_px = { width = 1020; height = 900; };
      blur_popups = false;
    }
    {
      match.app_id = "^dev\\.noctalia\\.UmbrielSharePicker$";
      default_floating = true;
      default_floating_size_px = { width = 800; height = 600; };
      default_position = { x = 32; y = 32; anchor = "bottom_right"; };
    }
    # Blur global (niri: window-rule global { background-effect { blur true;
    # xray false } }) — blur_ignore_alpha=0.0 reste une approximation de
    # "xray false" (aucune zone transparente non floutée), à valider
    # visuellement.
    {
      blur = true;
      blur_ignore_alpha = 0.0;
    }
  ];

  layer_rule = [
    # Reprend l'exemple officiel Umbriel/Noctalia :
    # https://docs.noctalia.dev/umbriel/rules/#layer-rules
    {
      match.namespace = "^noctalia-(bar-[^\"]+|notification|dock|panel|attached-panel|osd|desktop-widget-[^\"]*)$";
      blur = true;
      blur_ignore_alpha = 0.5;
      blur_popups = true;
    }
    {
      match.namespace = "^noctalia-window-switcher$";
      blur = true;
      blur_ignore_alpha = 0.0;
    }
  ];
  };
}
