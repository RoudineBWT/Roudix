[English](desktop.md) · [Français](desktop.fr.md) · [Español](desktop.es.md) · [Português (Brasil)](desktop.pt_BR.md) · [Русский](desktop.ru.md) · [简体中文](desktop.zh_CN.md) · **हिन्दी** · [العربية](desktop.ar.md)

# डेस्कटॉप एनवायरनमेंट

`roudix-switch <de>` या **Roudix Customizer** GUI (`roudix-switcher` पैकेज) से किसी भी समय डेस्कटॉप बदलें — अलग होस्ट की ज़रूरत नहीं। यह GUI अब सिर्फ़ डेस्कटॉप बदलने से कहीं आगे बढ़ चुका है: एक ही ऐप में अब डेस्कटॉप, गेमिंग (प्रति-ऐप टॉगल), एडिटर, टर्मिनल, ब्राउज़र, लॉगिन शेल, फ़ाइल मैनेजर, चैट क्लाइंट (Discord/Matrix) और इंटीग्रेशन (keyring/portal स्टैक) सब शामिल हैं।

| मान | डेस्कटॉप | टिप्पणियाँ |
|-----|----------|------------|
| `niri` | Niri + (Noctalia, DMS) | डिफ़ॉल्ट — स्क्रॉल होने वाला टाइलिंग (scrollable tiling) Wayland |
| `hyprland` | Hyprland + (Noctalia, DMS, Caelestia) | डायनामिक टाइलिंग Wayland — UWSM के ज़रिए लॉन्च होता है |
| `mangowc` | MangoWC + (Noctalia, DMS) | Wayland कंपोज़िटर |
| `umbriel` | Umbriel + Noctalia | स्क्रॉल होने वाला टाइलिंग — Noctalia का अपना नेटिव कंपोज़िटर, सिर्फ़ Noctalia के साथ (शेल बदलना संभव नहीं) |
| `gnome` | GNOME | |
| `kde` | KDE Plasma 6 | plasma-login-manager, KDE Connect |
| `cinnamon` | Cinnamon | X11 सेशन + LightDM — क्लासिक डेस्कटॉप, पुराने हार्डवेयर के लिए उपयुक्त (GNOME 49 सिर्फ़ Wayland है) |
| `cosmic` | COSMIC | System76 का Wayland डेस्कटॉप (cosmic-comp), cosmic-greeter |

स्थायी रूप से बदलने के लिए `hosts/roudix/local.nix` संपादित करें:

```nix
roudix.desktop.type = "niri"; # "niri", "hyprland", "mangowc", "gnome", "kde", "cinnamon" या "cosmic"
```

या fish फ़ंक्शन का उपयोग करें — यह कॉन्फ़िग संपादित करता है और एक ही चरण में रीबिल्ड कर देता है:

```fish
roudix-switch kde
```

> **नोट:** `roudix-switch` `nh os boot` का उपयोग करता है — बदलाव अगले रीबूट पर लागू होते हैं।

---

## ग्राफ़िकल शेल (सिर्फ़ Niri, Hyprland और MangoWC)

Wayland कंपोज़िटर (Niri, Hyprland, MangoWC) के लिए आप शेल/बार स्टैक को कंपोज़िटर से अलग बदल सकते हैं। Hyprland के लिए **एक ही कॉन्फ़िगरेशन ट्री** (`dotfiles/hyprland/`) में साझा कीबाइंड होते हैं और वह `roudix.desktop.shell` से शेल चुनता है।

| मान | शेल | Hyprland |
|-----|-----|----------|
| `noctalia` | Noctalia | `dotfiles/hyprland/` |
| `dms` | Dux Shell | `dotfiles/hyprland/` |
| `caelestia` | Caelestia | `dotfiles/hyprland/` |

**नोट:** Caelestia सिर्फ़ Hyprland पर उपलब्ध है। शेल को `ROUDIX_HYPR_SHELL` के ज़रिए सेशन में इंजेक्ट किया जाता है, इसलिए अलग-अलग `hyprland-dms/` या `hyprland-caelestia/` ट्री नहीं हैं जिन्हें सिंक रखना पड़े।

### शेल ऑटोस्टार्ट

स्टार्टअप चुने गए शेल और कंपोज़िटर पर निर्भर करता है, और हर शेल के लिए ठीक एक ही स्टार्टअप तंत्र होता है:

