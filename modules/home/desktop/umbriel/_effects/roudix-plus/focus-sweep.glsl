// focus-sweep.glsl — [animation.border] (focus transition). A short bright
// sweep runs once around the border when focus changes, then fades. Both ends
// of the transition return the input unchanged. Original work for Roudix.
// Tuning: BOOST (0..1), TAIL (higher = shorter sweep).

const float PI    = 3.14159265359;
const float TAIL  = 5.0;
const float LEAD  = 0.03;
const float BOOST = 0.55;

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

vec4 animation(vec2 uv) {
    vec4 c = umbriel_sample(uv);
    float p = umbriel_clamped_progress;
    float u = perimeterU((uv - 0.5) * umbriel_size, umbriel_size);

    float x = fract(p - u + LEAD);
    float sweep = exp(-max(x - LEAD, 0.0) * TAIL) * smoothstep(0.0, LEAD, x);
    float envelope = sin(PI * p);               // 0 at both ends

    return vec4(c.rgb * (1.0 + BOOST * sweep * envelope), c.a);
}
