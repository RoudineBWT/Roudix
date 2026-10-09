// orbit.glsl — border (focused window). A thin, softly "breathing" accent line
// with a small comet of light that slowly circles the window at constant speed
// (measured along the perimeter, so a wide window doesn't make it race on the
// long sides). Original work for Roudix.
//
// Colours: palette 0 (accent_primary) → palette 1 (accent_secondary); Peach →
// Maroon fallback without a palette.
// Cost: no loops, one exp + one sin per ring pixel. Animated, so it requests
// frames (cap with [effects] max_fps, or `animated = false` in effect.toml for
// a static line: time is frozen at 0).
//
// Tuning (GLSL constants):
//   CYCLE_HZ     revolutions per second (0.14 ≈ one lap every 7 s)
//   TAIL         comet tail sharpness (higher = shorter tail)
//   BASE_ALPHA   opacity of the line away from the comet, 0..1
//   BREATH       depth of the slow pulse of the line, 0..~0.3
//   GLOW         strength of the outer glow, 0..1 (needs `padding` > 0)

const float CYCLE_HZ   = 0.14;
const float TAIL       = 7.0;
const float LEAD       = 0.03;
const float BASE_ALPHA = 0.55;
const float BREATH     = 0.12;
const float GLOW       = 0.22;
const float GLOW_FALLOFF = 2.0;

// Position along the window's outline, 0..1, clockwise from the top-left corner.
float perimeterU(vec2 p, vec2 size) {
    vec2 n = p / (0.5 * size);
    float w = size.x;
    float h = size.y;
    float pos;
    if (abs(n.x) > abs(n.y)) {
        float t = clamp(0.5 * n.y + 0.5, 0.0, 1.0);
        pos = n.x > 0.0 ? w + t * h : 2.0 * w + h + (1.0 - t) * h;
    } else {
        float t = clamp(0.5 * n.x + 0.5, 0.0, 1.0);
        pos = n.y < 0.0 ? t * w : w + h + (1.0 - t) * w;
    }
    return clamp(pos / (2.0 * (w + h)), 0.0, 0.9999);
}

// 1 at the comet's head, short soft lead in front, long decaying tail behind.
// x runs 0..1 starting just ahead of the head, so the profile is continuous.
float cometAt(float u, float head) {
    float x = fract(head - u + LEAD);
    return exp(-max(x - LEAD, 0.0) * TAIL) * smoothstep(0.0, LEAD, x);
}

vec4 border(vec2 uv) {
    vec4 ring = umbriel_sample(uv);

    vec3 a = vec3(0.980, 0.702, 0.529); // Peach (fallback)
    vec3 b = vec3(0.922, 0.627, 0.675); // Maroon (fallback)
    if (umbriel_palette_count > 0) {
        a = umbriel_palette_at(0.0).rgb;
        b = umbriel_palette_at(0.25).rgb;
    }

    vec2 p = (uv - 0.5) * umbriel_size;
    float u = perimeterU(p, umbriel_size);
    float head = fract(umbriel_time * CYCLE_HZ);
    float tail = cometAt(u, head);

    float breath = 1.0 - BREATH + BREATH * sin(umbriel_time * 1.3);
    vec3 col = mix(mix(a, b, 0.35), b, tail);          // line → comet colour
    col = mix(col, vec3(1.0), 0.35 * tail * tail);     // bright core

    float lineA = ring.a * (BASE_ALPHA * breath + (1.0 - BASE_ALPHA) * tail);

    float d = max(umbriel_border_distance(uv), 0.0);
    float glow = GLOW * (0.35 + tail) * exp(-d / GLOW_FALLOFF);

    float alpha = max(lineA, glow);
    return vec4(col * alpha, alpha); // premultiplied
}
