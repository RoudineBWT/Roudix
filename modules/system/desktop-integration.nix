{ lib, ... }:
{
  options.roudix.desktopIntegration = lib.mkOption {
    type = lib.types.enum [ "gnome" "kde" ];
    default = "gnome";
    description = ''
      Stack de keyring + xdg-desktop-portal utilisée par les compositeurs
      "bruts" (niri, hyprland, mangowc, umbriel) qui n'ont pas de DE complet
      fournissant nativement leur propre stack. Sans effet quand
      roudix.desktop.type est "gnome" ou "kde" : ces DE gardent toujours
      leur intégration native respective.

      "gnome"  → gnome-keyring + xdg-desktop-portal-gtk/-gnome (défaut).
      "kde"    → KWallet + xdg-desktop-portal-kde. Utile si tu utilises
                 surtout des applis Qt/KDE (Dolphin, etc.) sur un
                 compositeur qui n'est ni GNOME ni KDE.

      ⚠ Sur les compositeurs qui utilisent greetd (le cas par défaut,
      via noctalia-greeter), l'auto-unlock KWallet au login a une
      limitation connue côté nixpkgs (le service PAM "greetd" ne
      substack pas "login" — nixpkgs#357201). À vérifier après un
      rebuild ; si le wallet reste verrouillé, voir les commentaires
      dans modules/system/desktop/*.nix pour le contournement.
    '';
  };
}
