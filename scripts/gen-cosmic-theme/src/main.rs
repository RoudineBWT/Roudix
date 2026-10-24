use cosmic_config::CosmicConfigEntry;
use cosmic_theme::palette::{Srgb, Srgba};
use cosmic_theme::{Theme, ThemeBuilder};

fn rgb(h: &str) -> Srgb {
    let h = h.trim_start_matches('#');
    let v = |i: usize| u8::from_str_radix(&h[i..i + 2], 16).unwrap() as f32 / 255.0;
    Srgb::new(v(0), v(2), v(4))
}
fn rgba(h: &str) -> Srgba {
    let c = rgb(h);
    Srgba::new(c.red, c.green, c.blue, 1.0)
}

struct P {
    bg: &'static str,
    container: &'static str,
    container2: &'static str,
    text: &'static str,
    accent: &'static str,
    success: &'static str,
    warning: &'static str,
    destructive: &'static str,
}

fn make(mut b: ThemeBuilder, p: &P) -> ThemeBuilder {
    b.bg_color = Some(rgba(p.bg));
    b.primary_container_bg = Some(rgba(p.container));
    b.secondary_container_bg = Some(rgba(p.container2));
    b.text_tint = Some(rgb(p.text));
    b.accent = Some(rgb(p.accent));
    b.success = Some(rgb(p.success));
    b.warning = Some(rgb(p.warning));
    b.destructive = Some(rgb(p.destructive));
    b.window_hint = Some(rgb(p.accent));
    b
}

fn main() {
    let dark = P { bg: "#14100D", container: "#211A15", container2: "#2A211B", text: "#EADBCB",
        accent: "#FF8C42", success: "#A8B86A", warning: "#F2B05E", destructive: "#E85D4A" };
    let light = P { bg: "#FBF5EE", container: "#F1E6D9", container2: "#E8DBCB", text: "#3B2F27",
        accent: "#E0661A", success: "#7A8F2E", warning: "#C98A1E", destructive: "#CC4B37" };

    for (builder, p, bcfg, tcfg) in [
        (ThemeBuilder::dark(), &dark, ThemeBuilder::dark_config(), Theme::dark_config()),
        (ThemeBuilder::light(), &light, ThemeBuilder::light_config(), Theme::light_config()),
    ] {
        let b = make(builder, p);
        let theme = b.clone().build();
        b.write_entry(&bcfg.unwrap()).unwrap();
        theme.write_entry(&tcfg.unwrap()).unwrap();
    }
}
