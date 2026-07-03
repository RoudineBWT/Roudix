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

        nativeBuildInputs = [ pkgs.wrapGAppsHook4 pkgs.gobject-introspection ];
        buildInputs = [ pkgs.gtk4 pkgs.libadwaita ];
        propagatedBuildInputs = [
          pkgs.python3Packages.pygobject3
        ];

        # Runtime tools the wizard shells out to.
        makeWrapperArgs = [
          "--prefix PATH : ${pkgs.lib.makeBinPath [
            disko.packages.${system}.disko
            pkgs.parted
            pkgs.util-linux   # lsblk
            pkgs.nixos-install-tools
          ]}"
        ];

        meta.mainProgram = "roudix-installer";
      };

      # Convenience app for `nix run .#` while iterating in a VM.
      apps.${system}.default = {
        type = "app";
        program = "${self.packages.${system}.default}/bin/roudix-installer";
      };
    };
}
