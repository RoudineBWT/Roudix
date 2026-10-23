[English](aliases.md) · [Français](aliases.fr.md) · [Español](aliases.es.md) · [Português (Brasil)](aliases.pt_BR.md) · [Русский](aliases.ru.md) · [简体中文](aliases.zh_CN.md) · **हिन्दी** · [العربية](aliases.ar.md)

# एलियास और फ़ंक्शन

## हर जगह उपलब्ध

| एलियास | कार्य |
|-------|--------|
| `rebuild` | कॉन्फ़िगरेशन तुरंत लागू करें |
| `update` | कॉन्फ़िगरेशन pull करें, रीबिल्ड + switch करें, Flatpak अपडेट करें ([नीचे](#update) देखें) |
| `cleanup` | पुरानी जनरेशन हटाएँ + गार्बेज कलेक्शन |
| `noctalia-reload` | लॉग-आउट किए बिना Noctalia रीस्टार्ट करें |
| `dms-reload` | लॉग-आउट किए बिना Quickshell रीस्टार्ट करें |
| `caelista-reload` | लॉग-आउट किए बिना Quickshell रीस्टार्ट करें |
| `roudix-switch <de>` | डेस्कटॉप एनवायरनमेंट बदलें (अगले रीबूट पर लागू) |
| `roudix-kernel-switch <kernel>` | कर्नेल वैरिएंट बदलें (अगले रीबूट पर लागू) |

### `update`

[ऑटो-अपडेट](autoupdate.hi.md) का मैनुअल रूप: वही रिपॉज़िटरी, वही फ़ॉलो की जा रही ब्रांच, fast-forward-only का वही नियम (आपके लोकल कमिट कभी नहीं छुए जाते)। यह आपके सामान्य उपयोगकर्ता के रूप में चलता है और `sudo` का उपयोग केवल वहीं करता है जहाँ ज़रूरी हो।

1. फ़ॉलो की जा रही ब्रांच का `git pull --ff-only` (अगर आप किसी दूसरी ब्रांच पर हैं, जैसे फ़ीचर ब्रांच, तो छोड़ दिया जाता है)
2. `nh os switch` (या `--boot` के साथ `nh os boot`)
3. यूज़र और सिस्टम दोनों के Flatpak अपडेट, फिर इस्तेमाल न होने वाले रनटाइम हटाना (कभी घातक नहीं)

git से मिलने वाली `flake.lock` वही है जिसे CI पहले ही बना और जाँच चुका है, इसलिए साधारण `update` flake इनपुट **नहीं** बढ़ाता।

| विकल्प | प्रभाव |
|--------|--------|
| `-i`, `--inputs [name…]` | flake इनपुट भी लोकल रूप से बढ़ाएँ (सभी, या केवल बताए गए)। बिल्ड विफल होने पर `flake.lock` पहले जैसी कर दी जाती है |
| `-b`, `--boot` | अभी switch करने के बजाय अगले बूट पर लागू करें |
| `-c`, `--check` | केवल बताएँ कि नए कमिट उपलब्ध हैं या नहीं |
| `-n`, `--dry` | ड्राई रन (`nh --dry`): कुछ भी pull, बम्प, सक्रिय या अपडेट नहीं होता |
| `--changes` | दिखाएँ कि अगले बूट का सिस्टम चल रहे सिस्टम से कैसे अलग है (ऑटो-अपडेट के बाद काम आता है) |
| `--log` | आख़िरी रन का लॉग दिखाएँ (`~/.local/state/roudix/update.log` में रखा जाता है) |
| `--no-inputs` | इनपुट बम्प छोड़ दें (`roudix.update.bumpInputs = true` के साथ उपयोगी) |
| `--no-pull` / `--no-flatpak` | pull / Flatpak अपडेट छोड़ दें |

```fish
update                    # pull + रीबिल्ड + switch
update --inputs           # सभी इनपुट बढ़ाएँ, फिर रीबिल्ड करें
update --inputs nixpkgs   # केवल nixpkgs बढ़ाएँ
```

जिस मशीन पर `dev` फ़ॉलो होती है और हमेशा ताज़ा इनपुट चाहिए, वहाँ `local.nix` में `roudix.update.bumpInputs = true;` रखें: तब साधारण `update` भी `update --inputs` की तरह चलता है।

> `update --inputs` के बाद `flake.lock` एक लोकल बदलाव होती है: उसे commit और push करें (या `git checkout flake.lock`), वरना अगर इस बीच CI ने lock को छुआ हो, तो अगला ऑटो-अपडेट pull चलने से मना कर सकता है।

## केवल Niri, Hyprland और MangoWC के लिए

| एलियास | कार्य |
|-------|--------|
| `roudix-shell-switch <shell>` | ग्राफ़िकल शेल बदलें (अगले रीबूट पर लागू) |

### उपयोग

```fish
# डेस्कटॉप एनवायरनमेंट बदलें
roudix-switch niri
roudix-switch hyprland
roudix-switch mangowc
roudix-switch umbriel
roudix-switch gnome
roudix-switch kde

# कर्नेल वैरिएंट बदलें — सूची hardware.myGpu पर निर्भर करती है, देखें docs/installation.md
# AMD/Intel (xddxdd):
roudix-kernel-switch cachyos-latest-v3
roudix-kernel-switch cachyos-lts-lto-v3
roudix-kernel-switch cachyos-bore
# Nvidia (Chaotic-Nyx — छोटा सेट, nvidia_cachyos बाइनरी कैश के लिए ज़रूरी):
roudix-kernel-switch cachyos
roudix-kernel-switch cachyos-lts
# सादे nixpkgs कर्नेल — दोनों GPU रास्तों पर उपलब्ध, CachyOS ओवरले के बाहर
# (Nvidia पर ये लोकल रूप से दोबारा बने Nvidia मॉड्यूल पर लौट जाते हैं, nvidia_cachyos कैश के बिना):
roudix-kernel-switch zen
roudix-kernel-switch nixpkgs-lts
roudix-kernel-switch nixpkgs-latest
roudix-kernel-switch nixpkgs-testing
roudix-kernel-switch xanmod-lts
roudix-kernel-switch xanmod-latest

# ग्राफ़िकल शेल बदलें (केवल Niri, Hyprland और MangoWC)
roudix-shell-switch noctalia
roudix-shell-switch dms
roudix-shell-switch caelestia # केवल hyprland के लिए
```

तीनों कमांड `hosts/roudix/local.nix` को अपने-आप एडिट करते हैं और `nh os boot` चलाते हैं — हाथ से रीबिल्ड करने की ज़रूरत नहीं। बदलाव अगले रीबूट पर लागू होते हैं।

> **नोट:** `roudix-kernel-switch` आपके मौजूदा `hardware.myGpu` के आधार पर अपने-आप `hardware.myKernel` या `hardware.myKernelChaotic` में लिखता है — अपनी GPU की सूची के अनुसार वैरिएंट का नाम दें (ऊपर की तालिका देखें)।
