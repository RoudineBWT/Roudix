// focus-zip.glsl — [animation.border] (focus transition). When a window gets
// focus, two fronts of light leave the middle of the top edge, run down both
// sides and meet at the middle of the bottom edge, leaving a short afterglow.
// Both ends of the transition return the input unchanged. Original work for
// Roudix. Tuning: BOOST (brightening), SPARK (added white-peach light),
// FRONT (front width as a fraction of the half-perimeter).

const float PI    = 3.14159265359;
const float BOOST = 0.9;
const float SPARK = 0.30;
const float FRONT = 0.045;

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

    float W = umbriel_size.x;
    float H = umbriel_size.y;
    float u = perimeterU((uv - 0.5) * umbriel_size, umbriel_size);
    float topCentre = 0.5 * W / (2.0 * (W + H));

    // Distance along the outline from the top-centre, either way round: 0..0.5.
    float dd = abs(u - topCentre);
    dd = min(dd, 1.0 - dd);

    float front = p * 0.5;
    float x = (dd - front) / FRONT;
    float head = exp(-x * x);
    float afterglow = dd < front ? exp(-(front - dd) / 0.10) : 0.0;
    float intensity = head + 0.35 * afterglow;

    float envelope = smoothstep(0.0, 0.06, p) * (1.0 - smoothstep(0.88, 1.0, p));
    float k = intensity * envelope;

    vec3 spark = vec3(1.0, 0.93, 0.86);
    return vec4(c.rgb * (1.0 + BOOST * k) + spark * (SPARK * k) * c.a, c.a);
}
