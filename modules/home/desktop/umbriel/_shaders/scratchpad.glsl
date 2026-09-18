// scratchpad.glsl — glisse le scratchpad depuis le bas en s'estompant, au
// lieu du fondu plat par défaut. Idée reprise de rebizzz/nixos
// (default_scratchpad + shader dédié), mais réécrite plus simplement :
// l'original recode sa propre courbe bezier "specialWorkSwitch" en dur dans
// le GLSL (0.05,0.7,0.1,1.0) et ignore donc animation.scratchpad.curve.
// Ici on utilise umbriel_clamped_progress, qui est déjà passé à travers la
// courbe et la durée choisies dans _animation.nix (curve="easeout",
// duration_ms=200) — un seul endroit à retoucher si tu changes le feeling,
// au lieu de deux (le TOML et ce fichier).
//
// Un même shader gère l'apparition ET la disparition (umbriel_direction),
// comme recommandé par la doc pour un shader partagé show/hide :
// https://docs.noctalia.dev/umbriel/animation/#shader-interface

const float slideShare = 0.15;

vec4 animation(vec2 uv) {
    float visible = umbriel_direction > 0.0
        ? umbriel_clamped_progress
        : 1.0 - umbriel_clamped_progress;
    return umbriel_sample(uv - vec2(0.0, slideShare * (1.0 - visible))) * visible;
}
