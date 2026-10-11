// orbit.glsl — border (focused window). "Snowflake braid":
//   * two interlaced strands (Peach / Maroon) flowing around the window, with
//     proper over/under at every crossing;
//   * small six-armed snowflake glints (the Roudix logo's motif) twinkling at
//     regular intervals along the outline;
//   * a comet of light circling the window, led by a larger rotating
//     snowflake flare, that also lights the strands and the glow it passes.
// Companion: roudix-orbit-inner (window overlay) continues the comet's glow
// on the INSIDE edge of the window; the preset's [light] makes it spill onto
// the surroundings. Original work for Roudix (no third-party code).
//
// Geometry: everything is placed with an unrolled perimeter coordinate `s`
// (px, clockwise from the top-left corner, continuous at the corners) and the
// distance `d` outside the client rectangle. Speed is therefore constant on
// every side and the pattern wraps seamlessly (glint count is an integer).
//
// IMPORTANT: PAD must equal `padding` of the preset in effect.toml.
// Layout in px outside the window: [0, bw] native ring, [bw, bw+PAD] braid zone
// (bw = what is left of the allocated rectangle once PAD is removed). Windows
// are 9 px apart in this config, so keep ring + PAD below ~8.
//
// Colours: palette 0 (accent_primary) / palette 1 (accent_secondary);
// Peach / Maroon fallback. Cost: no loops; one atan per snowflake (2 per
// pixel). Animated: asks for frames (see [effects] max_fps, `animated=false`).
//
// Tuning (GLSL constants):
//   CYCLE_HZ     comet revolutions per second (0.14 ≈ 7 s per lap)
//   TAIL_PX      comet tail length in px
//   BRAID_SPEED  braid flow in rad/s (about 8 px/s at 36 px wavelength)
//   GLINT_EVERY  approximate distance between snowflake glints, px
//   GLINT_SIZE   snowflake arm length, px
//   FLARE_SIZE   arm length of the flare at the comet head, px

const float PAD         = 6.0;
const float TAU         = 6.28318530718;
const float PI          = 3.14159265359;
const float CYCLE_HZ    = 0.14;
const float TAIL_PX     = 240.0;
const float BRAID_WAVE  = 36.0;
const float BRAID_SPEED = 1.4;
const float STRAND_HW   = 0.75;
const float GLINT_EVERY = 190.0;
const float GLINT_SIZE  = 4.5;
const float FLARE_SIZE  = 9.0;
const float BREATH      = 0.10;

float hash11(float x) { return fract(sin(x * 127.1 + 311.7) * 43758.5453); }

vec4 over(vec4 top, vec4 bottom) { return top + bottom * (1.0 - top.a); }
vec4 solid(vec3 c, float a) { a = clamp(a, 0.0, 1.0); return vec4(c * a, a); }

float sdSegment(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a;
    vec2 ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}

// Six-armed snowflake of arm length R, rotated by `rot`; 1 on the arms, 0 off.
float snowflake(vec2 p, float R, float rot) {
    float a = atan(p.y, p.x + 1e-4) + rot;
    float w = abs(mod(a + 0.5 * PI / 3.0, PI / 3.0) - 0.5 * PI / 3.0);
    vec2 f = length(p) * vec2(cos(w), sin(w));
    float dd = sdSegment(f, vec2(0.0), vec2(R, 0.0)) - 0.45 * (1.0 - 0.6 * min(length(p) / R, 1.0));
    return 1.0 - smoothstep(0.0, 0.9, dd);
}