- **Hyprland + Noctalia:** `hyprland.start` Lua हुक से `noctalia`।
- **Hyprland + Caelestia:** `hyprland.start` Lua हुक से `caelestia-shell`।
- **Hyprland + DMS:** DMS की यूज़र systemd सर्विस; Hyprland स्टार्टअप पर सेशन एनवायरनमेंट को systemd में एक्सपोर्ट करता है।
- **MangoWC + Noctalia:** MangoWC के `autostart_sh` से `noctalia`।
- **MangoWC + DMS:** DMS की यूज़र systemd सर्विस, जो `mango-session.target` के ज़रिए शुरू होती है; इसलिए MangoWC `dms run` नहीं चलाता।

DMS को systemd और कंपोज़िटर, दोनों से एक साथ शुरू नहीं किया जाना चाहिए: इसका आधिकारिक डॉक्यूमेंटेशन systemd सर्विस इस्तेमाल करने पर `dms run` हटाने की सलाह देता है।

बदलने के लिए `hosts/roudix/local.nix` संपादित करें:

```nix
roudix.desktop.shell = "noctalia"; # "noctalia", "dms" या "caelestia"
```

फिर रीबिल्ड करें:

```fish
rebuild
```

या fish फ़ंक्शन का उपयोग करें (सिर्फ़ Niri, Hyprland और MangoWC पर उपलब्ध) — यह कॉन्फ़िग संपादित करता है और एक ही चरण में रीबिल्ड कर देता है:

```fish
roudix-shell-switch dms
```

> **नोट:** `roudix-shell-switch` `nh os boot` का उपयोग करता है — बदलाव अगले रीबूट पर लागू होते हैं।

---

## nixpkgs या नवीनतम संस्करण (flake)

Niri, MangoWC और Umbriel हमेशा अपने ही flake से आते हैं। शेल (और उसके साथ आने वाले greeter) के लिए Roudix डिफ़ॉल्ट रूप से **nixpkgs** वाला संस्करण इस्तेमाल करता है। प्रोजेक्ट के अपने flake से बना सबसे नया संस्करण पाने के लिए, `local.nix` में हर कंपोनेंट के लिए इसे चालू करें — या `roudix-switcher` / इंस्टॉलर से, जहाँ यह स्विच सिर्फ़ आपके चुने हुए शेल के लिए दिखता है:

```nix
roudix.desktop.latest.noctalia  = true;  # Noctalia (+ noctalia-greeter)
roudix.desktop.latest.dms       = true;  # Dux Shell (+ dms-greeter)
roudix.desktop.latest.caelestia = true;  # Caelestia (DMS greeter इसके साथ चलता है)
```

Roudix में Hyprland का कोई flake संस्करण नहीं है: वह हमेशा nixpkgs से आता है।

> **ध्यान दें:** Roudix के कॉन्फ़िगरेशन **सबसे पहले flake (latest) संस्करणों के लिए** लिखे जाते हैं। nixpkgs संस्करणों पर, अगर कॉन्फ़िगरेशन एरर कहे कि कोई विकल्प, सेटिंग या कॉन्फ़िग कुंजी *मौजूद नहीं है*, तो यह **सामान्य** है: उसे nixpkgs द्वारा दिए जाने वाले संस्करण के बाद जोड़ा गया था। nixpkgs के अपडेट होने का इंतज़ार करें, या कंपोनेंट को `true` पर सेट करें।

> अगर कोई flake मॉड्यूल `package` विकल्प उपलब्ध नहीं कराता (DMS, MangoWC और DMS greeter के लिए संभव है), तो nixpkgs संस्करण लागू नहीं किया जा सकता: Roudix flake संस्करण पर ही रहता है और बिल्ड के समय चेतावनी प्रिंट करता है।

---

## व्यक्तिगत कंपोज़िटर ओवरराइड

Niri और Umbriel Nix में नेटिव रूप से कॉन्फ़िगर होते हैं (`programs.niri.settings` / `programs.umbriel.settings`) — ये असली, टाइप किए हुए attrset हैं, जनरेट की गई टेक्स्ट फ़ाइल नहीं। इसका मतलब है कि ओवरराइड बस Nix ही हैं: कोई ऐसी कुंजी जोड़ें जो अभी मौजूद नहीं है और वह अपने-आप मर्ज हो जाती है; अगर आप ऐसी कुंजी बदलते हैं जिसे रिपॉज़िटरी पहले से सेट करती है (वही आउटपुट, वही कीबाइंड) तो `lib.mkForce` चाहिए, वरना Nix «conflicting definitions» एरर के साथ बिल्ड करने से मना कर देगा।

