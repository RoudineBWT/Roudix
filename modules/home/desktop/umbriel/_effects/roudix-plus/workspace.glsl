// workspace.glsl — workspaces. While switching, the whole workspace "steps
// back" (tiny zoom-out + slight dim) and returns to rest at the end. It only
// post-processes the native slide, so both endpoints return the input
// unchanged. Original work for Roudix.
//
// Tuning: ZOOM_OUT (fraction, 0.025 = 2.5 %), DIP (dimming, 0..1).

const float PI       = 3.14159265;
const float ZOOM_OUT = 0.025;
const float DIP      = 0.10;

vec4 animation(vec2 uv) {
    float bump = sin(PI * umbriel_clamped_progress); // 0 → 1 → 0
    float s = 1.0 - ZOOM_OUT * bump;
    vec4 c = umbriel_sample((uv - 0.5) / s + 0.5);
    return vec4(c.rgb * (1.0 - DIP * bump), c.a);
}
