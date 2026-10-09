// logo.glsl — windows_in / windows_out. The window is revealed THROUGH the
// Roudix logo: the logo (6 peach arms, 6 rose chevrons, central disc) spins
// and grows from the centre of the window, a thin coloured outline follows its
// edge, then the shape swells until it covers the whole window. Closing plays
// the same sequence backwards (shared show/hide shader, driven by
// umbriel_direction). Original work for Roudix; geometry measured from
// assets/logo/roudix-logo.svg.
//
// Colours: arms = palette 0 (Peach), chevrons = palette 1 (Maroon) — exactly
// the logo's colours when [colors] is Catppuccin Mocha (setups roudix-logo*).
// Fallbacks to the same Peach/Maroon without a palette.
//
// Endpoints: opening ends on the untouched input; closing ends fully
// transparent (o = 0).
//
// Tuning (GLSL constants):
//   LOGO_SCALE   logo size vs. the window's short side (1.0 = touches edges)
//   START_SCALE  starting size of the logo (fraction of its final size)
//   SPIN         rotation while growing, radians; keep a multiple of pi/3 so
//                it lands exactly on the upright logo (2.094 = two turns of 60°)
//   RIM_PX       outline thickness, logical px; RIM_OPACITY its strength
//   Timing: duration_ms of [animation.windows_in/out] (~480 / 380 ms).
// Cost: one atan + a few distance evaluations per pixel; no loops/feedback.

const float SIXTH       = 1.04719755;   // pi / 3
const float LOGO_SCALE  = 0.90;
const float START_SCALE = 0.25;
const float SPIN        = 1.04719755;
const float AA          = 1.2;
const float RIM_PX      = 2.5;
const float RIM_OPACITY = 0.90;

float sdSegment(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a;
    vec2 ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}

// Signed distance to the logo in logo units (centre disc radius 0.30, tip of
// the arms at ~0.95). comp: 0 = arm, 1 = chevron, 2 = disc.
float logoSD(vec2 q, float spin, out float comp) {
    float r = length(q);
    float a = atan(q.y, q.x + 1e-5) + spin;
    // 6-fold symmetry: fold into [0, 30°]. Chevrons sit on 0°, arms on 30°.
    float w = abs(mod(a + 0.5 * SIXTH, SIXTH) - 0.5 * SIXTH);
    vec2 f = r * vec2(cos(w), sin(w));

    float disc = r - 0.30;
    vec2 dir = vec2(0.8660254, 0.5);                        // 30°
    float arm = sdSegment(f, 0.28 * dir, 0.90 * dir) - 0.083;
    float chev = sdSegment(f, vec2(0.58, 0.0), vec2(0.88, 0.16)) - 0.060;

    float d = disc;
    comp = 2.0;
    if (arm < d)  { d = arm;  comp = 0.0; }
    if (chev < d) { d = chev; comp = 1.0; }
    return d;
}

vec4 animation(vec2 uv) {
    // o: 0 = invisible, 1 = fully shown (opening goes 0→1, closing 1→0).
    float o = umbriel_direction > 0.0
        ? umbriel_clamped_progress
        : 1.0 - umbriel_clamped_progress;

    vec4 src = umbriel_sample(uv);
    if (o >= 0.999) return src;
    if (o <= 0.0) return vec4(0.0);

    vec2 p = (uv - 0.5) * umbriel_size;                     // logical px
    float shortHalf = 0.5 * min(umbriel_size.x, umbriel_size.y);

    float grow = smoothstep(0.0, 0.60, o);                  // logo scale + spin
    float R = max(shortHalf * LOGO_SCALE * mix(START_SCALE, 1.0, grow), 1.0);
    float spin = (1.0 - grow) * SPIN;

    float comp;
    float sd = logoSD(p / R, spin, comp) * R;               // px, <0 inside

    // The shape swells until it has swallowed the whole rectangle.
    float maxD = 0.5 * length(umbriel_size) + 4.0;
    float swell = smoothstep(0.50, 0.97, o);
    float edge = sd - swell * maxD;

    float fade = smoothstep(0.0, 0.25, o);
    float mask = 1.0 - smoothstep(-AA, AA, edge);
    vec4 shown = src * (mask * fade);

    // Coloured outline following the shape (Peach arms, Maroon chevrons).
    vec3 peach = vec3(0.980, 0.702, 0.529);
    vec3 maroon = vec3(0.922, 0.627, 0.675);
    if (umbriel_palette_count > 0) {
        peach = umbriel_palette_at(0.0).rgb;
        maroon = umbriel_palette_at(0.25).rgb;
    }
    vec3 rimColor = comp < 0.5 ? peach : (comp < 1.5 ? maroon : mix(peach, vec3(1.0), 0.6));

    float band = 1.0 - smoothstep(0.0, RIM_PX, abs(edge));
    float coverage = smoothstep(0.01, 0.12, src.a);
    float rim = band * RIM_OPACITY * (1.0 - swell) * fade * coverage;

    return vec4(rimColor * rim, rim) + shown * (1.0 - rim);
}