MangoWC और Hyprland टेक्स्ट-आधारित ही रहते हैं (नीचे देखें)।

आप ओवरराइड सीधे `modules/home/local.nix` में रख सकते हैं, लेकिन अगर आप किसी एक कंपोज़िटर को बहुत कस्टमाइज़ कर रहे हैं तो अलग फ़ाइल चीज़ों को साफ़-सुथरा रखती है — `modules/home/local.nix` अपने-आप `modules/home/niri-custom.nix`, `modules/home/umbriel-custom.nix` और `modules/home/mango-custom.nix` इम्पोर्ट कर लेता है, अगर वे मौजूद हों (शुरू करने के लिए संबंधित `*.example` फ़ाइल कॉपी करें; ये `local.nix` की तरह gitignore में हैं)।

**Niri**

```nix
# ऐसा मॉनिटर बदलें जिसे niri-flake पहले से सेट करता है (lib.mkForce चाहिए)
# — असली कनेक्टर नाम के लिए सेशन में `niri msg outputs` चलाएँ
programs.niri.settings.outputs."Lenovo Group Limited Legion 27Q-10 UNA07260".mode =
  lib.mkForce { width = 3840; height = 2160; refresh = 144.0; };

# रिपॉज़िटरी द्वारा पहले से परिभाषित कीबाइंड को रीमैप करें (lib.mkForce चाहिए)
programs.niri.settings.binds."Mod+T" = lib.mkForce {
  action.spawn = [ "alacritty" ];
};

# ऐसा कीबाइंड जोड़ें जो अभी मौजूद नहीं है (mkForce की ज़रूरत नहीं)
programs.niri.settings.binds."Mod+Shift+V".action.spawn = [ "pavucontrol" ];

# विंडो रूल जोड़ें — सूचियाँ फ़ाइलों के बीच जुड़ जाती हैं (CONCATENATE), इसलिए यह बस
# रिपॉज़िटरी के रूल्स के ऊपर जुड़ जाता है, mkForce की ज़रूरत नहीं
programs.niri.settings.window-rules = [
  { matches = [ { app-id = "mpv"; } ]; open-floating = true; }
];
```

**Umbriel**

```nix
# आउटपुट बदलें (lib.mkForce चाहिए — असली नाम के लिए `umbriel outputs` चलाएँ)
programs.umbriel.settings.output."DP-1".mode = lib.mkForce "3840x2160@144";

# रिपॉज़िटरी द्वारा पहले से परिभाषित कीबाइंड को रीमैप करें
programs.umbriel.settings.keybinds."Mod+C" = lib.mkForce "spawn:some-command";

# ऐसा कीबाइंड जोड़ें जो अभी मौजूद नहीं है
programs.umbriel.settings.keybinds."Mod+Shift+V" = "spawn:pavucontrol";

# विंडो रूल जोड़ें
programs.umbriel.settings.window_rule = [
  { match.app_id = "^mpv$"; default_floating = true; }
];
```

**MangoWC** अब भी अपनी कॉन्फ़िग के बिल्कुल अंत में home-manager द्वारा जनरेट की गई एक व्यक्तिगत ओवरराइड फ़ाइल सोर्स करता है — **`git pull` इसे कभी नहीं छूता** — क्योंकि व्यवहार में उसके पास टाइप किया हुआ Nix स्कीमा नहीं है:

- MangoWC → `~/.config/mango/user.conf`

```nix
xdg.configFile."mango/user.conf".text = lib.mkForce ''
  monitorrule=name:DP-1,width:2560,height:1440,refresh:144,x:0,y:0,scale:1,vrr:1,rr:0,tearing:1
'';
```

चूँकि यह कुछ Nix पंक्तियों की जगह एक बड़ा टेक्स्ट ब्लॉक है, इसलिए यह अपनी अलग फ़ाइल में बेहतर बैठता है — `modules/home/mango-custom.nix.example` देखें।

**Hyprland अब `dotfiles/hyprland/` में मौजूद मॉड्यूलर Lua कॉन्फ़िगरेशन इस्तेमाल करता है।** एंट्री पॉइंट `dotfiles/hyprland/hyprland.lua` है, जो मॉनिटर, लेआउट, एनिमेशन, बाइंड, विंडो रूल और शेल इंटीग्रेशन के `config/` मॉड्यूल लोड करता है। Nix इस ट्री को जैसा है वैसा ही `~/.config/hypr/` में कॉपी करता है।

