// aurora.glsl — border (focused window). "Sap light": ONE thin, slightly
// irregular stem hugging the window edge (like a hand-drawn line, in the spirit
// of Sakura's vine but with no leaves/flowers), through which a soft light
// flows. The light is a field, not a point: two lobes run one way, one the
// other, domain-warped so the pattern never repeats exactly. Where it passes,
// the stem swells a little and warms from Peach/Maroon toward pearl; tiny
// snowflake glints (the logo's motif) wake up only there. No comet, no braid,
// no filled band. Original work for Roudix (no third-party code).
//
// Companion: roudix-aurora-inner (window overlay) carries a faint version of the
// same light onto the INSIDE edge. lightField / hueField / FLOW MUST stay
// identical in aurora.glsl and aurora-inner.glsl.
//
// IMPORTANT: PAD must equal `padding` of the preset in effect.toml. Windows are
// 9 px apart in this config: native ring + PAD stays below ~8.
// Colours: palette 0 (accent_primary) / 1 (accent_secondary); Peach/Maroon
// fallback. Cost: no loops; one atan per pixel (glints). Animated: asks for
// frames ([effects] max_fps, or `animated = false` for a frozen light).
//
// Tuning (GLSL constants):
//   FLOW         overall speed of the light (1.0 = calm)
//   STEM_HW      half-width of the stem in px (0.8 = 1.6 px line)
//   STEM_MIN     brightness of the stem between waves of light, 0..1
//   WOBBLE       amplitude of the stem's irregularity in px (0 = ruler-straight)
//   GLINT_EVERY  approximate distance between snowflake glints, px
//   GLINT_SIZE   snowflake arm length, px

const float PAD         = 5.0;
const float TAU         = 6.28318530718;
const float PI          = 3.14159265359;
const float FLOW        = 1.0;
const float STEM_HW     = 0.80;
const float STEM_MIN    = 0.55;
const float WOBBLE      = 1.0;
const float GLINT_EVERY = 240.0;
const float GLINT_SIZE  = 2.6;
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
    float bw = max(margin - PAD, 0.0);                  // native ring width
    float breath = 1.0 - BREATH + BREATH * sin(umbriel_time * 1.1);

    float L = lightField(u, t);
    vec3 base = mix(peach, maroon, hueField(u, t));
    vec3 hot = mix(base, pearl, 0.50 * L * L);

    // The stem's centre line wanders slowly around the middle of the native
    // ring: two low-frequency sines with a WHOLE number of lobes (seamless wrap).
    float n1 = floor(P / 150.0 + 0.5);
    float n2 = floor(P / 57.0 + 0.5);
    float wob = 0.55 * sin(TAU * n1 * u + umbriel_time * 0.35 + 1.3)
              + 0.30 * sin(TAU * n2 * u - umbriel_time * 0.50 + 0.6);
    float c = 0.5 * bw + 0.6 + WOBBLE * wob;

    // Sap swell: the stem thickens a little where the light passes.
    float hw = STEM_HW * (0.85 + 0.45 * L);
    float stem = 1.0 - smoothstep(hw - 0.40, hw + 0.40, abs(d - c));
    float stemA = stem * (STEM_MIN + (1.0 - STEM_MIN) * L) * breath;
    vec4 acc = solid(hot, stemA);

    // A very faint halo around the stem, only as strong as the light.
    float halo = (0.02 + 0.16 * L) * exp(-abs(d - c) / 1.8) * (1.0 - smoothstep(bw + PAD - 1.0, bw + PAD, d));
    acc = over(acc, solid(hot, halo));

    // Tiny snowflake glints, awake only where the light is passing.
    float zone = smoothstep(bw - 0.2, bw + 0.6, d) * (1.0 - smoothstep(bw + PAD - 0.6, bw + PAD, d));
    float cg = bw + 0.5 * PAD;
    float count = max(floor(P / GLINT_EVERY), 3.0);
    float spacing = P / count;
    float idx = floor(s / spacing);
    float centre = (idx + 0.5) * spacing;
    float lt = s - centre;
    float cellLight = lightField(centre / P, t);
    float pulse = 0.5 + 0.5 * sin(umbriel_time * 1.6 + hash11(idx) * TAU);
    float gR = GLINT_SIZE * (0.35 + 0.65 * pulse);
    float flake = snowflake(vec2(lt, (d - cg) * 1.7), gR * 1.7, umbriel_time * 0.5 + hash11(idx + 7.0) * TAU) * zone;
    acc = over(solid(pearl, flake * smoothstep(0.45, 0.85, cellLight) * (0.25 + 0.60 * pulse)), acc);

    return acc; // premultiplied
}
