[English](README.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português (Brasil)](README.pt_BR.md) · [Русский](README.ru.md) · [简体中文](README.zh_CN.md) · **हिन्दी** · [العربية](README.ar.md)

<div align="center">
<img src="assets/logo/roudix-logo.png" width="250"/>

# Roudix
### NixOS कॉन्फ़िगरेशन (Unstable) — कई Wayland कंपोज़िटर (hyprland, niri, mangowc और umbriel) · Gnome और KDE · CachyOS कर्नेल

![NixOS](https://img.shields.io/badge/NixOS-unstable-5277C3?style=for-the-badge&logo=nixos&logoColor=white)
![Wayland](https://img.shields.io/badge/Wayland-Niri%20%2F%20Hyprland-FFB800?style=for-the-badge&logo=wayland&logoColor=black)
![Kernel](https://img.shields.io/badge/Kernel-CachyOS-FF4500?style=for-the-badge&logo=linux&logoColor=white)

<br/>

| पूर्वावलोकन |
|:---:|
| <img src="assets/screenshot/preview-slideshow.webp" alt="Roudix का पूर्वावलोकन स्लाइडशो: Umbriel, GNOME और KDE Plasma" width="900"/> |

<sub>निजी कस्टमाइज़ेशन — आपके सेटअप के अनुसार आपका रूप अलग दिखेगा 👀</sub><br/>
<sub>Wayland कंपोज़िटर को कस्टमाइज़ करना आप पर छोड़ा गया है: Roudix केवल Noctalia, DankMaterialShell और (केवल Hyprland के लिए) Caelestia का डिफ़ॉल्ट कॉन्फ़िग देता है।</sub>

</div>

---

## हार्डवेयर

| घटक | मॉडल |
|-----------|-------|
| CPU | Intel Core i5-13600KF |
| GPU | AMD Radeon RX 7900 XT |

---

## स्टैक

| परत | चुनाव |
|-------|--------|
| OS | Roudix (NixOS unstable) |
| Kernel | CachyOS (कर्नेल वैरिएंट [सुविधाएँ](docs/features.md) या [इंस्टॉलेशन](docs/installation.hi.md) में देखें) |
| Bootloader | Limine (डिफ़ॉल्ट) · systemd-boot |
| Compositor | Niri (स्क्रोल होने वाली टाइलिंग) · Hyprland (डायनामिक टाइलिंग) · MangoWC · Umbriel (स्क्रोल होने वाली टाइलिंग, Noctalia-नेटिव) |
| ग्राफ़िकल शेल | Noctalia · DankMaterialShell · Caelestia |
| डेस्कटॉप एनवायरनमेंट | KDE Plasma · Gnome |
| डिस्प्ले मैनेजर | DMS Greeter (केवल Dms) · Noctalia Greeter (केवल noctalia) · plasma-login-manager (केवल KDE) · GDM (केवल Gnome) |
| टर्मिनल | कॉन्फ़िगर करने योग्य (Ghossty, Kitty, Foot, Wzertem, Konsole, Ptyxis) |
| शेल | Fish · Bash |
| ब्राउज़र | कॉन्फ़िगर करने योग्य (Brave, Helium, Vivaldi, Firefox, LibreWolf, Chromium, Zen Twilight) |
| फ़ाइल मैनेजर | कॉन्फ़िगर करने योग्य (Nautilus, Thunar, Dolphin, Nemo) |
| एडिटर | कॉन्फ़िगर करने योग्य (Zed, VS Code, Neovim, कोई नहीं) |
| Chat | Discord (Vencord · vanilla · कोई नहीं) + Matrix (Element · Cinny · कोई नहीं) |
| संगीत | कॉन्फ़िगर करने योग्य (Spotify + Spicetify, YouTube Music Desktop, कोई नहीं) |

---

## दस्तावेज़

| | |
|-|-|
| 🖥️ [डेस्कटॉप और शेल](docs/desktop.md) | कंपोज़िटर और ग्राफ़िकल शेल बदलें, निजी ओवरराइड (Niri, Hyprland, GNOME, KDE) |
| ⚡ [एलियास और फ़ंक्शन](docs/aliases.hi.md) | सभी शेल एलियास और फ़ंक्शन — `roudix-switch`, `roudix-shell-switch`, `rebuild`… |
| 🚀 [इंस्टॉलेशन](docs/installation.hi.md) | स्वचालित और मैनुअल इंस्टॉलेशन गाइड |
| ✨ [सुविधाएँ](docs/features.md) | डेस्कटॉप एनवायरनमेंट के अनुसार सुविधाओं की पूरी सूची |
| 🔄 [ऑटो-अपडेट](docs/autoupdate.hi.md) | स्वचालित git pull + रीबिल्ड का कॉन्फ़िगरेशन |

---

## संरचना

```
roudix/
├── roudix-installer.sh              # Bash-आधारित इंस्टॉलर
├── flake.nix                        # इनपुट और आउटपुट
├── flake.lock
├── docs/                            # दस्तावेज़
│   ├── desktop.md                   # डेस्कटॉप एनवायरनमेंट और ग्राफ़िकल शेल
│   ├── aliases.md                   # शेल एलियास और फ़ंक्शन
│   ├── installation.md              # इंस्टॉलेशन गाइड
│   ├── features.md                  # सुविधाओं की सूची
│   ├── features.fr.md               # सुविधाओं की सूची (फ़्रेंच)
│   └── autoupdate.md                # ऑटो-अपडेट कॉन्फ़िगरेशन
│
├── hosts/
│   └── roudix/                      # एक ही होस्ट — DE roudix.desktop.type से चुना जाता है
│       ├── configuration.nix
│       ├── username.nix             # gitignore में — आपका उपयोगकर्ता नाम (इंस्टॉलेशन देखें)
│       ├── local.nix                # gitignore में — आपके निजी सिस्टम ओवरराइड
│       ├── local.nix.example        # शुरू करने के लिए इसे local.nix में कॉपी करें
│       └── hardware-configuration.nix
│
├── dotfiles/                        # Home Manager द्वारा प्रबंधित कच्ची कॉन्फ़िग फ़ाइलें
│   ├── easyeffects/                 # EasyEffects प्रीसेट
│   ├── fastfetch/
│   │   └── roudix.txt               # fastfetch के लिए डिफ़ॉल्ट Roudix ASCII लोगो
│   # niri/, niri-dms/ हटा दिए गए — niri कॉन्फ़िग अब पूरी तरह
│   # Nix-नेटिव है (नीचे modules/home/desktop/niri/ देखें)।
│   ├── hyprland/                    # Hyprland कॉन्फ़िग (Lua) — हर ग्राफ़िकल शेल के लिए एक ही ट्री
│   │   ├── hyprland.lua             # एंट्री पॉइंट: config/ के मॉड्यूल लोड करता है
│   │   └── config/
│   │       ├── shell.lua            # ROUDIX_HYPR_SHELL से शेल (noctalia / dms / caelestia) चुनता है
│   │       ├── shells/              # हर शेल के बाइंड और इंटीग्रेशन (noctalia.lua, dms.lua, caelestia.lua)
│   │       ├── binds/common.lua     # सभी शेल में साझा बाइंड
│   │       ├── rules/               # विंडो नियम (common.lua, apps.lua, gaming.lua)
│   │       ├── ws.lua               # साझा वर्कस्पेस तालिका (workspaces, binds और rules इस्तेमाल करते हैं)
│   │       ├── workspaces.lua       # वर्कस्पेस नियम
│   │       ├── monitors.lua / input.lua / layout.lua / decorations.lua / animations.lua
│   │       ├── defaults.lua / colors.lua / environment.lua / autostart.lua / misc.lua
│   │       └── nix-noctalia.lua     # लाइव Noctalia थीम लोड करता है (matugen द्वारा बनाई गई)
│   │   # config/nix-plugins.lua और config/nix-apps.lua Nix द्वारा बनाई जाती हैं (रिपॉज़िटरी में नहीं हैं)
│   └── perso/                       # निजी कॉन्फ़िग (gitignore में)
│
├── pkgs/
│   ├── roudix-branding              # Roudix ब्रांडिंग पैकेज
│   ├── roudix-kernel-switcher       # Roudix Kernel Switcher GUI पैकेज
│   ├── roudix-switcher/             # Roudix सेटिंग्स GUI (डेस्कटॉप, गेमिंग, एडिटर, टर्मिनल, ब्राउज़र, शेल, फ़ाइल मैनेजर, चैट, सिस्टम, इंटीग्रेशन)
│   └──   roudix-scheduler-switcher    # Scheduler Switcher GUI पैकेज
│
└── modules/
    ├── system/                      # NixOS सिस्टम-स्तर के मॉड्यूल
    │   ├── desktop/                 # डेस्कटॉप एनवायरनमेंट मॉड्यूल (NixOS-स्तर)
    │   │   ├── default.nix          # डेस्कटॉप विकल्प (roudix.desktop.type + roudix.desktop.shell)
    │   │   └── niri.nix / hyprland.nix / gnome.nix / kde.nix / mangowc.nix / umbriel.nix
    │   │
    │   ├── boot/                    # बूटलोडर, कर्नेल और CPU
    │   │   ├── boot.nix             # Limine/systemd-boot + मल्टी-OS एंट्री
    │   │   ├── boot.local.nix       # gitignore में — आपकी निजी बूट एंट्री
    │   │   ├── boot.local.nix.example
    │   │   ├── kernel.nix           # कर्नेल वैरिएंट का चुनाव — CachyOS वैरिएंट + सादा nixpkgs
    │   │   ├── cpu.nix              # Intel/AMD माइक्रोकोड + i2c मॉड्यूल
    │   │   └── bootloader/          # Limine वॉलपेपर एसेट
    │   │
    │   ├── apps/                    # ऐप-चयन मॉड्यूल (हर एक के लिए एक roudix.* विकल्प)
    │   │   ├── apps.nix / appimage.nix / flatpak.nix / browser.nix / discord.nix
    │   │   ├── telegram.nix / matrix.nix / mail-client.nix / music-player.nix
    │   │   ├── video-player.nix / torrent-client.nix / password-manager.nix
    │   │   └── filemanager.nix / editor.nix / terminal.nix / spicetify.nix / content-creation.nix
    │   │
    │   ├── virtualization/          # QEMU/KVM, कंटेनर, VM-गेस्ट ट्वीक, Waydroid
    │   │   └── virtualization.nix / containers.nix / vm-guest.nix / waydroid.nix
    │   │
    │   ├── rgb/                     # RGB कंट्रोलर रूटिंग
    │   │   ├── default.nix          # roudix.rgb विकल्प (openlinkhub / openrgb / none)
    │   │   └── openlinkhub.nix / openrgb.nix
    │   │
    │   ├── gaming/                  # Steam, Gamescope, ananicy-cpp, tuned-adm, SCX शेड्यूलर
    │   │   └── gaming.nix / scx.nix
    │   │
    │   ├── gpu/                     # GPU कॉन्फ़िगरेशन (AMD/NVIDIA/Intel/VM + mesa-git)
    │   │
    │   ├── autoupdate.nix       # कॉन्फ़िग बदलने पर स्वचालित git pull + रीबिल्ड
    │   ├── binary-caches.nix    # Nix बाइनरी कैश (substituters + भरोसेमंद कुंजियाँ)
    │   ├── common.nix           # साझा सिस्टम कॉन्फ़िग (सभी होस्ट)
    │   ├── desktop-integration.nix  # बिना DE वाले कंपोज़िटर के लिए कीरिंग + xdg-desktop-portal स्टैक
    │   ├── environment.nix      # एनवायरनमेंट वेरिएबल
    │   ├── fstrim.nix           # SSD/NVMe के लिए fstrim
    │   ├── hosts-gta.nix        # BattlEye होस्ट ब्लॉक (GTA फ़िक्स, वैकल्पिक)
    │   ├── icon-theme.nix       # पूरे सिस्टम की आइकन थीम का चुनाव
    │   ├── keyboard.nix         # ग्राफ़िकल (Wayland) कीबोर्ड लेआउट/वैरिएंट
    │   ├── pipewire.nix         # PipeWire ऑडियो + rnnoise नॉइज़ सप्रेशन
    │   ├── shell.nix            # डिफ़ॉल्ट शेल (fish/bash)
    │   ├── update.nix           # Flake अपडेट कॉन्फ़िगरेशन
    │   ├── roudix-update.nix    # `update` कमांड (pull + रीबिल्ड + Flatpak), स्क्रिप्ट roudix-update.sh में, शेल कम्प्लीशन completions/ में
    │   └── version.nix          # Roudix OS ब्रांडिंग (os-release, distroName)
    │   # टर्मिनल/फ़ाइल मैनेजर: hosts/roudix/ की local.nix से अपना पसंदीदा चुनें
    │
    └── home/                        # Home Manager के उपयोगकर्ता-स्तर के मॉड्यूल
        ├── common.nix               # साझा home कॉन्फ़िग (सभी उपयोगकर्ता और DE)
        ├── bash.nix                 # Bash शेल कॉन्फ़िग + roudix-switch + roudix-shell-switch
        ├── fastfetch.nix            # Fastfetch + fish ऑटोस्टार्ट
        ├── fish.nix                 # Fish शेल + एलियास + roudix-switch + roudix-shell-switch
        ├── gaming-home.nix          # उपयोगकर्ता के गेमिंग पैकेज (proton, mangohud...)
        ├── git.nix                  # Git कॉन्फ़िग
        ├── mangohud.nix             # MangoHud ओवरले (सभी DE में साझा)
        ├── papirus-icon.nix         # Papirus आइकन थीम (सभी DE में साझा)
        ├── papirus-folders.nix      # Papirus फ़ोल्डर रंग कॉन्फ़िगरेशन (साझा)
        ├── tela-icon.nix            # Tela आइकन थीम (सभी DE में साझा)
        ├── spicetify.nix            # Spotify + Spicetify (Comfy थीम)
        ├── ssh.nix                  # SSH + GitHub
        ├── shell-modules.nix        # साझा शेल मॉड्यूल इम्पोर्ट (noctalia, dms, caelestia)
        └── desktop/                 # हर DE के लिए एक फ़ोल्डर — Home Manager की तरफ़, modules/system/desktop/ की नक़ल
            ├── default.nix          # छहों बिना शर्त इम्पोर्ट करता है (हर एक अंदर से lib.mkIf से सुरक्षित है)
            ├── gnome/
            │   ├── default.nix      # वॉलपेपर, थीम, आइकन, कर्सर
            │   └── _extensions.nix  # GNOME एक्सटेंशन — पैकेज, चालू UUID, dconf सेटिंग्स
            ├── kde/default.nix      # plasma-manager कॉन्फ़िग (वॉलपेपर, पैनल, लॉक स्क्रीन)
            ├── hyprland/default.nix # शेल के अनुसार (noctalia/dms/caelestia), प्लगइन, पैकेज
            ├── mangowc/default.nix  # बनाए गए mango config.conf/apps.conf, पैकेज
            ├── niri/                # programs.niri.settings, विषय के अनुसार बँटा हुआ, शेल के अनुसार
            │   ├── default.nix      # सेटिंग्स जोड़ता है, लाइव-थीम include, पैकेज
            │   ├── _general.nix     # एनवायरनमेंट, ऑटोस्टार्ट, कर्सर (शेल के अनुसार)
            │   ├── _animation.nix
            │   ├── _input.nix
            │   ├── _layout.nix
            │   ├── _output.nix      # आउटपुट + नामित वर्कस्पेस
            │   ├── _ws.nix          # साझा वर्कस्पेस-आइकन ग्लिफ़ स्थिरांक
            │   ├── _rules-common.nix
            │   ├── _rules-noctalia.nix / _rules-dms.nix
            │   ├── _binds-noctalia.nix / _binds-dms.nix
            │   └── _include-noctalia.nix / _include-dms.nix  # niri-flake के रेंडर किए गए कॉन्फ़िग में लाइव-थीम `include` जोड़ता है
            └── umbriel/             # programs.umbriel.settings, विषय के अनुसार बँटा हुआ (केवल Noctalia)
                ├── default.nix
                ├── _general.nix / _appearance.nix / _animation.nix / _input.nix
                ├── _layout.nix / _output.nix / _binds.nix / _rules.nix
                └── _include-noctalia.nix  # noctalia.toml लोड करता है (Umbriel का नेटिव लाइव-थीम include)
```

---

## Flake इनपुट

| इनपुट | स्रोत |
|-------|--------|
| nixpkgs | [nixos-unstable](https://github.com/NixOS/nixpkgs/tree/nixos-unstable) |
| nixpkgs-stable | [nixos-26.05](https://github.com/NixOS/nixpkgs/tree/nixos-26.05) |
| niri | [epireyn/niri-flake](https://github.com/epireyn/niri-flake) |
| home-manager | [nix-community/home-manager](https://github.com/nix-community/home-manager) |
| noctalia | [noctalia-dev/noctalia](https://github.com/noctalia-dev/noctalia) |
| umbriel | [noctalia-dev/umbriel](https://github.com/noctalia-dev/umbriel) |
| caelestia-shell | [caelestia-dots/shell](https://github.com/caelestia-dots/shell) |
| dms | [AvengeMedia/DankMaterialShell](https://github.com/AvengeMedia/DankMaterialShell) |
| nix-cachyos-kernel | [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel) |
| chaotic | [chaotic-cx/nyx](https://github.com/chaotic-cx/nyx) |
| zen-browser | [0xc000022070/zen-browser-flake](https://github.com/0xc000022070/zen-browser-flake) |
| spicetify-nix | [Gerg-L/spicetify-nix](https://github.com/Gerg-L/spicetify-nix) |
| millennium | [SteamClientHomebrew/Millennium](https://github.com/SteamClientHomebrew/Millennium) |
| helium | [x13-me/helium-nix](https://github.com/x13-me/helium-nix) |
| nix-flatpak | [gmodena/nix-flatpak](https://github.com/gmodena/nix-flatpak) |
| plasma-manager | [nix-community/plasma-manager](https://github.com/nix-community/plasma-manager) |
| brave-previews | [roudinebwt/brave-preview](https://github.com/roudinebwt/brave-preview) |
| roudix-caches | [RoudineBWT/Roudix-caches](https://github.com/RoudineBWT/Roudix-caches) |
| nix-gaming-edge | [powerofthe69/nix-gaming-edge](https://github.com/powerofthe69/nix-gaming-edge) |
| betterbird-nix | [TheAnachronism/betterbird-nix](https://github.com/TheAnachronism/betterbird-nix) |
---

## यह भी देखें

| प्रोजेक्ट | विवरण |
|---------|-------------|
| [GLF OS](https://framagit.org/gaming-linux-fr/glf-os/glf-os) | Gaming Linux FR का NixOS-आधारित गेमिंग डिस्ट्रो |

---

## निजी dotfiles

निजी कॉन्फ़िग फ़ाइलें `dotfiles/perso/` में रहती हैं — वे gitignore में हैं (`dotfiles/perso/README.md` को छोड़कर) और `git pull` या ऑटो-अपडेटर उन्हें कभी नहीं छूते।

संरचना और उपयोग के लिए [`dotfiles/perso/README.md`](dotfiles/perso/README.md) देखें।

कंपोज़िटर-स्तर के ओवरराइड (मॉनिटर, कीबाइंड, गैप…) के लिए, इसके बजाय बनाई गई उपयोगकर्ता ओवरराइड फ़ाइलें इस्तेमाल करें — उन्हें home-manager संभालता है और वे `git pull` से सुरक्षित हैं। विवरण के लिए [डेस्कटॉप और शेल](docs/desktop.md#personal-compositor-overrides) देखें।

## डेवलपमेंट

```bash
nix develop     # dev shell: just, ruff, statix, deadnix, shellcheck, gettext
just            # कार्यों की सूची दिखाता है
just ci         # CI जो कुछ जाँचता है (हर होस्ट का मूल्यांकन, lint, Python, अनुवाद)
```

इंस्टॉलर का अनुवाद gettext से होता है — [इंस्टॉलर › अनुवाद](iso/roudix-installer/README.md#traductions) देखें।

## लाइसेंस
   MIT — देखें [LICENSE](LICENSE)। Roudix Store GPL-2.0-only है और कुछ
   थर्ड-पार्टी फ़ाइलें अपने-अपने लाइसेंस रखती हैं: देखें [THIRD_PARTY.md](THIRD_PARTY.md)।
