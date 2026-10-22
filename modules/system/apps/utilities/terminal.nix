{ config, lib, ... }:
with lib;
let
  terminal = config.roudix.terminal;

  # Konsole ships with Plasma whatever roudix.terminal says, so on KDE it
  # always gets the Roudix look; elsewhere only if it is the chosen terminal.
  konsoleThemed = terminal == "konsole" || config.roudix.desktop.type == "kde";

  # Fixed profile id so the Roudix profile exists on first launch.
  ptyxisProfile = "7b2f1d9e-5c3a-4e8b-9a61-0d4f2c8e7a15";
in
{
  options.roudix.terminal = mkOption {
    type = types.enum [ "ghostty" "kitty" "alacritty" "foot" "wezterm" "ptyxis" "konsole" ];
    default = "ghostty";
    description = "Terminal émulateur par défaut installé et configuré comme terminal principal.";
  };

  config = mkMerge [
    # ── Konsole: Roudix profile as the default ────────────────────────────
    # The colour schemes (RoudixDark / RoudixLight) and Roudix.profile live
    # in roudix-branding (share/konsole, generated from the palette). Konsole
    # looks them up in XDG_DATA_DIRS. DefaultProfile goes in /etc/xdg, i.e.
    # under ~/.config: a default, never an override — once the user picks
    # another profile in Konsole, theirs wins and a rebuild doesn't touch it.
    (mkIf konsoleThemed {
      environment.pathsToLink = [ "/share/konsole" ];
      environment.etc."xdg/konsolerc".text = ''
        [Desktop Entry]
        DefaultProfile=Roudix.profile
      '';
    })

    # ── Ptyxis: Roudix palette on a default profile ───────────────────────
    # Palette file comes from roudix-branding (share/org.gnome.Ptyxis/palettes,
    # light + dark variants). Profile = system dconf default, same approach
    # as gnome.nix: the user's own db wins as soon as they change something.
    (mkIf (terminal == "ptyxis") {
      environment.pathsToLink = [ "/share/org.gnome.Ptyxis" ];
      programs.dconf.enable = true;
      programs.dconf.profiles.user.databases = [
        { settings = {
            "org/gnome/Ptyxis" = {
              default-profile-uuid = ptyxisProfile;
              profile-uuids = [ ptyxisProfile ];
            };
            "org/gnome/Ptyxis/Profiles/${ptyxisProfile}" = {
              label = "Roudix";
              palette = "Roudix";
            };
          };
        }
      ];
    })
  ];
}
