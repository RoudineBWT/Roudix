// aurora-inner.glsl — window overlay of the "roudix-aurora" border. Carries the
// same flowing light onto the INSIDE edge of the focused window, as a very faint
// rim glow. Original work for Roudix. Only touches pixels within DEPTH px of the
// edge; everything else returns the input unchanged.
//
// lightField / hueField and FLOW MUST stay identical to aurora.glsl, so the
// inner glow and the border move together.
// Tuning: DEPTH (px), RIM (resting strength), LIGHT (strength under the waves).

const float TAU   = 6.28318530718;
const float FLOW  = 1.0;
const float DEPTH = 10.0;
const float RIM   = 0.015;
const float LIGHT = 0.16;

// ---- identical to aurora.glsl ----------------------------------------------
float lightField(float u, float t) {
    float warp = 0.9 * sin(TAU * u + t * 0.35);
    float a = sin(TAU * 2.0 * u - t * 0.55 + warp);
    float b = sin(TAU * 3.0 * u + t * 0.40 - 0.8 * warp);
    float c = sin(TAU * 1.0 * u - t * 0.25 + 2.1);
    float v = 0.5 + 0.5 * (0.55 * a + 0.30 * b + 0.15 * c);
    return v * v * (3.0 - 2.0 * v);
}
float hueField(float u, float t) {
    return 0.5 + 0.5 * sin(TAU * u + t * 0.30 + 1.7 * sin(TAU * 2.0 * u - t * 0.2));
}
// ---------------------------------------------------------------------------

vec4 window(vec2 uv) {
    vec4 src = umbriel_sample(uv);

    vec2 size = umbriel_size;
    vec2 q = uv * size - 0.5 * size;
    vec2 h = 0.5 * size;
    vec2 e = abs(q) - h;                 // <= 0 inside
    float inside = -max(e.x, e.y);       // px to the nearest edge
    if (inside > DEPTH) return src;

    float W = size.x;
    float H = size.y;
    float P = 2.0 * (W + H);
    float s;
    if (e.x > e.y) {
        float t = clamp(q.y + h.y, 0.0, H);
        s = q.x > 0.0 ? W + t : 2.0 * W + H + (H - t);
    } else {
        float t = clamp(q.x + h.x, 0.0, W);
        s = q.y < 0.0 ? t : W + H + (W - t);
    }

    vec3 peach  = vec3(0.980, 0.702, 0.529);
    vec3 maroon = vec3(0.922, 0.627, 0.675);
    if (umbriel_palette_count > 0) {
        peach  = umbriel_palette_at(0.0).rgb;
        maroon = umbriel_palette_at(0.25).rgb;
    }
    vec3 pearl = mix(peach, vec3(1.0), 0.62);

    float t = umbriel_time * FLOW;
    float u = s / P;
    float L = lightField(u, t);
    vec3 col = mix(mix(peach, maroon, hueField(u, t)), pearl, 0.4 * L * L);

    float falloff = exp(-max(inside, 0.0) / 4.0) * (1.0 - smoothstep(DEPTH - 4.0, DEPTH, inside));
    float strength = falloff * (RIM + LIGHT * L);

    // Additive light, scaled by the source alpha (translucent windows stay valid).
    return vec4(src.rgb + col * strength * src.a, src.a);
}
