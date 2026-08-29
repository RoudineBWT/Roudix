## _rules.nix — Umbriel: [[window_rule]] et [[layer_rule]].
##
## Chaque règle qui matche contribue ses réglages ; en cas de conflit sur
## une même clé, la règle la PLUS BAS dans la liste gagne.
##
## Doc : https://docs.noctalia.dev/umbriel/rules/
{ ... }:
{
  programs.umbriel.settings = {
  window_rule = [
    # Discord / Element : pas d'équivalent "largeur fixe en pixels tuilée"
    # côté Umbriel (default_width n'accepte qu'une fraction) → flottant
    # pour respecter la taille/position d'origine niri à l'identique.
    {
      match.app_id = "^(discord|Element)$";
      default_output = "DP-3";
      default_workspace = 1;
      default_floating = true;
      default_size = [ 1316 1011 ];
      default_position = { x = 0; y = 0; anchor = "top_left"; };
    }
    {
      match.app_id = "^org\\.telegram\\.desktop$";
      default_output = "DP-3";
      default_workspace = 1;
      default_floating = true;
      default_size = [ 555 1011 ];
      default_position = { x = 0; y = 0; anchor = "top_right"; };
    }
    {
      match.app_id = "^com\\.mitchellh\\.ghostty$";
      default_floating = true;
      default_size = [ 1505 755 ];
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
      match.app_id = "^Spotify$";
      default_output = "DP-3";
      default_workspace = 2;
      default_maximize = true;
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
      default_size = [ 1020 900 ];
      blur_popups = false;
    }
    {
      match.app_id = "^dev\\.noctalia\\.UmbrielSharePicker$";
      default_floating = true;
      default_size = [ 800 600 ];
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
