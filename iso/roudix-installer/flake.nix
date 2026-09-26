{
  description = "Roudix Installer — GTK4/libadwaita wizard + disko backend";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    disko.url = "github:nix-community/disko";
    disko.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, disko }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in
    {
      packages.${system}.default = pkgs.python3Packages.buildPythonApplication {
        pname = "roudix-installer";
        version = "0.1.0";
        src = ./.;
        format = "pyproject";

        # hicolor-icon-theme's setup hook is what actually runs
        # gtk-update-icon-cache over $out/share/icons/hicolor at build time —
        # without it the icon we copy in postInstall below is on disk but
        # never picked up by icon-name lookups.
        nativeBuildInputs = [
          pkgs.wrapGAppsHook4
          pkgs.gobject-introspection
          pkgs.hicolor-icon-theme
        ];
        buildInputs = [ pkgs.gtk4 pkgs.libadwaita ];
        propagatedBuildInputs = [
          pkgs.python3Packages.pygobject3
        ];

        # PEP 517 backend declared in pyproject.toml — required explicitly,
        # pypaBuildPhase otherwise can't import setuptools.build_meta.
        build-system = [ pkgs.python3Packages.setuptools ];

        # Runtime tools the wizard shells out to.
        makeWrapperArgs = [
          "--prefix PATH : ${pkgs.lib.makeBinPath [
            disko.packages.${system}.disko
            pkgs.parted
            pkgs.util-linux   # lsblk
            pkgs.nixos-install-tools
          ]}"
        ];

        # Ship the app's own hicolor icon (data/icons/hicolor/...) alongside
        # the Python package — buildPythonApplication only installs the
        # importable package by default, so the icon theme tree needs an
        # explicit copy into $out/share for icon lookups (Icon=roudix-installer
        # in the .desktop entries) to resolve.
        postInstall = ''
          mkdir -p $out/share/icons
          cp -r data/icons/hicolor $out/share/icons/
        '';

        meta.mainProgram = "roudix-installer";
      };

      # Convenience app for `nix run .#` while iterating in a VM.
      apps.${system}.default = {
        type = "app";
        program = "${self.packages.${system}.default}/bin/roudix-installer";
      };
    };
}