// Unrolled outline coordinate s (0..P px, clockwise from the top-left corner,
// continuous through the corners), outward distance d from the client edge,
// outline length P.
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

    float t = umbriel_time;
    float margin = 0.5 * (umbriel_size.y - umbriel_border_hole.w * umbriel_size.y);
    float bw = max(margin - PAD, 0.0);          // native ring width
    float c = bw + 0.5 * PAD;                   // centre line of the braid zone
    float breath = 1.0 - BREATH + BREATH * sin(t * 1.1);

    // ---- comet: signed distance behind (<0) / ahead (>0) of the head, px ----
    float sHead = fract(t * CYCLE_HZ) * P;
    float ds = mod(s - sHead + 0.5 * P, P) - 0.5 * P;
    float tailLen = min(TAIL_PX, 0.3 * P);
    float comet = ds < 0.0 ? exp(ds / tailLen) : exp(-ds * ds / 392.0);
    float across = exp(-(d - c) * (d - c) / 18.0);   // brightest mid-zone

    // ---- native ring: colour drifting between the two accents ----
    float drift = 0.5 + 0.5 * sin(TAU * 3.0 * s / P - t * 0.6);
    vec3 ringCol = mix(mix(peach, maroon, drift), pearl, 0.55 * comet);
    vec4 acc = solid(ringCol, ring.a * (0.85 * breath + 0.15 * comet));

    // ---- soft glow outside the ring, fed by the comet ----
    float outside = max(d - bw, 0.0);
    float glow = (0.10 + 0.55 * comet) * exp(-outside / 2.6) * (1.0 - smoothstep(PAD - 1.0, PAD, outside));
    acc = over(acc, solid(mix(maroon, peach, 0.5 + 0.5 * comet), glow));

    // ---- braid: two strands in antiphase with real over/under ----
    float amp = max(0.5 * PAD - STRAND_HW - 0.5, 0.5);
    float k = TAU / BRAID_WAVE;
    float phase = k * s - t * BRAID_SPEED;
    float sw = sin(phase);
    float slope = amp * k * cos(phase);
    float norm = inversesqrt(1.0 + slope * slope);
    float zone = smoothstep(bw - 0.2, bw + 0.6, d) * (1.0 - smoothstep(bw + PAD - 0.8, bw + PAD, d));
    float a1 = (1.0 - smoothstep(STRAND_HW - 0.35, STRAND_HW + 0.35, abs(d - (c + amp * sw)) * norm)) * zone;
    float a2 = (1.0 - smoothstep(STRAND_HW - 0.35, STRAND_HW + 0.35, abs(d - (c - amp * sw)) * norm)) * zone;
    float lit = 0.70 * breath + 0.55 * comet * across;
    vec4 st1 = solid(mix(peach, pearl, 0.5 * comet), a1 * lit);
    vec4 st2 = solid(mix(maroon, pearl, 0.5 * comet), a2 * lit);
    // Parity of the crossing index decides which strand is on top there.
    bool oneOnTop = mod(floor(phase / PI + 0.5), 2.0) < 0.5;
    acc = oneOnTop ? over(st1, over(st2, acc)) : over(st2, over(st1, acc));

    // ---- snowflake glints at regular intervals (integer count: seamless) ----
    float count = max(floor(P / GLINT_EVERY), 4.0);
    float spacing = P / count;
    float idx = floor(s / spacing);
    float lt = s - (idx + 0.5) * spacing;
    float pulse = 0.5 + 0.5 * sin(t * 1.6 + hash11(idx) * TAU);
    float gR = GLINT_SIZE * (0.35 + 0.65 * pulse);
    float flake = snowflake(vec2(lt, (d - c) * 1.7), gR * 1.7, t * 0.5 + hash11(idx + 7.0) * TAU);
    flake *= zone;
    acc = over(solid(pearl, flake * (0.30 + 0.60 * pulse)), acc);

    // ---- flare at the comet head: larger, spinning snowflake + halo ----
    vec2 fp = vec2(ds, (d - c) * 1.7);
    float flare = snowflake(fp, FLARE_SIZE * 1.7, t * 1.2);
    float halo = exp(-dot(fp, fp) / 70.0);
    acc = over(solid(vec3(1.0), (0.85 * flare + 0.35 * halo) * (1.0 - smoothstep(PAD - 0.5, PAD + 1.0, outside))
                                * smoothstep(-0.5, 0.5, d + 0.5)), acc);
    acc = over(solid(pearl, 0.5 * halo * across), acc);

    return acc; // premultiplied
}
