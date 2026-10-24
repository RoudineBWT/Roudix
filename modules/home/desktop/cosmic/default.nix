{ lib, config, osConfig, ... }:
let
  isCosmic = osConfig.roudix.desktop.type == "cosmic";

  # Roudix colours, from assets/palette/Roudix.json (modules/home/theming/palette.nix).
  p = config.roudix.palette.active;

  # ── Roudix colours for GTK apps ───────────────────────────────────────────
  # COSMIC themes its own libcosmic apps (panel, dock, Settings, Files...)
  # from the theme chosen in Settings > Appearance, and has no GTK theming at
  # all. GTK apps (the Roudix apps, browsers...) run
  # on adw-gtk3 / libadwaita (modules/home/theming/gtk-theme.nix, which
  # applies on COSMIC like on the bare compositors); this file gives them the
  # Roudix palette on top, through the named colours both of them honour.
  css = ''
    /* Roudix colours — generated from assets/palette/Roudix.json. */
    @define-color accent_color ${p.primary};
    @define-color accent_bg_color ${p.primary};
    @define-color accent_fg_color ${p.onPrimary};
    @define-color destructive_color ${p.error};
    @define-color destructive_bg_color ${p.error};
    @define-color destructive_fg_color ${p.onError};

    @define-color window_bg_color ${p.surface};
    @define-color window_fg_color ${p.onSurface};
    @define-color view_bg_color ${p.surface};
    @define-color view_fg_color ${p.onSurface};
    @define-color headerbar_bg_color ${p.surfaceVariant};
    @define-color headerbar_fg_color ${p.onSurface};
    @define-color headerbar_border_color ${p.outline};
    @define-color card_bg_color ${p.surfaceVariant};
    @define-color card_fg_color ${p.onSurface};
    @define-color sidebar_bg_color ${p.surfaceVariant};
    @define-color sidebar_fg_color ${p.onSurface};
    @define-color popover_bg_color ${p.surfaceVariant};
    @define-color popover_fg_color ${p.onSurface};
    @define-color dialog_bg_color ${p.surfaceVariant};
    @define-color dialog_fg_color ${p.onSurface};
  '';
in
{
  # gtk.enable and the adw-gtk3 theme come from modules/home/theming/gtk-theme.nix
  # (it applies on COSMIC like on the bare compositors). Home Manager already
  # owns ~/.config/gtk-{3,4}.0/gtk.css once a GTK theme is set, so the palette
  # goes through its extraCss options (appended after the theme's own CSS)
  # rather than a second file fighting for the same path.
  config = lib.mkIf isCosmic {
    gtk.gtk3.extraCss = css;
    gtk.gtk4.extraCss = css;
  };
}
