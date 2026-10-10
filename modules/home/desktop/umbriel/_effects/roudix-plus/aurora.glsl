// aurora.glsl — border (focused window). "Liquid light": a flowing light that
// drifts around the window in soft, organic waves (two lobes running one way,
// one the other, domain-warped so the pattern never repeats exactly), blending
// Peach → Maroon → pearl. Underneath, a fine braid of two strands keeps the
// structure, and little snowflake glints (the logo's motif) twinkle only where
// the light is passing. No comet, no head: the light is a field, not a point.
// Original work for Roudix (no third-party code).
//
// Companion: roudix-aurora-inner (window overlay) carries the same light onto
// the INSIDE edge of the window. Both read the same field (lightField), which
// must stay identical in aurora.glsl and aurora-inner.glsl.
//
// IMPORTANT: PAD must equal `padding` of the preset in effect.toml. Windows
// are 9 px apart in this config: ring + PAD stays below ~8.
// Colours: palette 0 (accent_primary) / 1 (accent_secondary); Peach/Maroon
// fallback. Cost: no loops; one atan per pixel (glints). Animated: asks for
// frames ([effects] max_fps, or `animated = false` for a frozen light).
//
// Tuning (GLSL constants):
//   FLOW         overall speed of the light (1.0 = calm; 2.0 = twice as fast)
//   LIGHT_MIN    resting brightness of the line between waves, 0..1
//   GLINT_EVERY  approximate distance between snowflake glints, px
//   GLINT_SIZE   snowflake arm length, px
//   BRAID_SPEED  braid flow in rad/s

const float PAD         = 6.0;
const float TAU         = 6.28318530718;
const float PI          = 3.14159265359;
const float FLOW        = 1.0;
const float LIGHT_MIN   = 0.40;
const float BRAID_WAVE  = 36.0;
const float BRAID_SPEED = 1.4;
const float STRAND_HW   = 0.75;
const float GLINT_EVERY = 190.0;
const float GLINT_SIZE  = 4.5;
const float BREATH      = 0.08;

float hash11(float x) { return fract(sin(x * 127.1 + 311.7) * 43758.5453); }
vec4 over(vec4 top, vec4 bottom) { return top + bottom * (1.0 - top.a); }
vec4 solid(vec3 c, float a) { a = clamp(a, 0.0, 1.0); return vec4(c * a, a); }

// ---- the light field (keep identical in aurora-inner.glsl) -----------------
// u = s / perimeter. Whole-number multiples of u make it wrap seamlessly.
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

float sdSegment(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a;
    vec2 ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}

float snowflake(vec2 p, float R, float rot) {
    float a = atan(p.y, p.x + 1e-4) + rot;
    float w = abs(mod(a + 0.5 * PI / 3.0, PI / 3.0) - 0.5 * PI / 3.0);
    vec2 f = length(p) * vec2(cos(w), sin(w));
    float dd = sdSegment(f, vec2(0.0), vec2(R, 0.0)) - 0.45 * (1.0 - 0.6 * min(length(p) / R, 1.0));
    return 1.0 - smoothstep(0.0, 0.9, dd);
}

// s: unrolled outline (px, clockwise from the top-left corner, continuous
// through the corners); d: distance outside the client edge; P: outline length.
void outline(vec2 uv, out float s, out float d, out float P) {
    vec2 cs = umbriel_border_hole.zw * umbriel_size;
    vec2 q = (uv - umbriel_border_hole.xy) * umbriel_size - 0.5 * cs;
    vec2 h = 0.5 * cs;
    vec2 e = abs(q) - h;
    float W = cs.x;
    float H = cs.y;
    P = 2.0 * (W + H);
    if (e.x > e.y) {
        float t = clamp(q.y + h.y, 0.0, H);
        s = q.x > 0.0 ? W + t : 2.0 * W + H + (H - t);
        d = e.x;
    } else {
        float t = clamp(q.x + h.x, 0.0, W);
        s = q.y < 0.0 ? t : W + H + (W - t);
        d = e.y;
    }
}

