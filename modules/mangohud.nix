{ ... }:
{
  # ── MangoHud ─────────────────────────────────────────────────────────────
  # On utilise xdg.configFile pour préserver l'ordre des options
  # (programs.mangohud.settings trie les clés alphabétiquement)
  programs.mangohud.enable = true;

  xdg.configFile."MangoHud/MangoHud.conf".text = ''
    legacy_layout=false
    custom_text=Roudix
    gpu_stats
    gpu_load_change
    gpu_temp
    gpu_core_clock
    vram
    gpu_mem_clock
    gpu_text=RX 7900 XT
    gpu_color=a51d2d
    gpu_load_value=60,90
    gpu_load_color=92e79a,ffaa7f,cc0000
    cpu_stats
    cpu_load_change
    cpu_temp
    cpu_mhz
    cpu_text=I5 13600KF
    cpu_color=2e97cb
    cpu_load_value=60,90
    cpu_load_color=92e79a,ffaa7f,cc0000
    ram
    ram_color=c26693
    fps
    fps_metrics=avg,0.01
    fps_limit_method=early
    fps_limit=120,,
    fps_value=30,60
    fps_color=cc0000,ffaa7f,92e79a
    frame_timing
    histogram
    frametime_color=00ff00
    time
    winesync
    wine_color=eb5b5b
    engine_short_names
    engine_color=eb5b5b
    text_outline=0
    text_color=ffffff
    media_player_color=ffffff
    media_player_format={title};{artist};{album}
    network_color=e07b85
    battery_color=92e79a
    horizontal_separator_color=ffffff
    vram_color=ad64c1
    background_color=000000
    background_alpha=0.1
    horizontal
    horizontal_stretch=0
    round_corners=10
    position=top-left
    table_columns=4
    toggle_hud=Shift_R+F12
    toggle_hud_position=Shift_R+F11
    toggle_logging=Shift_L+F2
    toggle_fps_limit=Shift_L+F1
    font_file=/run/current-system/sw/share/X11/fonts/IosevkaNerdFont-Bold.ttf
    font_glyph_ranges=korean, chinese, chinese_simplified, japanese, cyrillic, thai, vietnamese, latin_ext_a, latin_ext_b
  '';
}
