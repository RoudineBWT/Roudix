// layer.glsl — layers (bar, launcher, notifications…). Short 10 px slide
// from below + fade, same shared show/hide logic as scratchpad.glsl.
// Original work for Roudix. Opening ends fully visible, closing ends
// invisible. Tuning: SLIDE (logical px).

const float SLIDE = 10.0;

vec4 animation(vec2 uv) {
    float visible = umbriel_direction > 0.0
        ? umbriel_clamped_progress
        : 1.0 - umbriel_clamped_progress;
    float offset = SLIDE * (1.0 - visible) / umbriel_size.y;
    return umbriel_sample(uv - vec2(0.0, offset)) * visible;
}
