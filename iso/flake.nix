{
  description = "Roudix ISO — Live installer with Calamares";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";

      # ──────────────────────────────────────────────────────────────────
      # Overlay : on patche calamares-nixos-extensions pour y injecter
      # notre module "nixos" custom, nos configs, et notre branding.
      # Tout est copié DANS LE STORE (pas dans /etc au runtime), donc
      # Calamares les trouve directement via son search path par défaut
      # (local -> $out/lib/calamares/modules) sans bricolage.
      # ──────────────────────────────────────────────────────────────────
      roudixOverlay = final: prev: {
        calamares-nixos-extensions = prev.calamares-nixos-extensions.overrideAttrs (oldAttrs: {
          postInstall = ''
            ${oldAttrs.postInstall or ""}

            mkdir -p $out/lib/calamares/modules/nixos
            mkdir -p $out/etc/calamares/modules
            mkdir -p $out/share/calamares/branding/roudix

            # Module Python custom "nixos"
            cp ${./patches/calamares-nixos-extensions/modules/nixos/main.py} \
               $out/lib/calamares/modules/nixos/main.py
            cp ${./patches/calamares-nixos-extensions/modules/nixos/module.desc} \
               $out/lib/calamares/modules/nixos/module.desc

            # settings.conf principal
            cp ${./patches/calamares-nixos-extensions/config/settings.conf} \
               $out/etc/calamares/settings.conf

            # Configs des modules d'instance (packagechooser, users, locale, welcome...)
            cp ${./patches/calamares-nixos-extensions/config/modules/locale.conf} \
               $out/etc/calamares/modules/locale.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/nixos.conf} \
               $out/etc/calamares/modules/nixos.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/welcome.conf} \
               $out/etc/calamares/modules/welcome.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/users.conf} \
               $out/etc/calamares/modules/users.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-desktop.conf} \
               $out/etc/calamares/modules/packagechooser-desktop.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-shell.conf} \
               $out/etc/calamares/modules/packagechooser-shell.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-kernel.conf} \
               $out/etc/calamares/modules/packagechooser-kernel.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-browser.conf} \
               $out/etc/calamares/modules/packagechooser-browser.conf

            # Branding Roudix
            cp ${./patches/calamares-nixos-extensions/branding/roudix/branding.desc} \
               $out/share/calamares/branding/roudix/branding.desc
            cp ${./patches/calamares-nixos-extensions/branding/roudix/show.qml} \
               $out/share/calamares/branding/roudix/show.qml

            # Images : reprises du branding "default" fourni par calamares lui-même
            # (évite de committer des binaires ; remplace par tes propres assets
            #  plus tard en les ajoutant dans patches/calamares-nixos-extensions/branding/roudix/)
            cp ${final.calamares}/share/calamares/branding/default/languages.png \
               $out/share/calamares/branding/roudix/languages.png
            cp ${final.calamares}/share/calamares/branding/default/languages.png \
               $out/share/calamares/branding/roudix/logo.png
          '';
        });

        # Fix autostart Calamares pour Wayland : pkexec strip les variables
        # d'environnement Wayland, on utilise sudo --preserve-env à la place.
        # (nixos est wheel + NOPASSWD + SETENV sur le LiveCD -> transparent)
        makeAutostartItem = args:
          if args.name or "" == "calamares" then
            final.writeTextFile {
              name = "autostart-calamares";
              destination = "/etc/xdg/autostart/calamares.desktop";
              text = ''
                [Desktop Entry]
                Type=Application
                Version=1.0
                Name=Install Roudix
                GenericName=System Installer
                TryExec=calamares
                Exec=sh -c "sudo --preserve-env=WAYLAND_DISPLAY,XDG_RUNTIME_DIR,DISPLAY,QT_QPA_PLATFORM calamares"
                Comment=Calamares — Roudix Installer
                Icon=calamares
                Terminal=false
                StartupNotify=true
                Categories=Qt;System;
                X-AppStream-Ignore=true
              '';
            }
          else
            prev.makeAutostartItem args;
      };

    in
    {
      nixosConfigurations.roudix-iso = nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [
          "${nixpkgs}/nixos/modules/installer/cd-dvd/installation-cd-graphical-calamares-gnome.nix"
          "${nixpkgs}/nixos/modules/installer/cd-dvd/channel.nix"
          { nixpkgs.overlays = [ roudixOverlay ]; }
          ./iso-configuration.nix
        ];
      };

      packages.x86_64-linux.iso =
        self.nixosConfigurations.roudix-iso.config.system.build.isoImage;
    };
}
