{ pkgs, lib, roudixBranding, ... }:

{
  # Expose le dérivé de branding tel quel dans le live env — ne suppose
  # aucun nom de fichier précis à l'intérieur, donc ça ne peut pas casser
  # le build même si la structure de pkgs/roudix-branding change.
  environment.etc."roudix/branding".source = roudixBranding;

  # ── Pour brancher le fond d'écran GNOME une fois les vrais chemins connus ──
  # Vérifie d'abord ce que le dérivé expose réellement :
  #   nix build .#roudix-branding && ls -R result
  # Puis adapte le chemin ci-dessous et décommente :
  #
  # environment.etc."dconf/db/local.d/00-roudix-wallpaper".text = ''
  #   [org/gnome/desktop/background]
  #   picture-uri='file:///etc/roudix/branding/<chemin-réel>.png'
  #   picture-uri-dark='file:///etc/roudix/branding/<chemin-réel>.png'
  # '';
  # dconf.enable = true;

  # ── GRUB / Limine theming ────────────────────────────────────────────────
  # Volontairement pas touché ici — `isoImage.grubTheme = null;` reste dans
  # iso-configuration.nix pour l'instant. À reprendre plus tard.
}
