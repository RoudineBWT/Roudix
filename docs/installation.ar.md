[English](installation.md) · [Français](installation.fr.md) · [Español](installation.es.md) · [Português (Brasil)](installation.pt_BR.md) · [Русский](installation.ru.md) · [简体中文](installation.zh_CN.md) · [हिन्दी](installation.hi.md) · **العربية**

# التثبيت

هناك ثلاث طرق لتشغيل Roudix، بحسب نقطة انطلاقك:

| الحالة | ما تستخدمه |
|-----------|-----|
| جهاز جديد، لم يُثبَّت عليه شيء بعد | **ISO الخاصة بـ Roudix** — تُقلع مباشرة إلى مثبّت رسومي (يشمل تقسيم القرص) |
| NixOS مثبّت بالفعل (ISO الرسمية، تثبيت NixOS من توزيعة أخرى، آلة افتراضية…) | **`roudix-installer.sh`** — يثبّت flake الخاص بـ Roudix فوق تثبيتك الحالي |
| تريد التحكم الكامل في كل خطوة، أو لا يغطي السكربت حالتك | **التثبيت اليدوي** (أدناه) |

## الخيار A — ISO الخاصة بـ Roudix (موصى بها للتثبيت الجديد)

تتضمن ISO مثبّتنا الرسومي الخاص المبني على GTK4/libadwaita (`roudix-installer`) فوق جلسة GNOME حيّة، ويتولى تقسيم القرص نيابةً عنك عبر [disko](https://github.com/nix-community/disko) — لست بحاجة إلى تثبيت NixOS مسبقًا.

1. احصل على أحدث ISO: انتقل إلى تبويب **Actions** في المستودع ← سير العمل **💿 Build Roudix ISO** ← شغّله (`workflow_dispatch`) إن لم يكن هناك بناء حديث مدرج، ثم افتح عملية التشغيل وخذ رابط التنزيل المنشور في ملخص المهمة (تُستضاف ISO على Cloudflare R2، لا كمُخرَج في GitHub).
2. اكتبها على وحدة USB (مثلًا `dd` أو Ventoy أو Rufus…) وأقلع منها.
3. تفتح نافذة المثبّت تلقائيًا عند تسجيل الدخول (تُعيد تشغيل نفسها بـ `sudo`: تحتاج الجلسة الحيّة إلى root من أجل disko/`nixos-install`). امرّ على الصفحات: اختيار القرص، النواة، سطح المكتب، المتصفح، المحرر، Discord، تطبيقات الألعاب، اللغة والمنطقة، المنطقة الزمنية، تخطيط لوحة المفاتيح، وحدة تحكم RGB، والوحدات الاختيارية.
4. عند التأكيد يقسّم القرص (disko)، وينسخ flake الخاص بـ Roudix المضمَّن في ISO إلى `/mnt/etc/nixos`، ثم يشغّل `nixos-install --flake /mnt/etc/nixos#roudix`.

> **ملاحظة:** تتيح قائمة الإقلاع أيضًا تخصيصات لتخطيط لوحة المفاتيح (US/BE/FR/DE/CH/UK) إن لم تطابق لوحة مفاتيح الجلسة الحيّة لوحتك الفعلية — اختر واحدًا قبل بدء المثبّت.

يحلّ هذا المسار محل الخطوتين التاليتين بالكامل (لا حاجة إلى `roudix-installer.sh` ولا إلى الخطوات اليدوية) — انتقل إلى ما يلي التثبيت بعد إعادة التشغيل.

## الخيار B — لديك NixOS مثبّت بالفعل

إذا كان NixOS مثبّتًا بالفعل (عبر ISO الرسمية المستقرة/unstable أو بأي وسيلة أخرى) وتريد فقط تثبيت Roudix فوقه، فهناك مثبّتان: الرسومي (من جلسة سطح مكتب) وسكربت bash (يعمل من TTY مجرّد).

> **ملاحظة:** ثبّت NixOS أولًا عبر ISO [المستقرة](https://nixos.org/download/) أو [unstable](https://releases.nixos.org/nixos/unstable/nixos-26.05pre980183.4bd9165a9165)، ثم شغّل أحد المثبّتَين أدناه أو اتبع التثبيت اليدوي.

### B1 — المثبّت الرسومي (موصى به على سطح المكتب)

المعالج نفسه الموجود في ISO، دون صفحة القرص. شغّله من الحساب الذي تريد الاحتفاظ به:

```bash
nix run "github:RoudineBWT/Roudix?dir=iso/roudix-installer"
```

- **لا يُمسح شيء.** تذهب الإعدادات إلى `~/.config/roudix` (يُنقل أي مجلد موجود جانبًا ولا يُحذف أبدًا)، ثم يبني `nixos-rebuild boot` نظام Roudix ويجدوله للإقلاع التالي. يبقى نظامك الحالي في قائمة الإقلاع.
- **تُنسخ `/etc/nixos` احتياطيًا** إلى `/var/backups/roudix/nixos-<date>/` مع ملف `RESTORE.txt` (الجيل السابق، مدير الإقلاع، `stateVersion`، والأوامر الدقيقة للعودة). يُعاد استخدام `hardware-configuration.nix` كما هو ولا يُستبدل أبدًا.
- **جرّب المحاكاة أولًا.** يولّد زر *محاكاة* في صفحة الملخص الإعدادات في مجلد مؤقت، ويتحقق من كتابة كل خيار، ويجعل Nix يقيّم النظام بأكمله. لا يتغيّر شيء على جهازك.
- تحذيرات مسبقة: مساحة قليلة في `/boot` (يمتلئ قسم EFI بحجم 512 ميغابايت بسرعة)، أو تغيير مدير الإقلاع، أو `system.stateVersion` أقدم.
- يطلب كلمة مرور المسؤول عبر مربع حوار polkit (يحتاج إلى وكيل polkit، أي أي جلسة سطح مكتب عادية).

**العودة إلى الوراء:** اختر الجيل السابق من قائمة الإقلاع ثم نفّذ `sudo nixos-rebuild switch --rollback`. وإذا لم يُقلع الجهاز إطلاقًا، فإن `RESTORE.txt` يشرح كيفية استعادة إعداداتك القديمة من USB حيّ.

### B2 — سكربت Bash (TTY / دون جلسة رسومية)

**نزّل سكربت roudix-installer**

```bash
nix-shell -p wget --run "wget https://github.com/RoudineBWT/Roudix/raw/refs/heads/main/roudix-installer.sh"
chmod +x roudix-installer.sh
./roudix-installer.sh
```

يتولى المثبّت كل شيء بشكل تفاعلي:
- يسأل عن الفرع الذي ستثبّته وتتبعه (`main` = مستقر، `testing`، `dev`)، ويستنسخه، ويولّد `hardware-configuration.nix`، وينشئ جميع ملفات الإعدادات المحلية
- **يكتشف أنظمة التشغيل الأخرى تلقائيًا** عبر NVRAM الخاصة بـ EFI (`efibootmgr`) — دون البحث عن PARTUUID يدويًا
- **يكتشف بطاقة GPU والمعالج تلقائيًا** (`lspci` / `/proc/cpuinfo`) — يحدّدهما مسبقًا ويطلب التأكيد
- **يكتشف ما إذا كان يعمل داخل آلة افتراضية** (`systemd-detect-virt`) — يفعّل مسبقًا وضع ضيف الآلة الافتراضية ويحذّر من أن اكتشاف GPU/المعالج قد لا يكون دقيقًا
- يسأل عن النواة وسطح المكتب والمتصفح والمحرر وDiscord وتطبيقات الألعاب واللغة والمنطقة والمنطقة الزمنية وخريطة المفاتيح ووحدة تحكم RGB والوحدات الاختيارية
- يبني الإعدادات ويطبّقها

---

## الخيار C — التثبيت اليدوي

> ⚠️ **اتبع كل خطوة بعناية قبل إعادة البناء.**

### 1. استنسخ المستودع

> **إذا لم يكن `git` مثبّتًا** (تثبيت NixOS جديد):

```bash
nix-shell -p git --run "git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix"
```

> **وإلا:**

```bash
git clone https://github.com/RoudineBWT/Roudix.git ~/.config/roudix
cd ~/.config/roudix
```

### 2. حدّد اسم المستخدم

أنشئ الملف `username.nix` باسم المستخدم الخاص بك:

```bash
echo '"yourusername"' > ~/.config/roudix/hosts/roudix/username.nix
```

> هذا الملف مُدرج في gitignore — لن يستبدله `git pull` أبدًا.

### 3. استبدل hardware-configuration.nix

```bash
sudo cp /etc/nixos/hardware-configuration.nix ~/.config/roudix/hosts/roudix/hardware-configuration.nix
```

### 4. أنشئ إعداداتك المحلية

**لا تعدّل `configuration.nix` ولا `home/common.nix` مباشرة أبدًا** — فهما يُستبدلان عند `git pull`.
بدلًا من ذلك، أنشئ ملفات التخصيص المحلية الخاصة بك (كلها في gitignore):

```bash
cp hosts/roudix/local.nix.example hosts/roudix/local.nix
cp home/local.nix.example home/local.nix
cp modules/system/boot/boot.local.nix.example modules/system/boot/boot.local.nix
```

عدّل `hosts/roudix/local.nix` ليطابق عتادك:

```nix
{ lib, ... }:
{
  roudix.desktop.type = "niri";               # "niri" أو "hyprland" أو "mangowc" أو "umbriel" أو "gnome" أو "kde"
  hardware.myGpu      = "amd";                # "amd" أو "nvidia" أو "intel"
  hardware.myCpu      = "intel";              # "intel" أو "amd"
  hardware.myKernel        = "cachyos-lts-lto-v3"; # نواة xddxdd — تُستخدم عندما hardware.myGpu != "nvidia"
  hardware.myKernelChaotic = "cachyos";            # نواة Chaotic-Nyx — تُستخدم فقط عندما hardware.myGpu == "nvidia"
  roudix.boot.bootloader = "limine";          # "limine" أو "systemd-boot"
  roudix.browsers     = [ "helium" ];         # "brave" أو "helium" أو "vivaldi" أو "firefox" أو "librewolf" أو "chromium" أو []
  roudix.zen.enable   = false;                # اضبطها على true لتثبيت Zen Browser أيضًا (Twilight)
  roudix.rgb          = "openlinkhub";        # "openlinkhub" أو "openrgb" أو "none" — انظر أدناه
  roudix.mesa.useGit  = false;                # true = mesa-git (تجريبي، قد يفشل البناء)، false = nixpkgs المستقر
  roudix.matrixClient = "none";               # "element" أو "cinny" أو "none"
  roudix.discord      = "vencord";            # "vencord" أو "vanilla" أو "none"
  roudix.editor       = "zed";                # "zed" أو "vscode" أو "neovim" أو "none"

  # ── تطبيقات الألعاب (كلها true افتراضيًا — عطّل ما لا تريده) ────────
  # roudix.gaming.apps.lutris.enable        = false;
  # roudix.gaming.apps.heroic.enable        = false;
  # roudix.gaming.apps.faugus.enable        = false;
  # roudix.gaming.apps.prismlauncher.enable = false;
  # roudix.gaming.apps.vintagestory.enable  = false;
  # roudix.gaming.apps.mangohud.enable      = false;

  # ── تكامل المُركِّب المجرّد (niri/hyprland/mangowc/umbriel فقط) ───────
  roudix.desktopIntegration = "gnome";        # "gnome" أو "kde" — سلسلة المفاتيح + حزمة xdg-desktop-portal؛ لا أثر على جلسات gnome/kde

  # ── اللغة والمنطقة / المنطقة الزمنية ───────────────────────────────────────────────────────
  time.timeZone                   = "Europe/Brussels"; # راجع https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
  environment.sessionVariables.TZ = "Europe/Brussels"; # يجب أن تطابق time.timeZone
  i18n.defaultLocale              = "en_US.UTF-8";     # لغة النظام ومنطقته
  console.keyMap                  = "us";              # تخطيط لوحة مفاتيح الطرفية — TTY فقط، قبل بدء الجلسة الرسومية

  # ── تخطيط لوحة المفاتيح الرسومية (Wayland) — مستقل عن console.keyMap ─
  # لا أثر على GNOME/KDE، فهما يديران تخطيطهما بنفسيهما عبر خدمة الإعدادات الخاصة بكل منهما.
  roudix.keyboardLayout  = "us";              # "us", "be", "fr", "de", "ch", "nl", "es", "it", "pt", "pl", "ru", "gb", "jp"...
  roudix.keyboardVariant = "intl";            # "intl" أو "nodeadkeys" أو "bepo" أو "dvorak" أو "colemak" أو "" (بدون)
}
```

**خيارات وحدة تحكم RGB:**

| القيمة | الوصف |
|-------|-------------|
| `openlinkhub` | OpenLinkHub — إعداد Corsair الكامل (iCUE Link وCommander...) |
| `openrgb` | OpenRGB — علامات تجارية متنوعة (Razer وASUS وMSI...) |
| `none` | بدون إدارة RGB |

**RGB للذاكرة (OpenLinkHub فقط):**

إذا اخترت `openlinkhub`، يمكنك أيضًا تفعيل التحكم في RGB لذاكرة Corsair DDR4/DDR5 لديك. أضف هذه الأسطر إلى `hosts/roudix/local.nix`:

```nix
roudix.memory.enable = true;                  # تفعيل RGB للذاكرة عبر SMBus
roudix.memory.type   = "ddr5";                # "ddr4" أو "ddr5"
roudix.memory.smBus  = "i2c-9";              # اعثر عليه بـ: sudo i2cdetect -l (ابحث عن "SMBus")
roudix.memory.sku    = "CMH64GX5M2B5200C40"; # اعثر عليه بـ: sudo dmidecode -t memory | grep 'Part Number'
```

للعثور على القيم الصحيحة قبل ضبطها:

```bash
# ثبّت الأدوات اللازمة إن لم تكن متوفرة (تثبيت NixOS جديد)
nix-env -iA nixos.i2c-tools
nix-env -iA nixos.dmidecode

# اعثر على SMBus (سطر يحتوي على "SMBus" أو "i801" أو "piix4" أو "nforce")
sudo i2cdetect -l

# اعثر على رقم قطعة ذاكرتك
sudo dmidecode -t memory | grep 'Part Number'
```

> **ملاحظة:** يطبّق `roudix.memory.enable` تلقائيًا `acpi_enforce_resources=lax` كمعامل للنواة، ويضع `spd5118` (DDR5) أو `ee1004` (DDR4) في القائمة السوداء لتحرير SMBus. ويُعدَّل `config.json` الخاص بـ OpenLinkHub تلقائيًا عند التفعيل.

**قيم المنطقة الزمنية الشائعة:**

| المنطقة الزمنية | المنطقة |
|----------|--------|
| `Europe/Brussels` | بلجيكا |
| `Europe/Paris` | فرنسا |
| `Europe/London` | المملكة المتحدة |
| `Europe/Berlin` | ألمانيا |
| `Europe/Amsterdam` | هولندا |
| `America/New_York` | شرق الولايات المتحدة |
| `America/Los_Angeles` | غرب الولايات المتحدة |
| `Asia/Tokyo` | اليابان |
| `UTC` | عالمية |

**قيم اللغة والمنطقة الشائعة:**

| اللغة والمنطقة | اللغة |
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

**قيم خريطة مفاتيح الطرفية الشائعة:**

| خريطة المفاتيح | التخطيط |
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

> **ملاحظة:** يجب أن يطابق `environment.sessionVariables.TZ` دائمًا `time.timeZone` — فكلاهما يتحكم في المنطقة الزمنية، أحدهما على مستوى النظام والآخر على مستوى الجلسة.

عدّل `home/local.nix` لتخصيصات home-manager الشخصية (حزم إضافية، dotfiles، أسماء مستعارة، fastfetch...):

```nix
{ pkgs, lib, osConfig, ... }:
{
  # home.packages = with pkgs; [ vlc telegram-desktop ];
}
```

> راجع `home/local.nix.example` لمعرفة جميع خيارات التخصيص المتاحة بما فيها تخصيص fastfetch.

### 5. اضبط النواة

يستخدم Roudix **مزوّدَين مختلفَين للنواة** بحسب بطاقة GPU لديك:

- **`hardware.myGpu != "nvidia"`** (AMD أو Intel) ← نواة من [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel)، تُختار عبر `hardware.myKernel`. لا وحدة Nvidia تدعو للقلق، لذا تتوفر المجموعة الكاملة من 32 نسخة.
- **`hardware.myGpu == "nvidia"`** ← نواة من **Chaotic-Nyx**، تُختار عبر `hardware.myKernelChaotic`. هذا ضروري للحصول على **`nvidia_cachyos`**، وهو تعريف Nvidia مبني مسبقًا ومطابق لنواتهم — وإلا أُعيد بناء وحدة نواة Nvidia محليًا مع كل ترقية للنواة. مجموعة النسخ هنا أصغر عمدًا (لا ينشر Chaotic-Nyx هذا العدد من النكهات، كما أن نسخ `-lto` أكثر عرضة لكسر الوحدات الخارجية مثل وحدة Nvidia).

يقبل الخياران أيضًا عددًا قليلًا من **نوى nixpkgs العادية**، خارج overlay الخاصة بـ CachyOS تمامًا — وهي مفيدة إن أردت نواة قياسية دون ترقيعات CachyOS: `zen` و`nixpkgs-lts` و`nixpkgs-latest` و`nixpkgs-testing` و`xanmod-lts` و`xanmod-latest`. على مسار Nvidia تتجاوز هذه النوى ذاكرة `nvidia_cachyos` المؤقتة وتعيد بناء وحدة Nvidia محليًا (انظر `nvidia.nix`).

**نوى nixpkgs الأحدث — `hardware.myKernelSource`:** تتبع نوى nixpkgs هذه افتراضيًا مدخل `nixpkgs` الرئيسي (nixos-unstable). اضبط `hardware.myKernelSource` على `"master"` أو `"staging-next"` لتأخذ **النواة فقط** (والوحدات الخارجية المبنية عليها، مثل Nvidia) من ذلك الفرع في NixOS/nixpkgs وتحصل على ترقيات النواة أبكر — دون المساس ببقية النظام. القيم: `"nixpkgs"` (افتراضي) و`"master"` و`"staging-next"`. تنبيهات: قد لا تكون هذه النواة في ذاكرة ثنائية مؤقتة بعد، فتوقّع بناءً محليًا طويلًا؛ كما يحمل `staging-next` تغييرات سلسلة الأدوات الجارية، فهو الأكثر مخاطرة بين الثلاثة. لا أثر له على نوى `cachyos-*` (يظهر تحذير). بعد الضبط، نفّذ `nix flake lock` مرة واحدة ليُقفل المدخل الجديد.

**نسخ `hardware.myKernel` (xddxdd — AMD/Intel فقط):**

| النسخة | الوصف |
|---------|-------------|
| `zen` | `linuxPackages_zen` العادية (nixpkgs) — خارج overlay الخاصة بـ xddxdd |
| `nixpkgs-lts` | نواة LTS الافتراضية العادية من nixpkgs — خارج overlay الخاصة بـ xddxdd |
| `nixpkgs-latest` | أحدث نواة mainline عادية من nixpkgs — خارج overlay الخاصة بـ xddxdd |
| `nixpkgs-testing` | `linux_testing` العادية من nixpkgs (RC/mainline) — خارج overlay الخاصة بـ xddxdd |
| `xanmod-lts` | فرع XanMod LTS (`linuxPackages_xanmod`، nixpkgs) — governor الأداء، الاستباق الكسول، BBRv3 |
| `xanmod-latest` | الفرع الرئيسي لـ XanMod (`linuxPackages_xanmod_latest`، nixpkgs) |
| `cachyos-latest` | أحدث نواة CachyOS قياسية |
| `cachyos-latest-v2` | مُحسَّنة لـ x86_64-v2 |
| `cachyos-latest-v3` | مُحسَّنة لـ x86_64-v3 (موصى بها للمعالجات الحديثة) |
| `cachyos-latest-v4` | مُحسَّنة لـ x86_64-v4 (AVX-512، المعالجات الحديثة جدًا فقط) |
| `cachyos-latest-zen4` | مُحسَّنة لـ AMD Zen 4 |
| `cachyos-latest-lto` | بناء LTO لأداء أفضل |
| `cachyos-latest-lto-v2` | LTO + x86_64-v2 |
| `cachyos-latest-lto-v3` | LTO + x86_64-v3 (أفضل أداء، للمعالجات الحديثة فقط) |
| `cachyos-latest-lto-v4` | LTO + x86_64-v4 (AVX-512) |
| `cachyos-latest-lto-zen4` | LTO + AMD Zen 4 |
| `cachyos-lts` | نواة CachyOS ذات الدعم طويل الأمد |
| `cachyos-lts-v2` | LTS + x86_64-v2 |
| `cachyos-lts-v3` | LTS + مُحسَّنة لـ x86_64-v3 |
| `cachyos-lts-v4` | LTS + x86_64-v4 (AVX-512) |
| `cachyos-lts-zen4` | LTS + AMD Zen 4 |
| `cachyos-lts-lto` | LTS + LTO |
| `cachyos-lts-lto-v2` | LTS + LTO + x86_64-v2 |
| `cachyos-lts-lto-v3` | LTS + LTO + x86_64-v3 (مستقرة + أداء) |
| `cachyos-lts-lto-v4` | LTS + LTO + x86_64-v4 (AVX-512) |
| `cachyos-lts-lto-zen4` | LTS + LTO + AMD Zen 4 |
| `cachyos-bmq` | مجدول BMQ |
| `cachyos-bmq-lto` | مجدول BMQ + LTO |
| `cachyos-bore` | مجدول BORE (تفاعلية أفضل) |
| `cachyos-bore-lto` | مجدول BORE + LTO |
| `cachyos-deckify` | مُحسَّنة لـ Steam Deck |
| `cachyos-deckify-lto` | مُحسَّنة لـ Steam Deck + LTO |
| `cachyos-eevdf` | مجدول EEVDF |
| `cachyos-eevdf-lto` | مجدول EEVDF + LTO |
| `cachyos-hardened` | نواة مُعزَّزة أمنيًا |
| `cachyos-hardened-lto` | مُعزَّزة أمنيًا + LTO |
| `cachyos-rc` | إصدار مرشح — الأحدث على الإطلاق، وقد يكون غير مستقر |
| `cachyos-rc-lto` | Release candidate + LTO |
| `cachyos-rt-bore` | الزمن الحقيقي + مجدول BORE |
| `cachyos-rt-bore-lto` | Real-time + BORE + LTO |
| `cachyos-server` | مُحسَّنة للخوادم (دون ضبط لسطح المكتب) |
| `cachyos-server-lto` | مُحسَّنة للخوادم + LTO |

**نسخ `hardware.myKernelChaotic` (Chaotic-Nyx — Nvidia فقط):**

| النسخة | الوصف |
|---------|-------------|
| `cachyos` | افتراضية — LTO + مجدول BORE، وتأتي مع `nvidia_cachyos` المطابق |
| `cachyos-lts` | دعم طويل الأمد |
| `cachyos-server` | مُحسَّنة للخوادم (دون ضبط لسطح المكتب) |
| `cachyos-hardened` | مُعزَّزة أمنيًا |
| `zen` | `linuxPackages_zen` العادية (nixpkgs) — وحدة Nvidia تُعاد بناؤها محليًا |
| `nixpkgs-lts` | LTS العادية من nixpkgs — وحدة Nvidia تُعاد بناؤها محليًا |
| `nixpkgs-latest` | أحدث mainline عادية من nixpkgs — وحدة Nvidia تُعاد بناؤها محليًا |
| `nixpkgs-testing` | `linux_testing` العادية من nixpkgs (RC) — وحدة Nvidia تُعاد بناؤها محليًا |
| `xanmod-lts` | XanMod LTS (nixpkgs) — وحدة Nvidia تُعاد بناؤها محليًا |
| `xanmod-latest` | الفرع الرئيسي لـ XanMod (nixpkgs) — وحدة Nvidia تُعاد بناؤها محليًا |

> **ملاحظة حول NVIDIA:** المدعوم فقط GTX 20xx / سلسلة RTX وما بعدها. التعريفات المفتوحة مفعّلة افتراضيًا لبطاقات RTX 20xx+ (Turing+). بطاقات GTX 10xx/16xx غير مدعومة.

> **ملاحظة حول سمة Spicetify Comfy:** بعد أول بناء، انسخ الملف color.ini يدويًا:
> ```bash
> cp ~/.config/spicetify/Themes/Comfy/color.ini ~/.config/roudix/modules/home/spicetify/Comfy/color.ini
> ```
> ثم نفّذ `rebuild` للتطبيق.

### 6. حدّث تركيب القرص

في `hosts/roudix/local.nix` أضف كتلة `lib.mkForce` تحتوي على UUID الخاص بك (أو تخطَّ هذه الخطوة إن لم يكن لديك قرص ثانوي):

```bash
lsblk -f  # اعثر على UUID الخاص بقرصك
```

```nix
fileSystems."/mnt/gaming" = lib.mkForce {
  device = "/dev/disk/by-uuid/YOUR-UUID-HERE";
  fsType = "btrfs";
  options = [ "defaults" "nofail" ];
};
```

### 7. اضبط الإقلاع المتعدد في Limine (اختياري)

> تخطَّ هذه الخطوة إن كان لديك NixOS فقط على جهازك.

يستطيع Limine إقلاع أنظمة تشغيل أخرى موجودة على أقراص منفصلة. يتحكم `boot.local.nix` في المدخلات الإضافية — وهو مُدرج في gitignore ولا يستبدله `git pull` أبدًا.

**لا تعدّل `modules/system/boot/boot.nix` مباشرة أبدًا** — فهو يُستبدل عند `git pull`.

#### إذا استخدمت المثبّت الآلي

اكتشف المثبّت أنظمة التشغيل الأخرى لديك تلقائيًا من NVRAM الخاصة بـ EFI (`efibootmgr`) وكتب `boot.local.nix` نيابةً عنك — لا حاجة لأي إجراء يدوي. يمكنك مراجعة النتيجة:

```bash
cat modules/system/boot/boot.local.nix
```

#### إذا كنت تثبّت يدويًا

**احصل على PARTUUID الخاصة بك:**

```bash
lsblk -o NAME,FSTYPE,SIZE,PARTLABEL,PARTUUID
```

ابحث عن الأقسام ذات نوع نظام الملفات `vfat` والتسمية `EFI system partition` — هذه هي أقسام ESP لديك.

**عدّل `modules/system/boot/boot.local.nix`** وأضف مدخلاتك:

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

> **نصيحة:** يعتمد مسار EFI بعد UUID على مدير الإقلاع الذي يستخدمه نظام التشغيل الآخر. المسارات الشائعة:
> - Windows: `/EFI/Microsoft/Boot/bootmgfw.efi`
> - CachyOS (Limine): `/EFI/limine/BOOTX64.EFI`
> - Arch/Manjaro (GRUB): `/EFI/grub/grubx64.efi`
> - أي توزيعة (بديل احتياطي): `/EFI/BOOT/BOOTX64.EFI`

إن لم يكن لديك نظام تشغيل آخر لإضافته، فاترك `extraEntries` فارغة:

```nix
{
  extraEntries = "";
}
```

> `boot.local.nix` مُدرج في `.gitignore` — فلن يستبدله `git pull` أبدًا.

### 8. حدّث إعدادات git

`modules/home/git.nix` مُدرج في gitignore (مثل `local.nix`) — انسخ القالب المتتبَّع واملأ هويتك:

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

- `init.defaultBranch = "main"` — الاسم المستخدم للفرع الأول عند تنفيذ `git init` لمستودع جديد (لا يؤثر على فرع هذا المستودع نفسه، بل على الفروع التي تنشئها أنت فقط).
- `pull.rebase = false` — ما يفعله `git pull` عندما يتباعد فرعك المحلي والبعيد: `false` يدمج (ينشئ commit دمج، وهو السلوك الافتراضي والأبسط)، و`true` يعيد تأسيس التزاماتك المحلية فوق البعيد (تاريخ خطي، لكنه يعيد كتابة التزاماتك — تجنّبه إن لم تكن مرتاحًا مع تعارضات rebase). `false` هو الخيار الأكثر أمانًا لمستودع إعدادات شخصي.

> إذا كان الملف مفقودًا، فإن `common.nix` يتجاوزه ببساطة — لن يضبط Home Manager أي إعدادات لـ git حتى تنسخه، لكن لن ينكسر شيء.

### 9. فعّل/عطّل الوحدات الاختيارية

في `hosts/roudix/local.nix`:

```nix
roudix.gaming.enable         = true;
roudix.flatpak.enable        = true;   # Flatpak + تحديث تلقائي يومي
roudix.fstrim.enable         = true;   # موصى به لأقراص SSD/NVMe
roudix.virtualization.enable = false;  # فعّله لـ QEMU/KVM
roudix.vmGuest.enable        = true;   # فعّله داخل آلة افتراضية فقط
roudix.hosts.gtaFix.enable   = true;   # حظر قياسات BattlEye عن بُعد (إصلاح GTA)
roudix.autoupdate.enable     = true;   # git pull تلقائي + nh os boot عند حدوث تغييرات
roudix.zen.enable            = false;  # تثبيت Zen Browser (معطّل افتراضيًا)
roudix.mesa.useGit           = false;  # true = mesa-git (تجريبي، الأحدث على الإطلاق — قد يفشل البناء)، false = nixpkgs المستقر
roudix.boot.bootloader       = "limine";  # "limine" أو "systemd-boot"
roudix.matrixClient          = "none"; # "element" أو "cinny" أو "none"
```

> **تذكير:** إذا ضبطت `roudix.autoupdate.enable = true`، فاضبط الفاصل الزمني أيضًا:
> ```nix
> roudix.autoupdate.interval = "1h"; # 1h, 6h, 12h, 24h...
> ```

### 10. خصّص fastfetch (اختياري)

افتراضيًا يعرض Roudix شعاره بصيغة ASCII في fastfetch. يمكنك استبداله في `home/local.nix` دون المساس بـ git:

```nix
# استخدم صورة مخصصة (تتطلب طرفية kitty)
programs.fastfetch.settings.logo = {
  type = "kitty-direct";
  source = "/home/youruser/Pictures/my-logo.png";
  padding = { top = 1; left = 3; };
  width = 38;
};

# استخدم ملف ASCII مخصصًا
programs.fastfetch.settings.logo = {
  type = "file";
  source = "/home/youruser/.config/fastfetch/my-logo.txt";
  padding = { top = 1; left = 3; };
  width = 38;
};

# استبدل إعدادات fastfetch بالكامل (يستبدل كل شيء)
programs.fastfetch.settings = lib.mkForce {
  "$schema" = "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json";
  logo = { ... };
  display = { separator = "  "; color = "33"; };
  modules = [ ... ];
};
```

> يستبدل `lib.mkForce` إعدادات Roudix الافتراضية بالكامل. ودونه تُدمج مفاتيحك مع الإعدادات الافتراضية.
> راجع `home/local.nix.example` لمزيد من الأمثلة.

### 11. ابنِ

> **إذا لم تكن flakes وnix-command مفعّلتين بعد** (تثبيت NixOS جديد):

```bash
nix --extra-experimental-features 'nix-command flakes' shell nixpkgs#git -c sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

> **وإلا:**

```bash
sudo nixos-rebuild boot --flake path:$(pwd)#roudix --accept-flake-config
```

بعد اكتمال البناء، استخدم أسماء fish المستعارة في جميع العمليات اللاحقة.

> الملفات الثلاثة `local.nix` وكذلك `boot.local.nix` كلها مُدرجة في `.gitignore` — فلن يستبدلها `git pull` أبدًا.
