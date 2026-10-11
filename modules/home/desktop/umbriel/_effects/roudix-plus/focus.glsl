// focus.glsl — [animation.border] (focus transition). Brief brightness swell
// of the border ring when focus changes; identical to the input at both ends.
// Original work for Roudix. Tuning: BOOST (0..1).

const float PI    = 3.14159265;
const float BOOST = 0.35;

vec4 animation(vec2 uv) {
    float bump = sin(PI * umbriel_clamped_progress);
    vec4 c = umbriel_sample(uv);
    return vec4(c.rgb * (1.0 + BOOST * bump), c.a);
}
