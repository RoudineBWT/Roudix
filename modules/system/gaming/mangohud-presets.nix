# Niveaux de l'overlay MangoHud : une seule source de vérité, lue par
#   - modules/system/gaming/gaming.nix       (option roudix.gaming.mangohud.defaultPreset)
#   - modules/system/gaming/gamescope-session.nix (niveau de départ en Gaming Mode)
#   - modules/home/theming/mangohud.nix      (presets.conf + ordre du raccourci)
#
# Les numéros sont ceux des presets natifs de MangoHud, donc ceux que le réglage
# « Performance overlay » de Steam sélectionne en Gaming Mode (0 = caché ... 4 = complet).
{
  ids = {
    off      = 0; # overlay caché
    fps      = 1; # FPS seulement
    compact  = 2; # barre horizontale (CPU/GPU/RAM/VRAM + frametime)
    extended = 3; # + températures, puissances, fréquences
    full     = 4; # tout
  };
}
