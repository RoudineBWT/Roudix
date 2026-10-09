// vignette.glsl — screen. Very light darkening of the corners. OPT-IN: not
// selected by any setup. Static, but a screen effect disables direct scanout
// on the output (bad for fullscreen games) — see the note in effect.toml.
// Original work for Roudix. Tuning: STRENGTH (0..1), START/END (distance from
// the centre in UV units, corners are ~0.71).

const float STRENGTH = 0.14;
const float START    = 0.35;
const float END      = 0.80;

vec4 screen(vec2 uv) {
    vec4 s = umbriel_sample(uv);
    float v = smoothstep(START, END, length(uv - 0.5));
    return vec4(s.rgb * (1.0 - STRENGTH * v), s.a);
}
