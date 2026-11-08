{ lib, osConfig, ... }:
let
  mangoPresets = import ../../system/gaming/mangohud-presets.nix;
  defaultPreset = mangoPresets.ids.${osConfig.roudix.gaming.mangohud.defaultPreset};

  # Shift_R+F10 (toggle_preset) parcourt cette liste dans l'ordre et démarre sur
  # son premier élément : on fait tourner 0..4 pour que le défaut passe en tête.
  all = [ 0 1 2 3 4 ];
  presetOrder = lib.concatMapStringsSep "," toString
    ((lib.drop defaultPreset all) ++ (lib.take defaultPreset all));

  # ── Pourquoi tout est dans presets.conf et pas dans MangoHud.conf ──────────
  # MangoHud applique le preset PUIS relit MangoHud.conf par-dessus : toute
  # option d'affichage (gpu_stats, horizontal, table_columns...) mise dans
  # MangoHud.conf écraserait le niveau choisi, et tous les niveaux se
  # ressembleraient. MangoHud.conf ne garde donc que les raccourcis et le
  # limiteur de FPS ; le style vit dans chaque [preset N] de presets.conf.
  # En Gaming Mode, Steam réécrit son propre fichier de config
  # (MANGOHUD_CONFIGFILE) mais presets.conf reste lu : le style suit.
  #
  # Chaque niveau est une liste explicite d'éléments (voir fpsOnly, normalPreset,
  # fullPreset, horizontalPreset) suivie de l'apparence (style, fpsLook, hwLook).

  style = ''
    text_color=EADBC8
    text_outline=0
    background_color=14100D
    background_alpha=0.1
    round_corners=10
    position=top-left
    horizontal_separator_color=A8978A
    media_player_color=EADBC8
    media_player_format={title};{artist};{album}
    network_color=7FB5A0
    battery_color=A8B86A
    font_file=/run/current-system/sw/share/X11/fonts/IosevkaNerdFont-Bold.ttf
    font_glyph_ranges=korean, chinese, chinese_simplified, japanese, cyrillic, thai, vietnamese, latin_ext_a, latin_ext_b
  '';

  # ── Niveaux 1, 3 et 4 : construits EXACTEMENT comme le niveau 2 ─────────────
  # (listes d'options explicites, pas d'`inherit`, pas de `control=mangohud` ni de
  # lignes fsr/nis_steam_sharpness : c'est ce montage qui fonctionne pour le
  # niveau 2). Seule la liste d'éléments change, calquée sur les presets
  # MangoApp. Layout non-legacy : l'ordre des lignes = l'ordre d'affichage,
  # donc l'heure en haut (niveaux 3 et 4) et « Powered By Roudix » en dernier.

  # Niveau 1 : FPS seul.
  fpsOnly = ''
    legacy_layout=false
    frame_timing=0
    cpu_stats=0
    gpu_stats=0
    fps
    fps_only
    width=40
    frametime=0
  '';

  # Niveau 3 : preset « normal » de MangoApp + éléments propres à ton horizontal.
  normalPreset = ''
    legacy_layout=false
    time
    gpu_stats
    gpu_temp
    gpu_power
    gpu_name
    cpu_stats
    cpu_temp
    cpu_power
    ram
    vram
    io_read
    io_write
    arch
    wine
    battery
    fps
    fps_metrics=avg,0.01
    frametime
    frame_timing
    winesync
    cpu_mhz
    gpu_core_clock
    gpu_mem_clock
    custom_text=Powered By Roudix
  '';

  # Niveau 4 : équivalent explicite de `full` (on évite `full` pour garder le
  # même montage que le niveau 2).
  fullPreset = ''
    legacy_layout=false
    time
    version
    gpu_stats
    gpu_temp
    gpu_core_clock
    gpu_mem_clock
    gpu_power
    gpu_fan
    gpu_name
    cpu_stats
    cpu_temp
    cpu_mhz
    cpu_power
    core_load
    ram
    vram
    swap
    procmem
    io_read
    io_write
    battery
    fan
    fps
    fps_metrics=avg,0.01
    frametime
    frame_timing
    frame_count
    arch
    wine
    winesync
    custom_text=Powered By Roudix
  '';

  fpsLook = ''
    fps_color=E85D4A,FF8C42,A8B86A
    fps_value=30,60
  '';

  hwLook = ''
    gpu_text=RX 7900 XT
    gpu_color=E5604D
    gpu_load_change
    gpu_load_value=60,90
    gpu_load_color=A8B86A,FF8C42,E85D4A
    cpu_text=I5 13600KF
    cpu_color=7FA3B5
    cpu_load_change
    cpu_load_value=60,90
    cpu_load_color=A8B86A,FF8C42,E85D4A
    ram_color=C98FA6
    vram_color=E0A9BE
    frametime_color=C2D283
    wine_color=F07A68
    engine_color=F07A68
    engine_short_names
  '';

  # Niveau 2 (« horizontal » dans Steam) : ta config d'origine, telle quelle, SANS
  # `inherit`. Le preset natif horizontal ajouterait hud_no_margin et son propre
  # jeu d'éléments ; ici on veut exactement ta liste (barre horizontale à
  # 4 colonnes avec températures, fréquences, VRAM, frametime + histogramme...).
  # Les raccourcis, fps_limit, vsync restent dans MangoHud.conf.
  horizontalPreset = ''
    legacy_layout=false
    custom_text=Powered By Roudix
    gpu_stats
    gpu_load_change
    gpu_temp
    gpu_core_clock
    vram
    gpu_mem_clock
    gpu_text=RX 7900 XT
    gpu_color=E5604D
    gpu_load_value=60,90
    gpu_load_color=A8B86A,FF8C42,E85D4A
    cpu_stats
    cpu_load_change
    cpu_temp
    cpu_mhz
    cpu_text=I5 13600KF
    cpu_color=7FA3B5
    cpu_load_value=60,90
    cpu_load_color=A8B86A,FF8C42,E85D4A
    ram
    ram_color=C98FA6
    fps
    fps_metrics=avg,0.01
    fps_value=30,60
    fps_color=E85D4A,FF8C42,A8B86A
    frame_timing
    histogram
    frametime_color=C2D283
    time
    winesync
    wine_color=F07A68
    engine_short_names
    engine_color=F07A68
    text_outline=0
    text_color=EADBC8
    media_player_color=EADBC8
    media_player_format={title};{artist};{album}
    network_color=7FB5A0
    battery_color=A8B86A
    horizontal_separator_color=A8978A
    vram_color=E0A9BE
    background_color=14100D
    background_alpha=0.1
    horizontal
    horizontal_stretch=0
    round_corners=10
    position=top-left
    table_columns=4
    font_file=/run/current-system/sw/share/X11/fonts/IosevkaNerdFont-Bold.ttf
    font_glyph_ranges=korean, chinese, chinese_simplified, japanese, cyrillic, thai, vietnamese, latin_ext_a, latin_ext_b
  '';
in
{
  programs.mangohud.enable = true;

  # xdg.configFile conserve l'ordre des lignes
  # (programs.mangohud.settings trie les clés par ordre alphabétique)
  xdg.configFile."MangoHud/MangoHud.conf".text = ''
    preset=${presetOrder}
    toggle_preset=Shift_R+F10
    toggle_hud=Shift_R+F12
    toggle_hud_position=Shift_R+F11
    toggle_logging=Shift_L+F2
    toggle_fps_limit=Shift_L+F1
    fps_limit_method=early
    fps_limit=240,165,120,60,30
    vsync=0
    gl_vsync=-1
  '';

  xdg.configFile."MangoHud/presets.conf".text = ''
    [preset 0]
    no_display

    [preset 1]
    ${fpsOnly}
    ${style}
    ${fpsLook}
    [preset 2]
    ${horizontalPreset}
    [preset 3]
    ${normalPreset}
    ${style}
    ${fpsLook}
    ${hwLook}
    [preset 4]
    ${fullPreset}
    ${style}
    ${fpsLook}
    ${hwLook}
  '';
}
