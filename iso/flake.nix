{
  description = "Roudix ISO — Live installer with Calamares";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";

      # ──────────────────────────────────────────────────────────────────
      # Overlay : on patche calamares-nixos-extensions (PAS calamares lui-
      # même). Le module officiel NixOS installe calamares ET
      # calamares-nixos-extensions côte à côte dans environment.systemPackages.
      # NixOS fusionne tous les paquets installés dans
      # /run/current-system/sw/{bin,lib,share}/ : c'est CE chemin que
      # Calamares utilise réellement comme search path (cf settings.conf
      # -> modules-search inclut /run/current-system/sw/lib/calamares/modules),
      # pas le $out du binaire calamares pris isolément.
      # ──────────────────────────────────────────────────────────────────
      roudixOverlay = final: prev: {
        calamares-nixos-extensions = prev.calamares-nixos-extensions.overrideAttrs (oldAttrs: {
          postInstall = (oldAttrs.postInstall or "") + ''
            mkdir -p $out/lib/calamares/modules/nixos
            mkdir -p $out/etc/calamares/modules
            mkdir -p $out/share/calamares/branding/roudix

            # Module Python custom "nixos"
            cp ${./patches/calamares-nixos-extensions/modules/nixos/main.py} \
               $out/lib/calamares/modules/nixos/main.py
            cp ${./patches/calamares-nixos-extensions/modules/nixos/module.desc} \
               $out/lib/calamares/modules/nixos/module.desc

            # settings.conf principal — écrase celui par défaut
            cp ${./patches/calamares-nixos-extensions/config/settings.conf} \
               $out/etc/calamares/settings.conf

            # Configs des modules d'instance (locale/nixos/welcome/users)
            cp ${./patches/calamares-nixos-extensions/config/modules/locale.conf} \
               $out/etc/calamares/modules/locale.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/nixos.conf} \
               $out/etc/calamares/modules/nixos.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/welcome.conf} \
               $out/etc/calamares/modules/welcome.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/users.conf} \
               $out/etc/calamares/modules/users.conf

            # Configs des instances packagechooser (matériel, logiciels, extras)
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-gpu.conf} \
               $out/etc/calamares/modules/packagechooser-gpu.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-nvidialaptop.conf} \
               $out/etc/calamares/modules/packagechooser-nvidialaptop.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-cpu.conf} \
               $out/etc/calamares/modules/packagechooser-cpu.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-vmguest.conf} \
               $out/etc/calamares/modules/packagechooser-vmguest.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-kernel.conf} \
               $out/etc/calamares/modules/packagechooser-kernel.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-browser.conf} \
               $out/etc/calamares/modules/packagechooser-browser.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-bravevariant.conf} \
               $out/etc/calamares/modules/packagechooser-bravevariant.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-zen.conf} \
               $out/etc/calamares/modules/packagechooser-zen.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-desktop.conf} \
               $out/etc/calamares/modules/packagechooser-desktop.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-shell.conf} \
               $out/etc/calamares/modules/packagechooser-shell.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-shelldefault.conf} \
               $out/etc/calamares/modules/packagechooser-shelldefault.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-gaming.conf} \
               $out/etc/calamares/modules/packagechooser-gaming.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-gtafix.conf} \
               $out/etc/calamares/modules/packagechooser-gtafix.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-flatpak.conf} \
               $out/etc/calamares/modules/packagechooser-flatpak.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-virtualization.conf} \
               $out/etc/calamares/modules/packagechooser-virtualization.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-autoupdate.conf} \
               $out/etc/calamares/modules/packagechooser-autoupdate.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-autoupdateinterval.conf} \
               $out/etc/calamares/modules/packagechooser-autoupdateinterval.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-bootloader.conf} \
               $out/etc/calamares/modules/packagechooser-bootloader.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-matrix.conf} \
               $out/etc/calamares/modules/packagechooser-matrix.conf
            cp ${./patches/calamares-nixos-extensions/config/modules/packagechooser-waydroid.conf} \
               $out/etc/calamares/modules/packagechooser-waydroid.conf

            # Branding Roudix
            cp ${./patches/calamares-nixos-extensions/branding/roudix/branding.desc} \
               $out/share/calamares/branding/roudix/branding.desc
            cp ${./patches/calamares-nixos-extensions/branding/roudix/show.qml} \
               $out/share/calamares/branding/roudix/show.qml

            # Images : reprises du branding "default" fourni par calamares lui-même
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
