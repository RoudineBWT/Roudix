// wobble.glsl — windows_move. Light "jelly" wobble when a window moves or is
// re-tiled: the content stretches/squashes a little, in a damped oscillation,
// while the native slide plays. Original work for Roudix.
//
// Why it never clips: the displacement is multiplied by sin(pi*u)*sin(pi*v),
// which is 0 on all four edges, so the window outline stays put and no
// transparent sliver appears; only the inside flexes. Both ends of the
// transition return the input unchanged (sin(0) = 0 and an explicit fade-out).
//
// Tuning (GLSL constants):
//   STRENGTH  how much it flexes, as a fraction of window size. 0.035 is
//             subtle; 0.06 clearly wobbly; 0.10 is a lot.
//   CYCLES    number of back-and-forth swings over the transition.
//   DAMPING   how fast the swings die out (higher = fewer visible swings).
//   Timing comes from `duration_ms` of [animation.windows_move]; use ~350 ms.
// Cost: one texture sample per pixel, no loops, no feedback.

const float TAU      = 6.28318530718;
const float PI       = 3.14159265359;
const float STRENGTH = 0.035;
const float CYCLES   = 2.5;
const float DAMPING  = 4.0;

vec4 animation(vec2 uv) {
    // Linear (un-eased) progress: the swing speed must not follow the curve.
    float t = clamp(umbriel_linear_progress, 0.0, 1.0);

    float envelope = exp(-DAMPING * t) * (1.0 - smoothstep(0.80, 1.0, t));
    float swingX = sin(TAU * CYCLES * t) * envelope;
    float swingY = sin(TAU * CYCLES * t + 1.5708) * envelope; // quarter-cycle apart

    // Zero on every edge, maximal in the middle.
    float field = sin(PI * uv.x) * sin(PI * uv.y);

    vec2 shift = STRENGTH * field * vec2(
        swingX * (2.0 * uv.x - 1.0),
        swingY * (2.0 * uv.y - 1.0)
    );
    return umbriel_sample(uv + shift);
}
