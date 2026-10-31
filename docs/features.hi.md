[English](features.md) · [Français](features.fr.md) · [Español](features.es.md) · [Português (Brasil)](features.pt_BR.md) · [Русский](features.ru.md) · [简体中文](features.zh_CN.md) · **हिन्दी** · [العربية](features.ar.md)

# सुविधाएँ

## कर्नेल और परफ़ॉर्मेंस

- NTSync सक्षम CachyOS कर्नेल (`ntsync` मॉड्यूल)
- दो कर्नेल प्रदाता, जो `hardware.myGpu` के आधार पर अपने-आप चुने जाते हैं:
  - AMD/Intel → [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel), 36 वैरिएंट (`hardware.myKernel`)
  - Nvidia → Chaotic-Nyx, 4 वैरिएंट (`hardware.myKernelChaotic`) — `nvidia_cachyos` देता है, जो उनके कर्नेल से मेल खाता पहले से कंपाइल किया हुआ ड्राइवर है, इसलिए कर्नेल अपडेट पर Nvidia मॉड्यूल को लोकल रूप से दोबारा नहीं बनाना पड़ता
- सादे nixpkgs कर्नेल भी दोनों प्रदाताओं पर चुने जा सकते हैं, CachyOS ओवरले से पूरी तरह बाहर — `zen` (`linuxPackages_zen`), `nixpkgs-lts`, `nixpkgs-latest`, `nixpkgs-testing` (RC/mainline), `xanmod-lts` / `xanmod-latest` (XanMod)। Nvidia पर ये लोकल रूप से दोबारा बनाए गए Nvidia मॉड्यूल पर लौट आते हैं (`nvidia_cachyos` कैश नहीं मिलता)
- `hardware.myKernelSource` (`nixpkgs` / `master` / `staging-next`) सिर्फ़ इन्हीं nixpkgs कर्नेल को ज़्यादा नए nixpkgs से लेता है ताकि कर्नेल अपडेट जल्दी मिलें, और बाकी सिस्टम को छुए बिना
- ZRAM सक्षम (100% RAM, zstd, swappiness 150)
- zswap अक्षम
- CPU माइक्रोकोड अपने-आप कॉन्फ़िगर होता है (Intel या AMD)
- Intel: `split_lock_detect=off` अपने-आप लागू होता है
- ananicy-cpp सक्षम (प्रोसेस प्रायोरिटी डेमन, CachyOS नियम)
- SCX शेड्यूलर सपोर्ट — लाइव स्विचिंग, रीबूट की ज़रूरत नहीं (bpfland, lavd, flash, p2dq, rusty…) Kernel Switcher GUI के ज़रिए — `scx-switch` के ज़रिए सिर्फ़ एक बार पासवर्ड पूछा जाता है और ananicy-cpp को रोकना/शुरू करना तथा शेड्यूलर बदलना एक साथ हो जाता है — **नोट:** SCX रीबूट के बाद बना नहीं रहता; रीबूट के बाद ananicy-cpp अपने-आप दोबारा शुरू हो जाता है और शेड्यूलर को Kernel Switcher GUI से फिर से लागू करना पड़ता है

## बूट

- Limine बूटलोडर (डिफ़ॉल्ट) — आधुनिक, तेज़, मल्टी-डिस्क सपोर्ट के साथ — या systemd-boot, जिसे `roudix.boot.bootloader` से चुना जा सकता है
- UEFI एंट्री का नाम अपने-आप "Roudix" में बदल जाता है
- मल्टी-OS बूट मेन्यू (Windows, अलग ESP पर मौजूद अन्य Linux डिस्ट्रो)
- बूट लेबल में Roudix का नाम + NixOS रिलीज़ वर्ज़न दिखता है

## गेमिंग

