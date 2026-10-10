// orbit-inner.glsl — window overlay of the "roudix-orbit" border. Continues
// the comet's glow on the INSIDE edge of the focused window (same clock and
// same outline coordinate as orbit.glsl, so the two stay in sync) plus a very
// faint breathing rim. Original work for Roudix. Only touches pixels within
// DEPTH px of the edge; everything else returns the input unchanged.
//
// Tuning: DEPTH (px), RIM (resting strength), COMET (strength under the comet).
// CYCLE_HZ / TAIL_PX must match orbit.glsl.

const float PI       = 3.14159265359;
const float TAU      = 6.28318530718;
const float DEPTH    = 16.0;
const float RIM      = 0.05;
const float COMET    = 0.30;
const float CYCLE_HZ = 0.14;
const float TAIL_PX  = 240.0;

vec4 window(vec2 uv) {
    vec4 src = umbriel_sample(uv);

    vec2 size = umbriel_size;
    vec2 q = uv * size - 0.5 * size;
    vec2 h = 0.5 * size;
    vec2 e = abs(q) - h;                  // <= 0 inside
    float inside = -max(e.x, e.y);        // px to the nearest edge
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

    float t = umbriel_time;
    float sHead = fract(t * CYCLE_HZ) * P;
    float ds = mod(s - sHead + 0.5 * P, P) - 0.5 * P;
    float tailLen = min(TAIL_PX, 0.3 * P);
    float comet = ds < 0.0 ? exp(ds / tailLen) : exp(-ds * ds / 392.0);

    float falloff = exp(-max(inside, 0.0) / 4.5) * (1.0 - smoothstep(DEPTH - 4.0, DEPTH, inside));
    float breath = 0.5 + 0.5 * sin(t * 1.1);
    float strength = falloff * (RIM * (0.6 + 0.4 * breath) + COMET * comet);
    vec3 col = mix(maroon, peach, 0.35 + 0.65 * comet);

    // Additive light, scaled by the source alpha (translucent windows stay valid).
    return vec4(src.rgb + col * strength * src.a, src.a);
}
