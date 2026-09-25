# Decky Loader (Steam Deck Plugin Loader), vendored from Jovian-NixOS.
#
# Source: Jovian-Experiments/Jovian-NixOS, pkgs/decky-loader/default.nix at
# e2647dadda77487caba8055556dedde2e0448d83 (development, 2026-09-15,
# decky-loader 3.2.9), unchanged apart from this header and one line of
# trailing whitespace stripped. Vendored instead of
# taking Jovian as an input/tarball: only this one derivation is needed, not
# its overlay (which redefines gamescope/steam/mesa).
#
# Not in cache.nixos.org: compiled locally (pnpm frontend + Python package).
# The pnpmDeps hash below is Jovian's. Their pinned nixpkgs has pnpm_11
# 11.22.0, ours has 11.27.0: if that changes the pnpm store hash, the build
# fails once and prints the correct hash to paste here.
{ lib
, fetchFromGitHub
, nodejs
, pnpm_11
, fetchPnpmDeps
, pnpmConfigHook
, python3
, coreutils
, psmisc
}:
python3.pkgs.buildPythonPackage rec {
  pname = "decky-loader";
  version = "3.2.9";

  src = fetchFromGitHub {
    owner = "SteamDeckHomebrew";
    repo = "decky-loader";
    rev = "v${version}";
    hash = "sha256-XhW+bbsEhWnD/1c3QVHAQz6AAo824b/hbZ1t/VZE1po=";
  };

  pnpmDeps = fetchPnpmDeps {
    fetcherVersion = 4;
    inherit pname version src;
    pnpm = pnpm_11;
    sourceRoot = "${src.name}/frontend";
    hash = "sha256-w4UFsNqy8fYjpQ5jgPRQ4bfVZJb3aitYUsnf4PP8Itc=";
  };

  pyproject = true;

  pnpmRoot = "frontend";

  nativeBuildInputs = [
    nodejs
    pnpm_11
    pnpmConfigHook
  ];

  preBuild = ''
    cd frontend
    pnpm build
    cd ../backend
  '';

  build-system = with python3.pkgs; [
    poetry-core
    poetry-dynamic-versioning
  ];

  dependencies = with python3.pkgs; [
    aiohttp
    aiohttp-cors
    aiohttp-jinja2
    certifi
    multidict
    packaging
    setproctitle
    watchdog
  ];

  makeWrapperArgs = [
    "--prefix PATH : ${lib.makeBinPath [ coreutils psmisc ]}"
  ];

  pythonRelaxDeps = [
    "aiohttp-cors"
    "packaging"
    "watchdog"
  ];

  passthru.python = python3;

  meta = with lib; {
    description = "A plugin loader for the Steam Deck";
    homepage = "https://github.com/SteamDeckHomebrew/decky-loader";
    platforms = platforms.linux;
    license = licenses.gpl2Only;
  };
}
