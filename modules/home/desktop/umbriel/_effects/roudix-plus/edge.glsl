// edge.glsl — border (focused window). Fine accent line whose colour drifts
// slowly between accent_primary and accent_secondary, plus a faint outer glow.
// Original work for Roudix (no third-party code).
//
// Palette: reads Umbriel's [colors] (Noctalia/matugen, or Mocha in the
// "roudix-plus-mocha" setup). Falls back to Peach/Maroon without a palette.
// Cost: one atan + one exp per border pixel; animated, so it asks for frames
// (cap with [effects] max_fps, or set `animated = false` in effect.toml for a
// static gradient — time is then frozen at 0).
//
// Tuning (GLSL constants):
//   GLOW_STRENGTH  peak opacity of the outer glow, 0..1
//   GLOW_FALLOFF   glow decay length in logical px (keep <= padding / 3)
//   WAVES          colour lobes around the window — MUST be a whole number
//   DRIFT          rotation speed of the gradient, rad/s (scaled by `speed`)

const float GLOW_STRENGTH = 0.30;
const float GLOW_FALLOFF  = 2.0;
const float WAVES         = 2.0;
const float DRIFT         = 0.5;

vec3 edgeColor(float t) {
    vec3 a = vec3(0.980, 0.702, 0.529); // Peach (fallback)
    vec3 b = vec3(0.922, 0.627, 0.675); // Maroon (fallback)
    if (umbriel_palette_count > 0) {
        a = umbriel_palette_at(0.0).rgb;
        b = umbriel_palette_at(0.25).rgb;
    }
    return mix(a, b, t);
}

vec4 border(vec2 uv) {
    vec4 ring = umbriel_sample(uv);

    // Whole-number sine lobes stay continuous across the atan seam.
    vec2 p = (uv - 0.5) * umbriel_size;
    float angle = atan(p.y, p.x + 1e-4);
    float t = 0.5 + 0.5 * sin(angle * WAVES + umbriel_time * DRIFT);
    vec3 col = edgeColor(t);

    // Signed distance: <0 inside the client, >0 in the ring and the padding.
    float d = max(umbriel_border_distance(uv), 0.0);
    float glow = GLOW_STRENGTH * exp(-d / GLOW_FALLOFF);

    float a = max(ring.a, glow);
    return vec4(col * a, a); // premultiplied
}