vec4 border(vec2 uv) {
    vec4 ring = umbriel_sample(uv);

    vec3 peach  = vec3(0.980, 0.702, 0.529);
    vec3 maroon = vec3(0.922, 0.627, 0.675);
    if (umbriel_palette_count > 0) {
        peach  = umbriel_palette_at(0.0).rgb;
        maroon = umbriel_palette_at(0.25).rgb;
    }
    vec3 pearl = mix(peach, vec3(1.0), 0.62);

    float s;
    float d;
    float P;
    outline(uv, s, d, P);

    float t = umbriel_time * FLOW;
    float u = s / P;
    float margin = 0.5 * (umbriel_size.y - umbriel_border_hole.w * umbriel_size.y);
    float bw = max(margin - PAD, 0.0);
    float c = bw + 0.5 * PAD;
    float breath = 1.0 - BREATH + BREATH * sin(umbriel_time * 1.1);

    float L = lightField(u, t);
    vec3 base = mix(peach, maroon, hueField(u, t));
    vec3 hot = mix(base, pearl, 0.55 * L * L);

    // Native ring: always there, brighter where the light passes.
    vec4 acc = solid(hot, ring.a * (LIGHT_MIN + (1.0 - LIGHT_MIN) * L) * breath);

    // Soft outer glow, driven by the same field.
    float outside = max(d - bw, 0.0);
    float glow = (0.04 + 0.46 * L) * exp(-outside / 2.8) * (1.0 - smoothstep(PAD - 1.0, PAD, outside));
    acc = over(acc, solid(hot, glow));

    // Fine braid of two strands with real over/under at the crossings.
    float amp = max(0.5 * PAD - STRAND_HW - 0.5, 0.5);
    float k = TAU / BRAID_WAVE;
    float phase = k * s - umbriel_time * BRAID_SPEED;
    float sw = sin(phase);
    float slope = amp * k * cos(phase);
    float norm = inversesqrt(1.0 + slope * slope);
    float zone = smoothstep(bw - 0.2, bw + 0.6, d) * (1.0 - smoothstep(bw + PAD - 0.8, bw + PAD, d));
    float a1 = (1.0 - smoothstep(STRAND_HW - 0.35, STRAND_HW + 0.35, abs(d - (c + amp * sw)) * norm)) * zone;
    float a2 = (1.0 - smoothstep(STRAND_HW - 0.35, STRAND_HW + 0.35, abs(d - (c - amp * sw)) * norm)) * zone;
    float lit = (0.30 + 0.50 * L) * breath;
    vec4 st1 = solid(mix(peach, pearl, 0.45 * L), a1 * lit);
    vec4 st2 = solid(mix(maroon, pearl, 0.45 * L), a2 * lit);
    bool oneOnTop = mod(floor(phase / PI + 0.5), 2.0) < 0.5;
    acc = oneOnTop ? over(st1, over(st2, acc)) : over(st2, over(st1, acc));

    // Snowflake glints, awake only where the light is passing.
    float count = max(floor(P / GLINT_EVERY), 4.0);
    float spacing = P / count;
    float idx = floor(s / spacing);
    float centre = (idx + 0.5) * spacing;
    float lt = s - centre;
    float cellLight = lightField(centre / P, t);
    float pulse = 0.5 + 0.5 * sin(umbriel_time * 1.6 + hash11(idx) * TAU);
    float gR = GLINT_SIZE * (0.35 + 0.65 * pulse);
    float flake = snowflake(vec2(lt, (d - c) * 1.7), gR * 1.7, umbriel_time * 0.5 + hash11(idx + 7.0) * TAU) * zone;
    acc = over(solid(pearl, flake * smoothstep(0.35, 0.80, cellLight) * (0.25 + 0.65 * pulse)), acc);

    return acc; // premultiplied
}
