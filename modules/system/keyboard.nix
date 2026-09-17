{ lib, ... }:
{
  # ── Disposition clavier de la session graphique (XKB) ───────────────────
  # `console.keyMap` (voir common.nix) ne couvre que le TTY, AVANT le
  # lancement de la session graphique (niri/hyprland/mangowc/umbriel — GNOME
  # et KDE gèrent leur propre disposition via leur daemon de settings, pas
  # via ces options). Ces deux options pilotent la disposition XKB réelle
  # utilisée dans la session Wayland : greeter (noctalia-greeter) + input
  # du compositeur lui-même.
  options.roudix.keyboardLayout = lib.mkOption {
    type = lib.types.str;
    default = "us";
    example = "be";
    description = ''
      Code de disposition clavier XKB (setxkbmap) pour la session
      graphique : "us", "be", "fr", "de", "ch", "nl", "es", "it", "pt",
      "pl", "ru", "gb", "jp", etc. Indépendant de `console.keyMap`
      (celui-ci reste utilisé pour le TTY uniquement).
    '';
  };

  options.roudix.keyboardVariant = lib.mkOption {
    type = lib.types.str;
    default = "intl";
    example = "";
    description = ''
      Variante XKB associée à `roudix.keyboardLayout` (ex: "intl",
      "nodeadkeys", "bepo", "dvorak", "colemak"...). Chaîne vide pour
      aucune variante (disposition de base).
    '';
  };
}
