-- Application placement and appearance rules for Roudix Hyprland.

local gamingWorkspace = "name:\u{f0297}"

-- File manager / editor / development.
hl.window_rule({ match = { class = "^(org\\.gnome\\.Nautilus)$", title = "negative:^(Open|Open File|Save As|Save File|Enregistrer|Enregistrer Sous|Ouvrir|Choisir un Fichier)$" }, workspace = "name:\u{f024b}" })
hl.window_rule({ match = { class = "^(org\\.gnome\\.Nautilus)$", title = "^(Save As|Enregistrer Sous)$" }, float = true })
hl.window_rule({ match = { class = "^(org\\.gnome\\.TextEditor)$" }, workspace = "name:\u{f024b}" })
hl.window_rule({ match = { class = "^(dev\\.zed\\.Zed)$" }, workspace = "name:\u{e8da}" })
hl.window_rule({ match = { class = "^(kitty)$" }, workspace = "name:\u{e795}", float = true })
hl.window_rule({ match = { class = "^(ghostty|com\\.mitchellh\\.ghostty)$" }, workspace = "name:\u{e795}", float = true })
hl.window_rule({ match = { class = "^(org\\.gnome\\.Ptyxis)$" }, workspace = "name:\u{e795}" })

-- Media player.
hl.window_rule({ match = { class = "^(com\\.github\\.rafostar\\.Clapper|io\\.github\\.rafostar\\.Clapper)$", title = "^$" }, float = true, center = true })
hl.window_rule({ match = { class = "^(com\\.github\\.rafostar\\.Clapper|io\\.github\\.rafostar\\.Clapper)$" }, opacity = "1.0 override" })

-- Communication / music.
hl.window_rule({ match = { class = "^(vesktop|discord)$" }, workspace = "name:\u{f1ff}" })
hl.window_rule({ match = { class = "^(Element)$" }, workspace = "name:\u{f1ff}" })
hl.window_rule({ match = { class = "^(org\\.telegram\\.desktop)$" }, workspace = "name:\u{e743}" })
hl.window_rule({ match = { class = "^(Spotify)$" }, workspace = "name:\u{f075a}" })
hl.window_rule({ match = { class = "^(org\\.kde\\.easyeffects)$" }, workspace = "name:\u{f075a}" })

-- Browsers. Exclude PIP so the common PIP rule remains effective.
local pipTitleExclude = "negative:^([Pp]icture[-\\s]?[Ii]n[-\\s]?[Pp]icture)(.*)$"
local browserClasses = "^(firefox|zen|zen-twilight|brave-origin-beta|brave-browser)$"
hl.window_rule({ match = { class = browserClasses, title = pipTitleExclude }, workspace = "name:\u{f0239}", size = "monitor_w monitor_h" })
hl.window_rule({ match = { class = browserClasses }, opacity = "0.9 override" })

-- Ghostty default floating size.
hl.window_rule({ match = { class = "^(com\\.mitchellh\\.ghostty)$" }, float = true, size = "1505 755" })

-- Windows/Wine and generic launchers.
hl.window_rule({ match = { class = "^(.*\\.exe)$" }, float = true, monitor = PRIMARY_MONITOR, center = true, fullscreen_state = 0 })
hl.window_rule({ match = { class = "^(.*[Ll]auncher.*)$" }, float = true, monitor = PRIMARY_MONITOR })

-- Utility floating applications.
local floatApps = {
    { class = "^(kvantummanager|qt[56]ct|nwg-look)$" },
    { class = "^(org\\.pulseaudio\\.pavucontrol|blueman-manager|nm-applet|nm-connection-editor)$" },
    { class = "^(.*[Cc]alculator.*)$" },
    { class = "^(dev\\.)?(noctalia\\.Noctalia\\.Settings)$" },
    { class = "^(.*satty.*)$", title = "^(Satty)$" },
}
for _, m in ipairs(floatApps) do hl.window_rule({ match = m, float = true }) end

-- Browser/terminal/media opacity.
local terminals = "^(ghostty|kitty|com\\.mitchellh\\.ghostty|[Kk]onsole|Alacritty|gnome-terminal|xfce[0-9]?-terminal)$"
hl.window_rule({ match = { class = terminals }, opacity = "1.0 override" })
hl.window_rule({ match = { class = "^(mpv|org\\.kde\\.haruna|.*plex.*|org\\.kde\\.gwenview|.*vlc.*)$" }, opacity = "1.0 override" })

-- Keep the gaming workspace available for utility apps that belong there.
hl.window_rule({ match = { class = "^(openrgb)$" }, workspace = gamingWorkspace })
hl.window_rule({ match = { class = "^(org\\.prismlauncher\\.PrismLauncher)$" }, workspace = gamingWorkspace })
