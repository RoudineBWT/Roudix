// windows-in.glsl — remplace le style "popin" intégré par un vrai zoom
// piloté par bezier cubique (résolution Newton-Raphson, comme les courbes
// CSS standard). Repris et adapté de rebizzz/nixos
// (modules/home/desktop/umbriel/_shaders/windows-in.glsl, MIT) pour matcher
// tes propres courbes ([appearance] easeout/snappy côté config, cf.
// _animation.nix) plutôt que ses "beziers" custom.
//
// Ici : la fenêtre grandit selon emphasizedDecel (proche de ton "easeout")
// pendant 150ms — même durée que ton windows_in.duration_ms — et le fondu
// suit standard sur la même fenêtre de temps, plutôt que deux durées
// distinctes comme l'original (500/600ms) : plus cohérent avec un réglage
// piloté depuis _animation.nix.

float bezierAxis(float t, float p1, float p2) {
    float u = 1.0 - t;
    return 3.0 * u * u * t * p1 + 3.0 * u * t * t * p2 + t * t * t;
}

float bezierSlope(float t, float p1, float p2) {
    float u = 1.0 - t;
    return 3.0 * u * u * p1 + 6.0 * u * t * (p2 - p1) + 3.0 * t * t * (1.0 - p2);
}

float newtonStep(vec4 points, float x, float t) {
    float slope = max(bezierSlope(t, points.x, points.z), 1e-3);
    return clamp(t - (bezierAxis(t, points.x, points.z) - x) / slope, 0.0, 1.0);
}

float cubicBezier(vec4 points, float x) {
    x = clamp(x, 0.0, 1.0);
    float t = x;
    t = newtonStep(points, x, t);
    t = newtonStep(points, x, t);
    t = newtonStep(points, x, t);
    t = newtonStep(points, x, t);
    t = newtonStep(points, x, t);
    t = newtonStep(points, x, t);
    return bezierAxis(t, points.y, points.w);
}

// emphasizedDecel (Material 3) : décélération franche, proche de ton
// "easeout" mais avec un léger galbe en fin de course.
const vec4 emphasizedDecel = vec4(0.05, 0.7, 0.1, 1.0);
const vec4 standard = vec4(0.2, 0.0, 0.0, 1.0);

// Point de départ du zoom (0.85 = ton ancien scale du style "popin").
const float startScale = 0.85;

vec4 animation(vec2 uv) {
    float grow = cubicBezier(emphasizedDecel, umbriel_linear_progress);
    float alpha = cubicBezier(standard, umbriel_linear_progress);
    float scaleFactor = mix(startScale, 1.0, grow);
    vec2 scale = max(umbriel_size * scaleFactor, vec2(5.0)) / umbriel_size;
    return umbriel_sample((uv - 0.5) / scale + 0.5) * alpha;
}
