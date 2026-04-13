{ pkgs, lib, config, ... }:
{
  # Le user greeter a besoin d'un home pour que GTK charge bien le cursor theme
  users.users.greeter = {
    isSystemUser = true;
    group = "greeter";
    home = "/var/lib/greeter";
    createHome = true;
  };

  users.groups.greeter = {};

  # Fichiers de config GTK pour le greeter (cursor + thème)
  systemd.tmpfiles.rules = [
    "d /var/lib/greeter/.config/gtk-3.0 0755 greeter greeter -"
    "d /var/lib/greeter/.config/gtk-4.0 0755 greeter greeter -"
    "d /var/lib/greeter/.local/share/icons 0755 greeter greeter -"

    # Symlink vers capitaine-cursors dans le profil système
    "L+ /var/lib/greeter/.local/share/icons/capitaine-cursors - - - - /run/current-system/sw/share/icons/capitaine-cursors"
  ];

  environment.etc = {
    # GTK 3
    "skel/.config/gtk-3.0/settings.ini".text = ''
      [Settings]
      gtk-cursor-theme-name=capitaine-cursors
      gtk-cursor-theme-size=24
      gtk-theme-name=adw-gtk3-dark
      gtk-icon-theme-name=Papirus-Dark
    '';
  };

  # On écrit directement dans le home du greeter via activation script
  system.activationScripts.greeterGtkConfig = lib.stringAfter [ "users" "groups" ] ''
    install -d -m 755 -o greeter -g greeter /var/lib/greeter/.config/gtk-3.0
    install -d -m 755 -o greeter -g greeter /var/lib/greeter/.config/gtk-4.0

    cat > /var/lib/greeter/.config/gtk-3.0/settings.ini << 'EOF'
[Settings]
gtk-cursor-theme-name=capitaine-cursors
gtk-cursor-theme-size=24
gtk-theme-name=adw-gtk3-dark
gtk-icon-theme-name=Papirus-Dark
EOF
    chown greeter:greeter /var/lib/greeter/.config/gtk-3.0/settings.ini

    cat > /var/lib/greeter/.config/gtk-4.0/settings.ini << 'EOF'
[Settings]
gtk-cursor-theme-name=capitaine-cursors
gtk-cursor-theme-size=24
gtk-theme-name=adw-gtk3-dark
gtk-icon-theme-name=Papirus-Dark
EOF
    chown greeter:greeter /var/lib/greeter/.config/gtk-4.0/settings.ini
  '';
}