मौजूदा कॉन्फ़िगरेशन Hyprland 0.55+ को लक्षित करता है और नेटिव `dwindle`, `master` और `scrolling` लेआउट इस्तेमाल करता है। Nix मॉड्यूल एंट्री पॉइंट से पहले एक छोटा `config/nix-plugins.lua` लोडर जनरेट करता है; `borders-plus-plus` Roudix के साथ शामिल है। `dynamic_cursors` ब्लॉक वैकल्पिक रहता है और तभी लागू होता है जब वह प्लगइन मौजूद हो।

### Hyprland को कस्टमाइज़ करना

मशीन-विशिष्ट मान (`DP-1`/`DP-3` आउटपुट, प्राइमरी मॉनिटर, डिफ़ॉल्ट ऐप्स, कीबोर्ड आदि) `dotfiles/hyprland/config/` के अंतर्गत होते हैं। अगर आप अपना Hyprland सेटअप Roudix रिपॉज़िटरी में रखते हैं तो उन्हें सीधे संपादित करें।

ट्रैक की गई फ़ाइलों को बदले बिना व्यक्तिगत ओवरराइड के लिए `modules/home/local.nix` में `xdg.configFile."hypr/..."` और `lib.mkForce` का उपयोग करें।

> Lua कॉन्फ़िगरेशन बदलने के बाद `rebuild` चलाएँ। शेल या एनवायरनमेंट के बदलावों के लिए सेशन रीस्टार्ट की ज़रूरत पड़ सकती है।

> उदाहरणों की पूरी सूची के लिए `modules/home/niri-custom.nix.example`, `modules/home/umbriel-custom.nix.example`, `modules/home/mango-custom.nix.example` और `modules/home/local.nix.example` देखें।

---

## GNOME ओवरराइड

`roudix.desktop.type = "gnome"` इस्तेमाल करते समय एक्सटेंशन प्रबंधन `hosts/roudix/local.nix` में और दिखावट के ओवरराइड `modules/home/local.nix` में जाते हैं।

**डिफ़ॉल्ट एक्सटेंशन के ऊपर और एक्सटेंशन जोड़ें** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [
  pop-shell
];
```

**UUID से किसी डिफ़ॉल्ट एक्सटेंशन को अक्षम करें** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.disabledExtensions = [
  "arcmenu@arcmenu.com"
];
```

**दोनों को मिलाएँ — जैसे ArcMenu की जगह कोई दूसरा लॉन्चर लगाना** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [ pop-shell ];
roudix.gnome.disabledExtensions = [ "arcmenu@arcmenu.com" ];
```

**दिखावट हाथ से बदलना (अनुशंसित)**

Roudix GNOME की दिखावट (वॉलपेपर, डार्क थीम, आइकन, कर्सर, एक्सटेंशन सेटिंग्स) *डिफ़ॉल्ट* के रूप में देता है। सेटिंग्स, Tweaks या किसी एक्सटेंशन की प्राथमिकताओं में कुछ भी बदलें और वह आपका हो जाता है: रीबिल्ड उसे कभी वापस नहीं पलटता। Roudix के अपडेट सिर्फ़ उन सेटिंग्स के डिफ़ॉल्ट बदलते हैं जिन्हें आपने छुआ नहीं है।

**अपनी कॉन्फ़िग से कोई मान ज़बरदस्ती लागू करना** (`modules/home/local.nix`)

अगर आप किसी मान को डिक्लेरेटिव तरीके से पिन करना चाहते हैं, तो उसे home-manager से सेट करें। ऊपर वाले मैन्युअल तरीके से अलग, यह **हर** रीबिल्ड पर दोबारा लागू होता है और UI में आपके किए बदलावों को ओवरराइड कर देता है:
```nix
dconf.settings."org/gnome/desktop/background".picture-uri =
  "file:///home/youruser/Pictures/my-wallpaper.png";
dconf.settings."org/gnome/desktop/background".picture-uri-dark =
  "file:///home/youruser/Pictures/my-wallpaper-dark.png";
