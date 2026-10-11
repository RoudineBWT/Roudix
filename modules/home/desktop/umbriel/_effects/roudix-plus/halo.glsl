// halo.glsl — cursor. A very soft accent halo under the pointer.
// Original work for Roudix. Static (no umbriel_time) → no extra frames.
// Preset radius = 28 logical px (half-size of the square); the halo fades out
// before the edge so no square shows. The shader blends over what is
// underneath (the cursor image itself is never touched).
//
// Tuning: PEAK (0..1, opacity at the centre), SIGMA (logical px).

const float PEAK    = 0.20;
const float SIGMA   = 8.0;
const float R_INNER = 20.0;
const float R_OUTER = 28.0;

vec4 cursor(vec2 uv) {
    vec4 src = umbriel_sample(uv);

    vec2 p = (uv - umbriel_pointer) * umbriel_size;
    float d2 = dot(p, p);
    float window = 1.0 - smoothstep(R_INNER * R_INNER, R_OUTER * R_OUTER, d2);
    float a = PEAK * exp(-d2 / (2.0 * SIGMA * SIGMA)) * window;

    vec3 col = vec3(0.980, 0.702, 0.529); // Peach (fallback)
    if (umbriel_palette_count > 0) {
        col = umbriel_palette_at(0.0).rgb;
    }

    // "over": premultiplied tint on top of the (premultiplied) source.
    return vec4(col * a + src.rgb * (1.0 - a), a + src.a * (1.0 - a));
}
