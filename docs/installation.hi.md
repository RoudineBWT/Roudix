[English](installation.md) · [Français](installation.fr.md) · [Español](installation.es.md) · [Português (Brasil)](installation.pt_BR.md) · [Русский](installation.ru.md) · [简体中文](installation.zh_CN.md) · **हिन्दी** · [العربية](installation.ar.md)

# इंस्टॉलेशन

आपकी शुरुआती स्थिति के अनुसार Roudix चलाने के तीन तरीके हैं:

| स्थिति | क्या इस्तेमाल करें |
|-----------|-----|
| नई मशीन, अभी कुछ इंस्टॉल नहीं | **Roudix ISO** — सीधे ग्राफ़िकल इंस्टॉलर में बूट होता है (पार्टिशनिंग शामिल) |
| NixOS पहले से इंस्टॉल है (आधिकारिक ISO, किसी दूसरे डिस्ट्रो का NixOS इंस्टॉल, VM…) | **`roudix-installer.sh`** — आपके मौजूदा इंस्टॉल पर Roudix flake लगाता है |
| आप हर चरण पर पूरा नियंत्रण चाहते हैं, या स्क्रिप्ट आपका मामला कवर नहीं करती | **मैनुअल इंस्टॉलेशन** (नीचे) |

## विकल्प A — Roudix ISO (नए इंस्टॉल के लिए अनुशंसित)