dconf.settings."org/gnome/desktop/interface".color-scheme = "prefer-light"; # या "prefer-dark"
dconf.settings."org/gnome/desktop/interface".icon-theme = "Papirus";
dconf.settings."org/gnome/desktop/interface".cursor-theme = "capitaine-cursors";
dconf.settings."org/gnome/desktop/interface".cursor-size = 32;
```
`lib.mkForce` की ज़रूरत नहीं: home-manager अब ये कुंजियाँ परिभाषित नहीं करता।

**किसी सेटिंग (या पूरे सेक्शन) के लिए Roudix के डिफ़ॉल्ट वापस पाना**
```sh
dconf reset /org/gnome/desktop/interface/icon-theme
dconf reset -f /org/gnome/shell/extensions/dash-to-panel/
```

> उपलब्ध सभी GNOME ओवरराइड विकल्पों के लिए `hosts/roudix/local.nix.example` और `modules/home/local.nix.example` देखें।

---

## KDE Plasma ओवरराइड

`roudix.desktop.type = "kde"` इस्तेमाल करते समय:

Roudix अपनी KDE दिखावट **सिर्फ़ एक बार** लागू करता है, हर रीबिल्ड पर कभी नहीं, इसलिए सिस्टम सेटिंग्स में आप जो भी बदलते हैं वह बना रहता है:

- **डार्क थीम, आइकन, कर्सर**: सिर्फ़ पहले लॉगिन पर लागू होते हैं, `~/.local/state/roudix/kde-theme-seeded` से सुरक्षित। जानबूझकर Roudix की दिखावट वापस पाने के लिए: `rm ~/.local/state/roudix/kde-theme-seeded` चलाएँ और लॉग आउट/इन करें।
- **स्टार्टअप पर NumLock, लॉक-स्क्रीन वॉलपेपर**: `/etc/xdg` में साधारण KConfig डिफ़ॉल्ट, जो आपके `~/.config` से नीचे रहते हैं और उसे कभी ओवरराइड नहीं करते।
- **वॉलपेपर और पैनल**: plasma-manager द्वारा पहले लॉगिन पर लागू होते हैं, और फिर तभी दोबारा चलते हैं जब Roudix खुद किसी अपडेट में उनकी परिभाषा बदले।

**अपनी कॉन्फ़िग से मान पिन करना** (`modules/home/local.nix`)

plasma-manager से आप जो भी सेट करते हैं वह **हर** रीबिल्ड पर दोबारा लागू होता है, इसलिए इसे सिर्फ़ उसी के लिए इस्तेमाल करें जिसे आप डिक्लेरेटिव रखना चाहते हैं:

**वॉलपेपर**
```nix
programs.plasma.workspace.wallpaper = lib.mkForce "/home/youruser/Pictures/wallpaper.jpg";
```

**कलर स्कीम / आइकन / कर्सर**
```nix
programs.plasma.workspace.colorScheme = "BreezeDark";
programs.plasma.workspace.iconTheme = "Papirus-Dark";
programs.plasma.workspace.cursor.theme = "capitaine-cursors-white";
```

**टास्कबार / पैनल**
```nix
programs.plasma.panels = lib.mkForce [
  {
    location = "bottom";
    widgets = [
      { kickoff.icon = "/path/to/your/icon.svg"; }
      "org.kde.plasma.icontasks"
      "org.kde.plasma.marginsseparator"
      "org.kde.plasma.systemtray"
      "org.kde.plasma.digitalclock"
      "org.kde.plasma.showdesktop"
    ];
  }
];
```

> `lib.mkForce` सिर्फ़ `wallpaper` और `panels` के लिए ज़रूरी है, जो अब भी `modules/home/desktop/kde/default.nix` में परिभाषित हैं।

## Cinnamon के डिफ़ॉल्ट

Cinnamon डिफ़ॉल्ट रूप से Roudix Kitsune वॉलपेपर के साथ आता है — डेस्कटॉप पर भी और LightDM लॉगिन स्क्रीन पर भी — मेनू आइकन के रूप में Roudix लोगो इस्तेमाल करता है, और पैनल में डिफ़ॉल्ट ब्राउज़र (`roudix.browsers` का पहला), Roudix Store और सेटिंग्स को पिन करता है। GTK4 / libadwaita ऐप्स डार्क थीम का पालन करते हैं। ये डिफ़ॉल्ट हैं: ये सिर्फ़ उसी पर लागू होते हैं जिसे उपयोगकर्ता ने नहीं बदला है। पैनल पिन (ब्राउज़र, Nemo, Roudix Store, सेटिंग्स) और मेनू आइकन ऐप्लेट के डिफ़ॉल्ट हैं, जो दो ऐप्लेट की पैच की हुई कॉपियों के रूप में दिए जाते हैं: Cinnamon का कुछ भी रीबिल्ड नहीं होता।

लॉगिन स्क्रीन (slick-greeter) के लिए कोई सेटिंग्स ऐप नहीं है। उसका वॉलपेपर इस तरह बदलें:

```bash
roudix-lightdm-wallpaper ~/Pictures/wallpaper.jpg   # रीबिल्ड की ज़रूरत नहीं
roudix-lightdm-wallpaper --reset                    # Kitsune पर वापस
```

पिन किए गए ऐप्स को `hosts/roudix/local.nix` में ओवरराइड करें:

```nix
roudix.desktop.cinnamon.pinnedApps = [ "firefox.desktop" "io.roudix.store.desktop" "cinnamon-settings.desktop" ];
```

## COSMIC के डिफ़ॉल्ट

COSMIC डिफ़ॉल्ट रूप से Roudix Kitsune वॉलपेपर और `roudix.keyboardLayout` / `roudix.keyboardVariant` / `roudix.keyboardOptions` का कीबोर्ड लेआउट लेकर आता है। डॉक Roudix में चुने गए ब्राउज़र (और अगर चालू हो तो Zen), COSMIC Files, आपका टर्मिनल, Roudix Store और COSMIC Settings को पिन करता है — वही विचार जो GNOME के dash और Plasma के टास्क मैनेजर का है। ऐप लाइब्रेरी में Roudix के हर ऐप (Store, Customizer, Kernel Switcher, Scheduler, Hardware Sync, Config, Welcome) को एक **Roudix** फ़ोल्डर में समूहित किया गया है और वे अब सिस्टम / यूटिलिटीज़ में सूचीबद्ध नहीं होते। COSMIC Store इंस्टॉल नहीं होता: उसकी जगह Roudix Store लेता है।

ये डिफ़ॉल्ट हैं, जो सिस्टम-व्यापी cosmic-config फ़ाइलों के रूप में दिए जाते हैं: ये सिर्फ़ उसी पर लागू होते हैं जिसे उपयोगकर्ता ने नहीं बदला है, और रीबिल्ड COSMIC Settings में किए गए किसी चुनाव को कभी नहीं पलटता।

COSMIC के अपने ऐप्स और पैनल डिफ़ॉल्ट रूप से Roudix कलर स्कीम इस्तेमाल करते हैं (`assets/cosmic/`, जो `assets/palette/Roudix.json` से जनरेट होती है और `modules/system/desktop/cosmic.nix` द्वारा सिस्टम डिफ़ॉल्ट के रूप में इंस्टॉल की जाती है, Home Manager शामिल नहीं)। सेटिंग्स > दिखावट में कोई दूसरी थीम या एक्सेंट चुनने पर वह इसे ओवरराइड कर देती है, और रीबिल्ड आपके चुनाव को कभी नहीं छूता। «वर्तमान थीम को GNOME ऐप्स पर लागू करें» (सेटिंग्स > डेस्कटॉप > दिखावट > आइकन और टूलकिट थीमिंग) डिफ़ॉल्ट रूप से चालू है: COSMIC खुद अपनी थीम एक्सपोर्ट करता है, इसलिए GTK ऐप्स (ब्राउज़र, Roudix के ऐप्स...) को adw-gtk3 के ऊपर Roudix के रंग मिलते हैं, Roudix द्वारा लिखे गए किसी CSS के बिना। आइकन Papirus-Roudix हैं (`roudix.iconTheme` देखें), और आपके टर्मिनल को भी हर दूसरे डेस्कटॉप की तरह उसकी Roudix कलर स्कीम मिलती है।

`system76-scheduler`, जिसे nixpkgs का COSMIC मॉड्यूल चालू करता है, डिफ़ॉल्ट रूप से बंद है क्योंकि Roudix का अपना शेड्यूलर स्टैक (SCX) है। इसे रखने के लिए:

```nix
services.system76-scheduler.enable = true;
```

पिन किए गए ऐप्स बदलने के लिए बस डॉक से पिन / अनपिन करें: आपका चुनाव डिफ़ॉल्ट पर भारी पड़ता है।