- Steam + Proton-GE + Proton-CachyOS (x86_64-v3) + Gamescope (gamescope-wsi, सेशन डिफ़ॉल्ट रूप से अक्षम)
- OBS कैप्चर के एनवायरनमेंट वेरिएबल पहले से कॉन्फ़िगर हैं (`environment.sessionVariables` के ज़रिए `OBS_VKCAPTURE`)
- कस्टम हॉरिज़ॉन्टल MangoHud ओवरले (`Powered By Roudix` लेबल)
- कंट्रोलर सपोर्ट (Steam Hardware + game-devices-udev-rules)
- Wine/Steam के लिए 32-बिट सपोर्ट
- `game-performance` रैपर — गेम चलने के दौरान एक समर्पित `tuned-adm` परफ़ॉर्मेंस प्रोफ़ाइल पर स्विच करता है, जिसे `systemd-run --user --scope` cgroup के ज़रिए ट्रैक किया जाता है (ताकि Steam के दोबारा fork/डिटैच होने पर भी यह बना रहे) और बाहर निकलने पर पुरानी स्थिति बहाल हो जाती है (उपयोग: Steam लॉन्च विकल्पों में `game-performance %command%`) — GameMode जानबूझकर अक्षम है (यहाँ ananicy-cpp के साथ असंगत)
- `ffmpegthumbnailer` पूरे सिस्टम में उपलब्ध (फ़ाइल मैनेजर में वीडियो थंबनेल)
- KDE पर `protonup-qt`, अन्य डेस्कटॉप एनवायरनमेंट पर `protonplus`
- Heroic, Lutris, Faugus Launcher, Prism Launcher (Minecraft, या विकल्प के तौर पर Modrinth App — `roudix.gaming.apps.modrinth.enable`) और Vintage Story (roudix-caches के ज़रिए)
- हर गेमिंग ऐप को `roudix.gaming.apps.<lutris|heroic|faugus|prismlauncher|vintagestory|mangohud>.enable` से अलग-अलग चालू/बंद किया जा सकता है (सभी डिफ़ॉल्ट रूप से `true`)
- वैकल्पिक [Millennium](https://github.com/SteamClientHomebrew/Millennium) मॉडिफ़ाइड Steam क्लाइंट (थीम + प्लगइन) — डिफ़ॉल्ट रूप से बंद, `roudix.gaming.steam.millennium.enable = true` से (या इंस्टॉलर से) चालू करें। यह अनौपचारिक मॉड है; `game-performance` का सैंडबॉक्स ट्वीक और Proton कम्पैटिबिलिटी टूल काम करते रहते हैं, और इसे वापस `false` करने पर सामान्य Steam बहाल हो जाता है
- वैकल्पिक कंसोल जैसा गेमिंग मोड: `roudix.gaming.gamescopeSession.enable` लॉगिन स्क्रीन पर एक "Steam (Gaming Mode)" सेशन जोड़ता है (gamescope के अंदर Steam Big Picture, VRR/HDR/MangoApp, लॉन्च के समय रीफ़्रेश रेट पहचानी जाती है)। Steam में "डेस्कटॉप पर स्विच करें" आपका डेस्कटॉप खोलता है, और "Return to Gaming Mode" ऐप लॉगिन स्क्रीन से गुज़रे बिना वापस गेम में ले जाता है। GLF-OS पर आधारित; niri, umbriel, GNOME, KDE, Hyprland और MangoWC को सपोर्ट करता है
- वैकल्पिक Decky Loader (Steam प्लगइन) `roudix.gaming.gamescopeSession.decky.enable` के ज़रिए, Jovian-NixOS के flake input से लिया जाता है (अपडेट के लिए `nix flake update jovian`, हाथ से sha संभालने की ज़रूरत नहीं); कोई बाइनरी कैश नहीं है, इसलिए पहली रीबिल्ड पर यह लोकल रूप से कंपाइल होता है

## डेस्कटॉप (Niri)

- Niri स्क्रॉल होने वाला टाइलिंग Wayland कंपोज़िटर — [niri-flake](https://github.com/epireyn/niri-flake) (epireyn) के ज़रिए उपलब्ध, डिफ़ॉल्ट रूप से `niri-unstable` का उपयोग, और `niri-epireyn.cachix.org` बाइनरी कैश पहले से कॉन्फ़िगर
- कॉन्फ़िग Nix-नेटिव है (`programs.niri.settings`), विषय के अनुसार बँटा हुआ (general, animations, input, layout, outputs, binds, rules) और बिल्ड के समय `niri validate` से जाँचा जाता है — टूटा हुआ कॉन्फ़िग बिल्ड को फ़ेल करता है, लॉगिन पर कंपोज़िटर को नहीं
- Noctalia/DMS का लाइव थीम सिंक (matugen/DMS से बने रंग, alt-tab, ब्लर) जनरेट किए गए कॉन्फ़िग में एक `include` जोड़कर सुरक्षित रखा जाता है, उसे स्थिर रूप से बेक करके नहीं
- Noctalia (v5) आधुनिक शेल
- xdg-desktop-portal-gnome + gtk (screencast और रिमोट डेस्कटॉप पोर्टल कॉन्फ़िगर)
- Bibata Modern Ice कर्सर (24 px)
- adw-gtk3 + Papirus आइकन + Papirus Folders
- gnome-libsecret / kwallet6 के साथ Element Desktop (डेस्कटॉप एनवायरनमेंट के अनुसार अपने-आप पहचाना जाता है)
- GNOME Polkit एजेंट
- DMS Greeter (greetd)

## डेस्कटॉप (MangoWC)

- MangoWC Wayland कंपोज़िटर
- Noctalia / Dux Shell
- xdg-desktop-portal-gtk
- Bibata Modern Ice कर्सर (24 px)
- GNOME Polkit एजेंट
- Ly डिस्प्ले मैनेजर
- adw-gtk3 + Papirus आइकन + Papirus Folders
- ज़ूम ओपन एनीमेशन + आधिकारिक bezier कर्व
- गेमिंग मॉनिटर पर VRR + टियरिंग सक्षम (DP-1 1440p@240)
- grim + slurp + satty (एनोटेशन) से स्क्रीनशॉट — 3 कीबाइंड
- rofi विंडो स्विचर (Alt+Tab)
- XDG Desktop Portal एनवायरनमेंट वेरिएबल पहले से कॉन्फ़िगर (Pipewire स्क्रीन कैप्चर, OBS, Discord Go Live)
- सभी गेमिंग ऐप (Steam, Heroic, Minecraft, Lutris, Bottles) पर force_tearing + idleinhibit_when_focus
- बिना फ़ोकस वाली विंडो की अपारदर्शिता (0.85)
- Hotarea overview (कोने में माउस जेस्चर)
- फ़्लोटिंग snap + टाइल से टाइल में ड्रैग
- Scratchpad सपोर्ट: किसी भी विंडो के लिए एक सामान्य पूल (मूव/टॉगल/रीस्टोर),
  साथ में हर ऐप के लिए एक वैकल्पिक (`roudix.mangowc.scratchpadApps`) नामित scratchpad —
  Discord/Element/Telegram/Spotify के लिए — हर एक की अपनी टॉगल कुंजी

## डेस्कटॉप (Umbriel)

- Umbriel स्क्रॉल होने वाला टाइलिंग Wayland कंपोज़िटर — Noctalia का अपना नेटिव कंपोज़िटर, [noctalia-dev/umbriel](https://github.com/noctalia-dev/umbriel) के ज़रिए उपलब्ध (सिर्फ़ Noctalia के लिए, शेल बदलने की सुविधा नहीं)
- कॉन्फ़िग Nix-नेटिव है (`programs.umbriel.settings`), विषय के अनुसार बँटा हुआ (general, appearance, animation, input, layout, outputs, binds, rules) और बिल्ड के समय जाँचा जाता है (`validateConfig = true`)
- Noctalia का लाइव थीम सिंक (matugen से बने रंग) Umbriel के नेटिव `include.files` तंत्र के ज़रिए सुरक्षित रहता है, रंगों का कोई स्थिर स्नैपशॉट नहीं
- Bibata Modern Ice कर्सर (24 px)
- adw-gtk3 + Papirus आइकन + Papirus Folders
- Hot corners (माउस को कोने में ले जाने पर overview) और वर्कस्पेस ओवरव्यू (Mod+O)
- Scratchpad सपोर्ट (ज़रूरत पर फ़्लोटिंग विंडो को मूव/टॉगल/रीस्टोर करें)
- हर वर्कस्पेस के लिए अलग लेआउट ओवरराइड (जैसे गेमिंग वर्कस्पेस पर कोई gap नहीं)

## डेस्कटॉप (Hyprland)

- Hyprland डायनामिक टाइलिंग Wayland कंपोज़िटर, UWSM के ज़रिए लॉन्च
- Noctalia आधुनिक शेल
- xdg-desktop-portal-hyprland + gtk पोर्टल
- Bibata Modern Ice कर्सर (24 px)
- GNOME Polkit एजेंट (systemd यूज़र सर्विस के ज़रिए शुरू)
- awww वॉलपेपर डेमन
- grim + slurp + satty (एनोटेशन) से स्क्रीनशॉट — 3 कीबाइंड

## डेस्कटॉप (GNOME)

- GNOME (nixos-unstable ब्रांच को फ़ॉलो करता है)
- चुने हुए एक्सटेंशन का सेट (blur, tiling, vitals, arcmenu...) — dconf के ज़रिए सक्षम
- मेन्यू बटन आइकन के रूप में Roudix लोगो के साथ ArcMenu
- `environment.gnome.excludePackages` से फ़ालतू सॉफ़्टवेयर हटाए गए
- Papirus-Dark आइकन थीम
- adw-gtk3-dark GTK थीम (डिफ़ॉल्ट रूप से डार्क मोड)
- Bibata Modern Ice कर्सर (24 px)
- Roudix वॉलपेपर (सिस्टम थीम के अनुसार लाइट/डार्क)
- `color-scheme = prefer-dark` dconf के ज़रिए लागू
- एक्सटेंशन सेटिंग (ArcMenu, Dash to Dock, Dash to Panel, Blur My Shell...) `modules/home/desktop/gnome/_extensions.nix` के ज़रिए पहले से कॉन्फ़िगर
- मुख्य फ़ाइलें बदले बिना `roudix.gnome.extraExtensions` / `roudix.gnome.disabledExtensions` से एक्सटेंशन जोड़ें/हटाएँ
- वॉलपेपर, थीम, आइकन और कर्सर को `modules/home/local.nix` में ओवरराइड करें

## डेस्कटॉप (KDE)

- plasma-login-manager के साथ KDE Plasma 6 (Plasma 6.6+, nixpkgs unstable)
- KDE Connect सक्षम
- xdg-desktop-portal-kde
- Papirus-Dark आइकन थीम
- Breeze Dark लुक एंड फ़ील + कलर स्कीम
- लॉगिन स्क्रीन और डेस्कटॉप पर Roudix Dark वॉलपेपर
- चुने हुए पैकेज: partitionmanager, kcalc, digikam, vlc...
- फ़ालतू सॉफ़्टवेयर हटाए गए (Discover शामिल नहीं)
- वॉलपेपर, पैनल और आइकन थीम को `modules/home/local.nix` में ओवरराइड करें

## संगीत

`roudix.musicPlayer` से एक चुनें — `"spotify"` (डिफ़ॉल्ट), `"ytmdesktop"`,
`"sonora"` या `"none"`।

- `"spotify"` — Spicetify से पैच किया गया Spotify। लोकल थीम, डिफ़ॉल्ट रूप से "colorful"
  (या "comfy"), साथ में विज्ञापन-ब्लॉक और पॉडकास्ट छिपाने वाले एक्सटेंशन — नीचे
  दिए गए टॉगल देखें।
- `"ytmdesktop"` — YouTube Music Desktop App (अनौपचारिक, Electron-आधारित
  YouTube Music क्लाइंट)।
- `"sonora"` — [Sonora](https://github.com/sonorahq/sonora), एक नेटिव
  (Rust/GPUI) क्लाइंट, जिसमें Spotify, YouTube Music, Apple Music, Deezer और
  Subsonic एक ही ऐप में मिलते हैं। वैकल्पिक `roudix.sonora.provider` तय करता है कि वह
  किस प्रदाता पर शुरू हो (`"youtube"` = YouTube Music)। यह सब्सक्रिप्शन को बायपास नहीं
  करता: अगर किसी सर्विस को सब्सक्रिप्शन चाहिए, तो Sonora को भी चाहिए।

## वैकल्पिक सामान्य ऐप

GIMP, Inkscape, SongRec और EasyEffects (+ rnnoise-plugin) डिफ़ॉल्ट रूप से शामिल हैं, लेकिन
हर एक को `roudix.apps.<name>.enable` (`gimp`,
`inkscape`, `songrec`, `easyeffects`) से अलग-अलग बंद किया जा सकता है।

Signal और ZapZap (WhatsApp का अनौपचारिक, नेटिव जैसा लगने वाला डेस्कटॉप क्लाइंट)
के बीच बदलने के लिए कोई असली विकल्प नहीं है, इसलिए ये सीधे opt-in बूलियन हैं,
डिफ़ॉल्ट रूप से बंद: `roudix.apps.signal.enable` और `roudix.apps.zapzap.enable`।

Fluxer, Discord का एक सेल्फ़-होस्ट किया जा सकने वाला विकल्प, इसी तरह का opt-in
बूलियन है: `roudix.apps.fluxer.enable`। यह अभी nixpkgs में नहीं है, इसलिए इसे सीधे
`nix-gaming-edge` flake input के पहले से बने `fluxer-desktop` पैकेज से लिया जाता है।
यह जानबूझकर `roudix.discord` और `roudix.gaming.enable` से स्वतंत्र है — कोई भी
Discord और Fluxer दोनों चाह सकता है, या बिना किसी गेमिंग सेटअप के सिर्फ़ Fluxer।

एक मेल क्लाइंट और एक पासवर्ड मैनेजर भी उपलब्ध हैं, opt-in (डिफ़ॉल्ट रूप से बंद):
`roudix.mailClient` — `"thunderbird"` (पूरी सुविधाओं वाला),
`"betterbird"` (बारीकी से ट्यून किया गया Thunderbird फ़ोर्क, जिसे
[betterbird-nix](https://github.com/TheAnachronism/betterbird-nix) flake
input से लिया जाता है — अभी nixpkgs में नहीं है) या `"geary"` (हल्का GNOME क्लाइंट);
`roudix.passwordManager` —
`"bitwarden"` (क्लाउड-सिंक), `"keepassxc"` (लोकल, ऑफ़लाइन वॉल्ट) या
`"protonpass"` (क्लाउड-सिंक, Proton अकाउंट)।

इसके अलावा उपलब्ध, opt-in (डिफ़ॉल्ट रूप से बंद): `roudix.torrentClient` के ज़रिए
टोरेंट क्लाइंट — `"qbittorrent"` (सुविधाओं से भरपूर, Qt-आधारित),
`"fragments"` (न्यूनतम GNOME/libadwaita क्लाइंट), `"deluge"` (प्लगइन-आधारित) या
`"none"` (डिफ़ॉल्ट)।

## Spicetify

- थीम: `roudix.spicetify.theme` — `"colorful"` (डिफ़ॉल्ट, sanoojes/spicetify-colorful) या `"comfy"` (साथ में आने वाली Comfy थीम)
- कलर स्कीम: `roudix.spicetify.colorScheme` — `null` (डिफ़ॉल्ट) थीम की अपनी डिफ़ॉल्ट स्कीम इस्तेमाल करता है (colorful के लिए "noctalia", comfy के लिए "Comfy")
- एक्सटेंशन अलग-अलग चालू/बंद किए जा सकते हैं: `roudix.spicetify.extensions.adblock.enable`, `roudix.spicetify.extensions.hidePodcasts.enable` (दोनों डिफ़ॉल्ट रूप से `true`)
- Marketplace कस्टम ऐप: `roudix.spicetify.marketplace.enable` (डिफ़ॉल्ट `true`)

## ब्राउज़र

- `roudix.browsers` विकल्प से कॉन्फ़िगर की जा सकने वाली ब्राउज़र सूची
- `brave`, `helium` (x13-me/helium-nix के ज़रिए, DRM पैच शामिल — `helium` चुनने पर Widevine प्लेबैक `modules/home/apps/browser/helium-widevine.nix` के ज़रिए अपने-आप जुड़ जाता है), `vivaldi` (ffmpeg कोडेक के साथ), `firefox`, `librewolf`, `chromium`, या कोई भी न चाहिए तो `[]` को सपोर्ट करता है
- Zen Browser `roudix.zen.enable = true` से अलग से उपलब्ध (डिफ़ॉल्ट रूप से बंद); चैनल `roudix.zen.variant` से चुना जा सकता है — `"twilight"` (डिफ़ॉल्ट) या `"beta"`

## अन्य

- Discord को `roudix.discord` से चुना जा सकता है — `"vencord"` (पैच किया हुआ क्लाइंट, डिफ़ॉल्ट), `"vanilla"` (बिना पैच) या `"none"` (इंस्टॉल नहीं)
- Telegram को `roudix.telegram` से चुना जा सकता है — `"telegram"` (आधिकारिक Telegram Desktop), `"ayugram"` (अनौपचारिक फ़ोर्क: घोस्ट मोड, anti-recall, लोकल मैसेज हिस्ट्री...) या `"none"` (डिफ़ॉल्ट, इंस्टॉल नहीं)
- कोड एडिटर को `roudix.editor` से चुना जा सकता है — `"zed"` (डिफ़ॉल्ट), `"vscode"`, `"neovim"` या `"none"` (अपना खुद मैनेज करें, जैसे AppImage/Flatpak)
- ग्राफ़िकल (Wayland) कीबोर्ड लेआउट `roudix.keyboardLayout` / `roudix.keyboardVariant` से (XKB, जैसे `"be"` / `"intl"`) — `console.keyMap` से स्वतंत्र, जो ग्राफ़िकल सेशन शुरू होने से पहले सिर्फ़ TTY को कवर करता है; GNOME/KDE पर इसका कोई असर नहीं, क्योंकि वे अपना लेआउट खुद मैनेज करते हैं
- "बेयर" कंपोज़िटर (Niri, Hyprland, MangoWC, Umbriel) के लिए keyring + xdg-desktop-portal स्टैक `roudix.desktopIntegration` से चुना जा सकता है — `"gnome"` (gnome-keyring + xdg-desktop-portal-gtk/-gnome, डिफ़ॉल्ट) या `"kde"` (KWallet + xdg-desktop-portal-kde + polkit-kde-agent, और GNOME ऐप की जगह Kate / Gwenview / KDE Partition Manager / Dolphin; adw-gtk3, nwg-look, qt6ct और gvfs बने रहते हैं ताकि GTK ऐप पर थीम लगी रहे); GNOME/KDE सेशन पर इसका कोई असर नहीं, वे अपना नेटिव स्टैक रखते हैं
- `nix-ld` पूरे सिस्टम में सक्षम — बिना पैच किए डायनामिक बाइनरी बिना FHS एनवायरनमेंट के चलाएँ (आम लाइब्रेरी के साथ पहले से कॉन्फ़िगर: glibc, openssl, zlib, libGL, X11, libxkbcommon, dbus, glib और अन्य)
- OBS Studio, `roudix.contentCreation.obs.enable` से अलग से चालू/बंद (डिफ़ॉल्ट `true`), प्लगइन `roudix.contentCreation.obs.plugins.<name>.enable` से एक-एक करके चालू/बंद (`vkcapture` + `pipewireAudioCapture` डिफ़ॉल्ट रूप से चालू; इनके अलावा उपलब्ध: `backgroundRemoval`, `moveTransition`, `aitumMultistream`, `gstreamer`, `compositeBlur`, `advancedSceneSwitcher`, `inputOverlay`, `waveform`)
- वीडियो एडिटर `roudix.contentCreation.videoEditor` से चुना जा सकता है — `"kdenlive"` (डिफ़ॉल्ट), `"davinci-resolve"` (मुफ़्त), `"davinci-resolve-studio"` (पेड, लाइसेंस चाहिए), `"shotcut"` या `"none"`; जब `hardware.myGpu = "amd"` हो, तो DaVinci Resolve को अपने-आप AMD OpenCL ICD मिल जाता है
- OBS/DaVinci के लिए `v4l2loopback` वर्चुअल कैमरा अपने-आप सेट होता है (`roudix.contentCreation.virtualCamera.enable`, डिफ़ॉल्ट `true`)
- Chatterino2 Twitch चैट क्लाइंट, `roudix.contentCreation.streaming.chatterino.enable` से opt-in
- पूरा कंटेंट-क्रिएशन समूह `roudix.contentCreation.enable` से चालू/बंद किया जा सकता है
- GPU Screen Recorder
- AMD के लिए Mesa Git विकल्प — `local.nix` में `roudix.mesa.useGit = true` से प्रायोगिक/अत्याधुनिक Mesa चालू करें (डिफ़ॉल्ट: nixpkgs का स्थिर Mesa) — ⚠️ **प्रायोगिक**, nixpkgs की स्थिति के अनुसार बिल्ड फ़ेल हो सकता है
- AMD GPU स्थिरता के कर्नेल पैरामीटर अपने-आप लागू होते हैं (`mem_sleep_default=deep`, `amdgpu.gpu_recovery=1`, `amdgpu.lockup_timeout=1000`, `amdgpu.runpm=0`, `amdgpu.sg_display=0`) — RDNA2/RDNA3 पर अचानक फ़्रीज़ और स्लीप से जागने की समस्याएँ ठीक करते हैं
- RGB कंट्रोलर `roudix.rgb` से चुना जा सकता है — `openlinkhub` (Corsair iCUE Link / Commander, CI के ज़रिए अपने-आप अपडेट), `openrgb` (कई ब्रांड: Razer, ASUS, MSI…) या `none`
- सर्विस चलने के बाद OpenLinkHub का वेब UI [http://127.0.0.1:27003](http://127.0.0.1:27003) पर उपलब्ध है
- OpenLinkHub के ज़रिए DDR4/DDR5 RAM का RGB कंट्रोल — `roudix.memory.enable = true` से चालू करें, और `roudix.memory.type`, `roudix.memory.smBus` तथा `roudix.memory.sku` कॉन्फ़िगर करें (देखें `installation.hi.md`)
- rnnoise स्टीरियो नॉइज़ सप्रेशन के साथ PipeWire (nofail, LADSPA_PATH कम्पैट 26.05/26.11)
- Flathub रिमोट + रोज़ाना ऑटो-अपडेट के साथ Flatpak (nix-flatpak के ज़रिए)
- Blueman ब्लूटूथ मैनेजर
- Matrix क्लाइंट — `roudix.matrixClient` से कॉन्फ़िगर किया जा सकता है (`element`, `cinny` या `none`) — Element KDE पर अपने-आप kwallet6 और बाकी जगह gnome-libsecret चुनता है
- वीडियो प्लेयर `roudix.videoPlayer` से चुना जा सकता है — `"vlc"` (सबसे ज़्यादा फ़ॉर्मेट सपोर्ट, डिफ़ॉल्ट), `"clapper"` (आधुनिक GTK4 प्लेयर), `"mpv"` (+ yt-dlp, न्यूनतम/स्ट्रीमिंग), `"celluloid"` (mpv का GTK फ़्रंट-एंड) या `"none"`; हर डेस्कटॉप पर लागू होता है (पहले Clapper सिर्फ़ बेयर कंपोज़िटर पर हार्डकोड था, और साथ में डेस्कटॉप एनवायरनमेंट से स्वतंत्र एक अलग mpv टॉगल था)
- `appimage.nix` के ज़रिए AppImage सपोर्ट सक्षम
- Waydroid (Android कंटेनर) — वैकल्पिक, `roudix.waydroid.enable = true`
- QEMU/KVM + Virt-Manager (वैकल्पिक, `roudix.virtualization.enable`)
- vm-curator (वैकल्पिक, `roudix.virtualization.vmCurator.enable`) — virt-manager का Rust TUI विकल्प, QEMU को सीधे चलाता है (libvirt के बिना), 3D एक्सेलरेशन और GPU पासथ्रू सपोर्ट के साथ; इसे अलग से या libvirt स्टैक के साथ चालू किया जा सकता है
- VM गेस्ट ऑप्टिमाइज़ेशन मॉड्यूल (क्लिपबोर्ड शेयरिंग, ऑटो-रीसाइज़, QEMU एजेंट, Spice)