ISO में हमारा अपना GTK4/libadwaita ग्राफ़िकल इंस्टॉलर (`roudix-installer`) एक लाइव GNOME सेशन के ऊपर आता है, और डिस्क पार्टिशनिंग [disko](https://github.com/nix-community/disko) से अपने-आप संभालता है — पहले से NixOS इंस्टॉल होना ज़रूरी नहीं।

1. नवीनतम ISO लें: रिपॉज़िटरी के **Actions** टैब पर जाएँ → **💿 Build Roudix ISO** वर्कफ़्लो → अगर हाल का कोई बिल्ड सूची में नहीं है तो उसे चलाएँ (`workflow_dispatch`), फिर रन खोलकर जॉब सारांश में दिया डाउनलोड लिंक लें (ISO Cloudflare R2 पर होस्ट है, GitHub आर्टिफ़ैक्ट के रूप में नहीं)।
2. इसे USB ड्राइव पर फ़्लैश करें (जैसे `dd`, Ventoy, Rufus…) और उससे बूट करें।
3. लॉगिन पर इंस्टॉलर विंडो अपने-आप खुलती है (यह `sudo` के साथ खुद को दोबारा चलाती है: लाइव सेशन को disko/`nixos-install` के लिए root चाहिए)। पन्नों से गुज़रें: डिस्क चयन, कर्नेल, डेस्कटॉप, ब्राउज़र, एडिटर, Discord, गेमिंग ऐप, लोकेल, समय क्षेत्र, कीबोर्ड लेआउट, RGB कंट्रोलर और वैकल्पिक मॉड्यूल।
4. पुष्टि करने पर यह डिस्क का पार्टिशन करता है (disko), ISO में शामिल Roudix flake को `/mnt/etc/nixos` में कॉपी करता है और `nixos-install --flake /mnt/etc/nixos#roudix` चलाता है।

> **नोट:** अगर लाइव सेशन का कीबोर्ड आपके भौतिक कीबोर्ड से मेल नहीं खाता तो बूट मेनू कीबोर्ड-लेआउट विशेषीकरण (US/BE/FR/DE/CH/UK) भी देता है — इंस्टॉलर शुरू करने से पहले एक चुन लें।

यह रास्ता नीचे के दोनों चरणों की जगह पूरी तरह ले लेता है (`roudix-installer.sh` या मैनुअल चरणों की ज़रूरत नहीं) — रीबूट होने के बाद इंस्टॉलेशन के बाद वाले हिस्से पर जाएँ।

## विकल्प B — NixOS पहले से इंस्टॉल है

अगर NixOS पहले से इंस्टॉल है (आधिकारिक स्टेबल/unstable ISO या किसी और तरीके से) और आप बस उसके ऊपर Roudix लगाना चाहते हैं, तो दो इंस्टॉलर हैं: ग्राफ़िकल (डेस्कटॉप सेशन से) और bash स्क्रिप्ट (सीधे TTY से भी चलती है)।

> **नोट:** पहले [stable](https://nixos.org/download/) या [unstable](https://releases.nixos.org/nixos/unstable/nixos-26.05pre980183.4bd9165a9165) ISO से NixOS इंस्टॉल करें, फिर नीचे का कोई एक इंस्टॉलर चलाएँ या मैनुअल इंस्टॉलेशन का पालन करें।

### B1 — ग्राफ़िकल इंस्टॉलर (डेस्कटॉप पर अनुशंसित)

ISO वाला ही विज़ार्ड, बस डिस्क पेज के बिना। इसे उस खाते से चलाएँ जिसे आप रखना चाहते हैं:

```bash
nix run "github:RoudineBWT/Roudix?dir=iso/roudix-installer"
```

- **कुछ नहीं मिटाया जाता।** कॉन्फ़िगरेशन `~/.config/roudix` में जाता है (मौजूदा फ़ोल्डर को किनारे कर दिया जाता है, कभी हटाया नहीं जाता), फिर `nixos-rebuild boot` Roudix बनाता है और उसे अगले बूट के लिए तय कर देता है। आपका मौजूदा सिस्टम बूट मेनू में बना रहता है।
- **आपके `/etc/nixos` का बैकअप** `/var/backups/roudix/nixos-<date>/` में लिया जाता है, साथ में एक `RESTORE.txt` (पिछली जनरेशन, बूटलोडर, `stateVersion` और वापस जाने के सटीक कमांड)। `hardware-configuration.nix` जैसा है वैसा ही दोबारा इस्तेमाल होता है, कभी ओवरराइट नहीं होता।
- **पहले सिमुलेट करें।** सारांश पेज का *सिमुलेट* बटन कॉन्फ़िगरेशन को एक अस्थायी फ़ोल्डर में बनाता है, जाँचता है कि हर विकल्प लिखा गया, और Nix से पूरे सिस्टम का मूल्यांकन करवाता है। आपकी मशीन पर कुछ नहीं बदलता।
- पहले से चेतावनियाँ: `/boot` में कम खाली जगह (512 MB की EFI पार्टिशन जल्दी भर जाती है), बूटलोडर में बदलाव, पुराना `system.stateVersion`।
- polkit डायलॉग से आपका एडमिन पासवर्ड माँगता है (इसके लिए polkit एजेंट चाहिए, यानी कोई भी सामान्य डेस्कटॉप सेशन)।

**वापस जाना:** बूट मेनू में पिछली जनरेशन चुनें, फिर `sudo nixos-rebuild switch --rollback`। अगर मशीन बिल्कुल बूट नहीं होती, तो `RESTORE.txt` बताती है कि लाइव USB से अपना पुराना कॉन्फ़िगरेशन कैसे वापस लाएँ।

### B2 — Bash स्क्रिप्ट (TTY / बिना ग्राफ़िकल सेशन)

**roudix-installer स्क्रिप्ट डाउनलोड करें**

```bash
nix-shell -p wget --run "wget https://github.com/RoudineBWT/Roudix/raw/refs/heads/main/roudix-installer.sh"
chmod +x roudix-installer.sh
./roudix-installer.sh
```

इंस्टॉलर सब कुछ इंटरैक्टिव ढंग से संभालता है:
- पूछता है कि कौन सी ब्रांच इंस्टॉल करें और फ़ॉलो करें (`main` = स्थिर, `testing`, `dev`), उसे क्लोन करता है, `hardware-configuration.nix` बनाता है और सभी लोकल कॉन्फ़िग फ़ाइलें तैयार करता है
- **दूसरे OS अपने-आप पहचानता है** EFI NVRAM (`efibootmgr`) से — PARTUUID हाथ से खोजने की ज़रूरत नहीं
- **GPU और CPU अपने-आप पहचानता है** (`lspci` / `/proc/cpuinfo`) — पहले से चुन देता है और पुष्टि माँगता है
- **पहचानता है कि VM में चल रहा है या नहीं** (`systemd-detect-virt`) — VM गेस्ट मोड पहले से चालू करता है और चेताता है कि GPU/CPU की पहचान सटीक न हो सकती है
- कर्नेल, डेस्कटॉप, ब्राउज़र, एडिटर, Discord, गेमिंग ऐप, लोकेल, समय क्षेत्र, कीमैप, RGB कंट्रोलर और वैकल्पिक मॉड्यूल के बारे में पूछता है
- कॉन्फ़िगरेशन बनाता और लागू करता है

---

## विकल्प C — मैनुअल इंस्टॉलेशन

> ⚠️ **रीबिल्ड करने से पहले हर चरण ध्यान से पूरा करें।**

### 1. रिपॉज़िटरी क्लोन करें

> **अगर `git` इंस्टॉल नहीं है** (नया NixOS इंस्टॉल):

```bash
nix-shell -p git --run "git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix"
```

> **वरना:**

```bash
git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix
cd ~/.config/roudix
```

### 2. अपना उपयोगकर्ता नाम सेट करें

अपने उपयोगकर्ता नाम के साथ `username.nix` फ़ाइल बनाएँ:

```bash
echo '"yourusername"' > ~/.config/roudix/hosts/roudix/username.nix
```

> यह फ़ाइल gitignore में है — `git pull` इसे कभी ओवरराइट नहीं करेगा।

### 3. hardware-configuration.nix बदलें

```bash
sudo cp /etc/nixos/hardware-configuration.nix ~/.config/roudix/hosts/roudix/hardware-configuration.nix
```

### 4. अपने लोकल कॉन्फ़िग बनाएँ

**`configuration.nix` या `home/common.nix` को सीधे कभी एडिट न करें** — `git pull` पर ये ओवरराइट हो जाते हैं।
इसके बजाय अपनी लोकल ओवरराइड फ़ाइलें बनाएँ (सभी gitignore में हैं):

```bash
cp hosts/roudix/local.nix.example hosts/roudix/local.nix
cp home/local.nix.example home/local.nix
cp modules/system/boot/boot.local.nix.example modules/system/boot/boot.local.nix
```

`hosts/roudix/local.nix` को अपने हार्डवेयर के अनुसार एडिट करें:

```nix
{ lib, ... }:
{
  roudix.desktop.type = "niri";               # "niri", "hyprland", "mangowc", "umbriel", "gnome" या "kde"
  hardware.myGpu      = "amd";                # "amd", "nvidia" या "intel"
  hardware.myCpu      = "intel";              # "intel" या "amd"
  hardware.myKernel        = "cachyos-lts-lto-v3"; # xddxdd कर्नेल — hardware.myGpu != "nvidia" होने पर इस्तेमाल होता है
  hardware.myKernelChaotic = "cachyos";            # Chaotic-Nyx कर्नेल — केवल hardware.myGpu == "nvidia" होने पर इस्तेमाल होता है
  roudix.boot.bootloader = "limine";          # "limine" या "systemd-boot"
  roudix.browsers     = [ "helium" ];         # "brave", "helium", "vivaldi", "firefox", "librewolf", "chromium" या []
  roudix.zen.enable   = false;                # Zen Browser (Twilight) भी इंस्टॉल करने के लिए true करें
  roudix.rgb          = "openlinkhub";        # "openlinkhub", "openrgb" या "none" — नीचे देखें
  roudix.mesa.useGit  = false;                # true = mesa-git (प्रायोगिक, बिल्ड विफल हो सकता है), false = स्थिर nixpkgs
  roudix.matrixClient = "none";               # "element", "cinny" या "none"
  roudix.discord      = "vencord";            # "vencord", "vanilla" या "none"
  roudix.editor       = "zed";                # "zed", "vscode", "neovim" या "none"

  # ── गेमिंग ऐप (डिफ़ॉल्ट रूप से सभी true — जो नहीं चाहिए उन्हें बंद करें) ────────
  # roudix.gaming.apps.lutris.enable        = false;
  # roudix.gaming.apps.heroic.enable        = false;
  # roudix.gaming.apps.faugus.enable        = false;
  # roudix.gaming.apps.prismlauncher.enable = false;
  # roudix.gaming.apps.vintagestory.enable  = false;
  # roudix.gaming.apps.mangohud.enable      = false;

  # ── बिना DE वाले कंपोज़िटर का इंटीग्रेशन (केवल niri/hyprland/mangowc/umbriel) ───────
  roudix.desktopIntegration = "gnome";        # "gnome" या "kde" — कीरिंग + xdg-desktop-portal स्टैक; gnome/kde सेशन पर कोई असर नहीं

  # ── लोकेल / समय क्षेत्र ───────────────────────────────────────────────────────
  time.timeZone                   = "Europe/Brussels"; # देखें https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
  environment.sessionVariables.TZ = "Europe/Brussels"; # time.timeZone से मेल खाना चाहिए
  i18n.defaultLocale              = "en_US.UTF-8";     # सिस्टम लोकेल
  console.keyMap                  = "us";              # कंसोल कीबोर्ड लेआउट — केवल TTY, ग्राफ़िकल सेशन शुरू होने से पहले

  # ── ग्राफ़िकल (Wayland) कीबोर्ड लेआउट — console.keyMap से स्वतंत्र ─
  # GNOME/KDE पर कोई असर नहीं, वे अपनी सेटिंग्स डेमन से अपना लेआउट खुद संभालते हैं।
  roudix.keyboardLayout  = "us";              # "us", "be", "fr", "de", "ch", "nl", "es", "it", "pt", "pl", "ru", "gb", "jp"...
  roudix.keyboardVariant = "intl";            # "intl", "nodeadkeys", "bepo", "dvorak", "colemak", "" (कोई नहीं)
}
```

**RGB कंट्रोलर विकल्प:**

| मान | विवरण |
|-------|-------------|
| `openlinkhub` | OpenLinkHub — पूरा Corsair सेटअप (iCUE Link, Commander...) |
| `openrgb` | OpenRGB — मिले-जुले ब्रांड (Razer, ASUS, MSI...) |
| `none` | RGB का कोई प्रबंधन नहीं |

**RAM RGB (केवल OpenLinkHub):**

अगर आपने `openlinkhub` चुना है, तो अपनी Corsair DDR4/DDR5 RAM के लिए RGB कंट्रोल भी चालू कर सकते हैं। ये पंक्तियाँ `hosts/roudix/local.nix` में जोड़ें:

```nix
roudix.memory.enable = true;                  # SMBus के ज़रिए RAM RGB चालू करें
roudix.memory.type   = "ddr5";                # "ddr4" या "ddr5"
roudix.memory.smBus  = "i2c-9";              # ऐसे खोजें: sudo i2cdetect -l ("SMBus" देखें)
roudix.memory.sku    = "CMH64GX5M2B5200C40"; # ऐसे खोजें: sudo dmidecode -t memory | grep 'Part Number'
```

मान सेट करने से पहले सही मान खोजने के लिए:

```bash
# ज़रूरी टूल इंस्टॉल करें अगर उपलब्ध नहीं हैं (नया NixOS इंस्टॉल)
nix-env -iA nixos.i2c-tools
nix-env -iA nixos.dmidecode

# अपना SMBus खोजें ("SMBus", "i801", "piix4" या "nforce" वाली पंक्ति)
sudo i2cdetect -l

# अपनी RAM का पार्ट नंबर खोजें
sudo dmidecode -t memory | grep 'Part Number'
```

> **नोट:** `roudix.memory.enable` अपने-आप `acpi_enforce_resources=lax` को कर्नेल पैरामीटर के रूप में लागू करता है और SMBus खाली करने के लिए `spd5118` (DDR5) या `ee1004` (DDR4) को ब्लैकलिस्ट करता है। OpenLinkHub का `config.json` सक्रियण पर अपने-आप पैच हो जाता है।

**आम समय क्षेत्र मान:**

| समय क्षेत्र | क्षेत्र |
|----------|--------|
| `Europe/Brussels` | बेल्जियम |
| `Europe/Paris` | फ़्रांस |
| `Europe/London` | यूनाइटेड किंगडम |
| `Europe/Berlin` | जर्मनी |
| `Europe/Amsterdam` | नीदरलैंड |
| `America/New_York` | अमेरिका (पूर्व) |
| `America/Los_Angeles` | अमेरिका (पश्चिम) |
| `Asia/Tokyo` | जापान |
| `UTC` | सार्वभौमिक |

**आम लोकेल मान:**

| लोकेल | भाषा |
|--------|----------|
| `en_US.UTF-8` | English (US) |
| `en_GB.UTF-8` | English (UK) |
| `fr_BE.UTF-8` | Français (Belgique) |
| `fr_FR.UTF-8` | Français (France) |
| `de_DE.UTF-8` | Deutsch |
| `nl_BE.UTF-8` | Nederlands (België) |
| `nl_NL.UTF-8` | Nederlands |
| `es_ES.UTF-8` | Español |
| `pt_BR.UTF-8` | Português (Brasil) |
| `it_IT.UTF-8` | Italiano |
| `ru_RU.UTF-8` | Русский |
| `ja_JP.UTF-8` | 日本語 |
| `zh_CN.UTF-8` | 中文 (简体) |
| `ko_KR.UTF-8` | 한국어 |

**आम कंसोल कीमैप मान:**

| कीमैप | लेआउट |
|--------|--------|
| `us` | English (US) QWERTY |
| `us-acentos` | English (US) International |
| `uk` | English (UK) QWERTY |
| `be-latin1` | Belge AZERTY |
| `fr` | Français AZERTY |
| `de` | Allemand QWERTZ |
| `nl` | Néerlandais QWERTY |
| `es` | Espagnol QWERTY |
| `dvorak` | Dvorak (US) |
| `colemak` | Colemak |

> **नोट:** `environment.sessionVariables.TZ` हमेशा `time.timeZone` से मेल खाना चाहिए — दोनों समय क्षेत्र नियंत्रित करते हैं, एक सिस्टम स्तर पर और दूसरा सेशन स्तर पर।

निजी home-manager ओवरराइड (अतिरिक्त पैकेज, dotfiles, एलियास, fastfetch...) के लिए `home/local.nix` एडिट करें:

```nix
{ pkgs, lib, osConfig, ... }:
{
  # home.packages = with pkgs; [ vlc telegram-desktop ];
}
```

> fastfetch कस्टमाइज़ेशन समेत सभी उपलब्ध ओवरराइड विकल्पों के लिए `home/local.nix.example` देखें।

### 5. कर्नेल कॉन्फ़िगर करें

आपकी GPU के अनुसार Roudix **दो अलग कर्नेल प्रदाता** इस्तेमाल करता है:

- **`hardware.myGpu != "nvidia"`** (AMD या Intel) → [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel) से कर्नेल, जिसे `hardware.myKernel` से चुना जाता है। Nvidia मॉड्यूल की चिंता नहीं, इसलिए पूरे 32 वैरिएंट उपलब्ध हैं।
- **`hardware.myGpu == "nvidia"`** → **Chaotic-Nyx** से कर्नेल, जिसे `hardware.myKernelChaotic` से चुना जाता है। **`nvidia_cachyos`** पाने के लिए यह ज़रूरी है, जो उनके कर्नेल से मेल खाता पहले से कंपाइल किया हुआ Nvidia ड्राइवर है — वरना हर कर्नेल अपडेट पर Nvidia कर्नेल मॉड्यूल लोकल रूप से दोबारा बनता है। यहाँ वैरिएंट का सेट जानबूझकर छोटा है (Chaotic-Nyx इतने फ़्लेवर प्रकाशित नहीं करता, और `-lto` वैरिएंट Nvidia जैसे आउट-ऑफ़-ट्री मॉड्यूल तोड़ने की ज़्यादा संभावना रखते हैं)।

दोनों विकल्प कुछ **सादे nixpkgs कर्नेल** भी स्वीकार करते हैं, जो अपने-अपने CachyOS ओवरले से पूरी तरह बाहर हैं — उपयोगी अगर आपको CachyOS पैचिंग के बिना बस सामान्य कर्नेल चाहिए: `zen`, `nixpkgs-lts`, `nixpkgs-latest`, `nixpkgs-testing`, `xanmod-lts`, `xanmod-latest`। Nvidia रास्ते पर ये `nvidia_cachyos` कैश छोड़ देते हैं और Nvidia मॉड्यूल लोकल रूप से दोबारा बनाते हैं (देखें `nvidia.nix`)।

**ज़्यादा ताज़ा nixpkgs कर्नेल — `hardware.myKernelSource`:** ये nixpkgs कर्नेल डिफ़ॉल्ट रूप से मुख्य `nixpkgs` इनपुट (nixos-unstable) को फ़ॉलो करते हैं। `hardware.myKernelSource` को `"master"` या `"staging-next"` पर सेट करें, ताकि NixOS/nixpkgs की उस ब्रांच से **केवल कर्नेल** (और उसके विरुद्ध बने आउट-ऑफ़-ट्री मॉड्यूल, जैसे Nvidia) लिया जाए और कर्नेल अपडेट जल्दी मिलें — बाकी सिस्टम को नहीं छुआ जाता। मान: `"nixpkgs"` (डिफ़ॉल्ट), `"master"`, `"staging-next"`। सावधानियाँ: ऐसा कर्नेल अभी बाइनरी कैश में न हो सकता है, इसलिए लंबे लोकल बिल्ड की उम्मीद रखें; `staging-next` में टूलचेन के चल रहे बदलाव भी होते हैं, इसलिए तीनों में यह सबसे जोखिम भरा है। `cachyos-*` कर्नेल पर इसका कोई असर नहीं (चेतावनी दिखती है)। सेट करने के बाद एक बार `nix flake lock` चलाएँ ताकि नया इनपुट लॉक हो जाए।

**`hardware.myKernel` वैरिएंट (xddxdd — केवल AMD/Intel):**

| वैरिएंट | विवरण |
|---------|-------------|
| `zen` | सादा `linuxPackages_zen` (nixpkgs) — xddxdd ओवरले से बाहर |
| `nixpkgs-lts` | nixpkgs का सादा डिफ़ॉल्ट LTS कर्नेल — xddxdd ओवरले से बाहर |
| `nixpkgs-latest` | nixpkgs का सादा नवीनतम mainline कर्नेल — xddxdd ओवरले से बाहर |
| `nixpkgs-testing` | nixpkgs का सादा `linux_testing` (RC/mainline) — xddxdd ओवरले से बाहर |
| `xanmod-lts` | XanMod LTS ब्रांच (`linuxPackages_xanmod`, nixpkgs) — परफ़ॉर्मेंस governor, lazy preemption, BBRv3 |
| `xanmod-latest` | XanMod मुख्य ब्रांच (`linuxPackages_xanmod_latest`, nixpkgs) |
| `cachyos-latest` | मानक नवीनतम CachyOS कर्नेल |
| `cachyos-latest-v2` | x86_64-v2 के लिए ऑप्टिमाइज़्ड |
| `cachyos-latest-v3` | x86_64-v3 के लिए ऑप्टिमाइज़्ड (आधुनिक CPU के लिए अनुशंसित) |
| `cachyos-latest-v4` | x86_64-v4 के लिए ऑप्टिमाइज़्ड (AVX-512, केवल बहुत नए CPU) |
| `cachyos-latest-zen4` | AMD Zen 4 के लिए ऑप्टिमाइज़्ड |
| `cachyos-latest-lto` | बेहतर प्रदर्शन के लिए LTO बिल्ड |
| `cachyos-latest-lto-v2` | LTO + x86_64-v2 |
| `cachyos-latest-lto-v3` | LTO + x86_64-v3 (सर्वश्रेष्ठ प्रदर्शन, केवल आधुनिक CPU) |
| `cachyos-latest-lto-v4` | LTO + x86_64-v4 (AVX-512) |
| `cachyos-latest-lto-zen4` | LTO + AMD Zen 4 |
| `cachyos-lts` | दीर्घकालिक सपोर्ट वाला CachyOS कर्नेल |
| `cachyos-lts-v2` | LTS + x86_64-v2 |
| `cachyos-lts-v3` | LTS + x86_64-v3 के लिए ऑप्टिमाइज़्ड |
| `cachyos-lts-v4` | LTS + x86_64-v4 (AVX-512) |
| `cachyos-lts-zen4` | LTS + AMD Zen 4 |
| `cachyos-lts-lto` | LTS + LTO |
| `cachyos-lts-lto-v2` | LTS + LTO + x86_64-v2 |
| `cachyos-lts-lto-v3` | LTS + LTO + x86_64-v3 (स्थिर + प्रदर्शन) |
| `cachyos-lts-lto-v4` | LTS + LTO + x86_64-v4 (AVX-512) |
| `cachyos-lts-lto-zen4` | LTS + LTO + AMD Zen 4 |
| `cachyos-bmq` | BMQ शेड्यूलर |
| `cachyos-bmq-lto` | BMQ शेड्यूलर + LTO |
| `cachyos-bore` | BORE शेड्यूलर (बेहतर इंटरैक्टिविटी) |
| `cachyos-bore-lto` | BORE शेड्यूलर + LTO |
| `cachyos-deckify` | Steam Deck के लिए ऑप्टिमाइज़्ड |
| `cachyos-deckify-lto` | Steam Deck के लिए ऑप्टिमाइज़्ड + LTO |
| `cachyos-eevdf` | EEVDF शेड्यूलर |
| `cachyos-eevdf-lto` | EEVDF शेड्यूलर + LTO |
| `cachyos-hardened` | सुरक्षा के लिए मज़बूत किया गया कर्नेल |
| `cachyos-hardened-lto` | सुरक्षा के लिए मज़बूत + LTO |
| `cachyos-rc` | रिलीज़ कैंडिडेट — सबसे नया, अस्थिर हो सकता है |
| `cachyos-rc-lto` | Release candidate + LTO |
| `cachyos-rt-bore` | रियल-टाइम + BORE शेड्यूलर |
| `cachyos-rt-bore-lto` | Real-time + BORE + LTO |
| `cachyos-server` | सर्वर के लिए ऑप्टिमाइज़्ड (डेस्कटॉप ट्यूनिंग के बिना) |
| `cachyos-server-lto` | सर्वर के लिए ऑप्टिमाइज़्ड + LTO |

**`hardware.myKernelChaotic` वैरिएंट (Chaotic-Nyx — केवल Nvidia):**

| वैरिएंट | विवरण |
|---------|-------------|
| `cachyos` | डिफ़ॉल्ट — LTO + BORE शेड्यूलर, मेल खाते `nvidia_cachyos` के साथ |
| `cachyos-lts` | दीर्घकालिक सपोर्ट |
| `cachyos-server` | सर्वर के लिए ऑप्टिमाइज़्ड (डेस्कटॉप ट्यूनिंग के बिना) |
| `cachyos-hardened` | सुरक्षा के लिए मज़बूत |
| `zen` | सादा `linuxPackages_zen` (nixpkgs) — Nvidia मॉड्यूल लोकल रूप से दोबारा बना |
| `nixpkgs-lts` | nixpkgs का सादा LTS — Nvidia मॉड्यूल लोकल रूप से दोबारा बना |
| `nixpkgs-latest` | nixpkgs का सादा नवीनतम mainline — Nvidia मॉड्यूल लोकल रूप से दोबारा बना |
| `nixpkgs-testing` | nixpkgs का सादा `linux_testing` (RC) — Nvidia मॉड्यूल लोकल रूप से दोबारा बना |
| `xanmod-lts` | XanMod LTS (nixpkgs) — Nvidia मॉड्यूल लोकल रूप से दोबारा बना |
| `xanmod-latest` | XanMod मुख्य ब्रांच (nixpkgs) — Nvidia मॉड्यूल लोकल रूप से दोबारा बना |

> **NVIDIA नोट:** केवल GTX 20xx / RTX सीरीज़ और नए मॉडल समर्थित हैं। RTX 20xx+ (Turing+) के लिए ओपन ड्राइवर डिफ़ॉल्ट रूप से चालू हैं। GTX 10xx/16xx समर्थित नहीं हैं।

> **Spicetify Comfy थीम नोट:** पहले बिल्ड के बाद color.ini हाथ से कॉपी करें:
> ```bash
> cp ~/.config/spicetify/Themes/Comfy/color.ini ~/.config/roudix/modules/home/spicetify/Comfy/color.ini
> ```
> फिर लागू करने के लिए `rebuild` चलाएँ।

### 6. डिस्क माउंट अपडेट करें

`hosts/roudix/local.nix` में अपने UUID के साथ एक `lib.mkForce` ब्लॉक जोड़ें (या दूसरी डिस्क न हो तो छोड़ दें):

```bash
lsblk -f  # अपनी डिस्क का UUID खोजें
```

```nix
fileSystems."/mnt/gaming" = lib.mkForce {
  device = "/dev/disk/by-uuid/YOUR-UUID-HERE";
  fsType = "btrfs";
  options = [ "defaults" "nofail" ];
};
```

### 7. Limine मल्टी-बूट कॉन्फ़िगर करें (वैकल्पिक)

> अगर आपकी मशीन पर केवल NixOS है तो यह चरण छोड़ दें।

Limine अलग डिस्क पर मौजूद दूसरे ऑपरेटिंग सिस्टम बूट कर सकता है। `boot.local.nix` अतिरिक्त एंट्री नियंत्रित करती है — यह gitignore में है और `git pull` इसे कभी ओवरराइट नहीं करता।

**`modules/system/boot/boot.nix` को सीधे कभी एडिट न करें** — `git pull` पर यह ओवरराइट हो जाती है।

#### अगर आपने ऑटोमैटिक इंस्टॉलर इस्तेमाल किया

इंस्टॉलर ने EFI NVRAM (`efibootmgr`) से आपके दूसरे OS अपने-आप पहचान लिए और आपके लिए `boot.local.nix` लिख दी — कोई हाथ से कार्रवाई ज़रूरी नहीं। आप नतीजा देख सकते हैं:

```bash
cat modules/system/boot/boot.local.nix
```

#### अगर आप हाथ से इंस्टॉल कर रहे हैं

**अपने PARTUUID पाएँ:**

```bash
lsblk -o NAME,FSTYPE,SIZE,PARTLABEL,PARTUUID
```

`vfat` फ़ाइल सिस्टम प्रकार और `EFI system partition` लेबल वाले पार्टिशन खोजें — वही आपके ESP हैं।

**`modules/system/boot/boot.local.nix` एडिट करें** और अपनी एंट्री जोड़ें:

```nix
{
  extraEntries = ''
    /+Other systems and bootloaders
    //Windows
      protocol: efi
      path: uuid(YOUR-WINDOWS-ESP-PARTUUID):/EFI/Microsoft/Boot/bootmgfw.efi
    //CachyOS
      protocol: efi
      path: uuid(YOUR-CACHYOS-ESP-PARTUUID):/EFI/limine/BOOTX64.EFI
  '';
}
```

> **सुझाव:** UUID के बाद का EFI पाथ दूसरे OS के बूटलोडर पर निर्भर करता है। आम पाथ:
> - Windows: `/EFI/Microsoft/Boot/bootmgfw.efi`
> - CachyOS (Limine): `/EFI/limine/BOOTX64.EFI`
> - Arch/Manjaro (GRUB): `/EFI/grub/grubx64.efi`
> - कोई भी डिस्ट्रो (विकल्प): `/EFI/BOOT/BOOTX64.EFI`

अगर जोड़ने के लिए कोई दूसरा OS नहीं है, तो `extraEntries` को खाली छोड़ दें:

```nix
{
  extraEntries = "";
}
```

> `boot.local.nix` `.gitignore` में दर्ज है — `git pull` इसे कभी ओवरराइट नहीं करेगा।

### 8. git कॉन्फ़िग अपडेट करें

`modules/home/git.nix` gitignore में है (`local.nix` की तरह) — ट्रैक किया हुआ टेम्पलेट कॉपी करें और अपनी पहचान भरें:

```bash
cp modules/home/git.nix.example modules/home/git.nix
```

```nix
{ ... }:
{
  programs.git = {
    enable = true;
    settings = {
      user.name = "yourname";
      user.email = "your@email.com";
      init.defaultBranch = "main";
      pull.rebase = false;
    };
  };
}
```

- `init.defaultBranch = "main"` — नया रिपॉज़िटरी `git init` करने पर पहली ब्रांच के लिए इस्तेमाल होने वाला नाम (इस रिपॉज़िटरी की अपनी ब्रांच पर असर नहीं, केवल उन पर जो आप खुद बनाते हैं)।
- `pull.rebase = false` — जब आपकी लोकल ब्रांच और रिमोट अलग हो चुके हों तब `git pull` क्या करे: `false` मर्ज करता है (एक merge कमिट बनाता है, डिफ़ॉल्ट और सबसे सरल व्यवहार), `true` आपके लोकल कमिट को रिमोट के ऊपर rebase करता है (रैखिक इतिहास, पर आपके कमिट दोबारा लिखे जाते हैं — अगर rebase के टकरावों में सहज नहीं हैं तो इससे बचें)। निजी कॉन्फ़िग रिपॉज़िटरी के लिए `false` ज़्यादा सुरक्षित विकल्प है।

> अगर फ़ाइल नहीं है, तो `common.nix` उसे बस छोड़ देता है — आपके कॉपी करने तक Home Manager git कॉन्फ़िगर नहीं करेगा, पर कुछ टूटता नहीं।

### 9. वैकल्पिक मॉड्यूल चालू/बंद करें

`hosts/roudix/local.nix` में:

```nix
roudix.gaming.enable         = true;
roudix.flatpak.enable        = true;   # Flatpak + रोज़ाना ऑटो-अपडेट
roudix.fstrim.enable         = true;   # SSD/NVMe के लिए अनुशंसित
roudix.virtualization.enable = false;  # QEMU/KVM के लिए चालू करें
roudix.vmGuest.enable        = true;   # केवल VM के अंदर चालू करें
roudix.hosts.gtaFix.enable   = true;   # BattlEye टेलीमेट्री ब्लॉक करें (GTA फ़िक्स)
roudix.autoupdate.enable     = true;   # बदलाव होने पर ऑटो git pull + nh os boot
roudix.zen.enable            = false;  # Zen Browser इंस्टॉल करें (डिफ़ॉल्ट रूप से बंद)
roudix.mesa.useGit           = false;  # true = mesa-git (प्रायोगिक, सबसे नया — बिल्ड विफल हो सकता है), false = स्थिर nixpkgs
roudix.boot.bootloader       = "limine";  # "limine" या "systemd-boot"
roudix.matrixClient          = "none"; # "element", "cinny" या "none"
```

> **याद रखें:** अगर आप `roudix.autoupdate.enable = true` सेट करते हैं, तो अंतराल भी कॉन्फ़िगर करें:
> ```nix
> roudix.autoupdate.interval = "1h"; # 1h, 6h, 12h, 24h...
> ```

### 10. fastfetch कस्टमाइज़ करें (वैकल्पिक)

डिफ़ॉल्ट रूप से Roudix fastfetch में अपना ASCII लोगो दिखाता है। आप git को छुए बिना `home/local.nix` में इसे बदल सकते हैं:

```nix
# कस्टम इमेज इस्तेमाल करें (kitty टर्मिनल चाहिए)
programs.fastfetch.settings.logo = {
  type = "kitty-direct";
  source = "/home/youruser/Pictures/my-logo.png";
  padding = { top = 1; left = 3; };
  width = 38;
};

# कस्टम ASCII फ़ाइल इस्तेमाल करें
programs.fastfetch.settings.logo = {
  type = "file";
  source = "/home/youruser/.config/fastfetch/my-logo.txt";
  padding = { top = 1; left = 3; };
  width = 38;
};

# पूरा fastfetch कॉन्फ़िग बदल दें (सब कुछ बदल देता है)
programs.fastfetch.settings = lib.mkForce {
  "$schema" = "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json";
  logo = { ... };
  display = { separator = "  "; color = "33"; };
  modules = [ ... ];
};
```

> `lib.mkForce` पूरे Roudix डिफ़ॉल्ट कॉन्फ़िग को ओवरराइट कर देता है। इसके बिना आपकी कुंजियाँ डिफ़ॉल्ट के साथ मर्ज हो जाती हैं।
> और उदाहरणों के लिए `home/local.nix.example` देखें।

### 11. बिल्ड करें

> **अगर flakes और nix-command अभी चालू नहीं हैं** (नया NixOS इंस्टॉल):

```bash
nix --extra-experimental-features 'nix-command flakes' shell nixpkgs#git -c sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

> **वरना:**

```bash
sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

बिल्ड हो जाने के बाद, आगे के सभी कामों के लिए fish एलियास इस्तेमाल करें।

> तीनों `local.nix` फ़ाइलें और `boot.local.nix` `.gitignore` में दर्ज हैं — `git pull` इन्हें कभी ओवरराइट नहीं करेगा।
