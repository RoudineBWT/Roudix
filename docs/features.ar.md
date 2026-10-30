[English](features.md) · [Français](features.fr.md) · [Español](features.es.md) · [Português (Brasil)](features.pt_BR.md) · [Русский](features.ru.md) · [简体中文](features.zh_CN.md) · [हिन्दी](features.hi.md) · **العربية**

# الميزات

## النواة والأداء

- نواة CachyOS مع تفعيل NTSync (وحدة `ntsync`)
- مزوّدان للنواة، يُختاران تلقائيًا بحسب `hardware.myGpu`:
  - AMD/Intel → [xddxdd/nix-cachyos-kernel](https://github.com/xddxdd/nix-cachyos-kernel)، 36 إصدارًا (`hardware.myKernel`)
  - Nvidia → Chaotic-Nyx، 4 إصدارات (`hardware.myKernelChaotic`) — يوفّر `nvidia_cachyos`، وهو تعريف مُجمَّع مسبقًا ومطابق لنواتهم، ولذلك لا تُعاد بناء وحدة Nvidia محليًا عند كل تحديث للنواة
- يمكن أيضًا اختيار نوى nixpkgs العادية مع كلا المزوّدين، خارج طبقة CachyOS تمامًا — `zen` (`linuxPackages_zen`) و`nixpkgs-lts` و`nixpkgs-latest` و`nixpkgs-testing` (RC/mainline) و`xanmod-lts` / `xanmod-latest` (XanMod). على Nvidia تعود هذه النوى إلى وحدة Nvidia تُبنى محليًا (دون ذاكرة التخزين المؤقت `nvidia_cachyos`)
- يأخذ `hardware.myKernelSource` (`nixpkgs` / `master` / `staging-next`) نوى nixpkgs هذه فقط من nixpkgs أحدث للحصول على تحديثات النواة أبكر، دون المساس ببقية النظام
- تفعيل ZRAM (100% من الذاكرة، zstd، swappiness 150)
- zswap معطّل
- ضبط ميكروكود المعالج تلقائيًا (Intel أو AMD)
- Intel: يُطبَّق `split_lock_detect=off` تلقائيًا
- تفعيل ananicy-cpp (خدمة أولوية العمليات، قواعد CachyOS)
- دعم مجدول SCX — تبديل مباشر دون الحاجة إلى إعادة تشغيل (bpfland وlavd وflash وp2dq وrusty…) عبر واجهة Kernel Switcher الرسومية — يكفي طلب كلمة مرور واحد عبر `scx-switch` لإيقاف/تشغيل ananicy-cpp وتبديل المجدول دفعة واحدة — **ملاحظة:** SCX لا يبقى مفعّلًا بعد إعادة التشغيل؛ بعد إعادة التشغيل يعمل ananicy-cpp من جديد تلقائيًا ويجب إعادة تطبيق المجدول عبر واجهة Kernel Switcher الرسومية

## الإقلاع

- محمّل الإقلاع Limine (الافتراضي) — حديث وسريع ويدعم الأقراص المتعددة — أو systemd-boot، ويُختار عبر `roudix.boot.bootloader`
- إعادة تسمية مدخل UEFI تلقائيًا إلى "Roudix"
- قائمة إقلاع متعددة الأنظمة (Windows وتوزيعات Linux أخرى على أقسام ESP منفصلة)
- تعرض تسمية الإقلاع اسم Roudix + إصدار NixOS

## الألعاب

- Steam + Proton-GE + Proton-CachyOS (x86_64-v3) + Gamescope (gamescope-wsi، الجلسة معطّلة افتراضيًا)
- متغيرات بيئة التقاط OBS مضبوطة مسبقًا (`OBS_VKCAPTURE` عبر `environment.sessionVariables`)
- طبقة MangoHud أفقية مخصّصة (تسمية `Powered By Roudix`)
- دعم أذرع التحكم (Steam Hardware + game-devices-udev-rules)
- دعم 32 بت لـ Wine/Steam
- غلاف `game-performance` — يبدّل إلى ملف أداء `tuned-adm` مخصّص طوال مدة اللعبة، ويُتتبَّع عبر cgroup من نوع `systemd-run --user --scope` (فيستمر حتى لو أعاد Steam عمل fork أو انفصل) ويُستعاد عند الخروج (الاستخدام: `game-performance %command%` في خيارات تشغيل Steam) — GameMode معطّل عمدًا (غير متوافق مع ananicy-cpp هنا)
- `ffmpegthumbnailer` متاح على مستوى النظام كله (صور مصغّرة للفيديو في مديري الملفات)
- `protonup-qt` على KDE، و`protonplus` على بيئات سطح المكتب الأخرى
- Heroic وLutris وFaugus Launcher وPrism Launcher (Minecraft، أو Modrinth App كبديل — `roudix.gaming.apps.modrinth.enable`) وVintage Story (عبر roudix-caches)
- يمكن تفعيل/تعطيل كل تطبيق ألعاب على حدة عبر `roudix.gaming.apps.<lutris|heroic|faugus|prismlauncher|vintagestory|mangohud>.enable` (كلها `true` افتراضيًا)
- عميل Steam المعدَّل [Millennium](https://github.com/SteamClientHomebrew/Millennium) اختياري (سمات + إضافات) — معطّل افتراضيًا، ويُفعَّل بـ `roudix.gaming.steam.millennium.enable = true` (أو من المثبّت). تعديل غير رسمي؛ يستمر عمل تعديل العزل في `game-performance` وأدوات توافق Proton، وإعادته إلى `false` تستعيد Steam الأصلي
- وضع ألعاب اختياري على غرار الكونسول: يضيف `roudix.gaming.gamescopeSession.enable` جلسة "Steam (Gaming Mode)" إلى شاشة تسجيل الدخول (Steam Big Picture داخل gamescope، VRR/HDR/MangoApp، ويُكتشف معدل التحديث عند التشغيل). يفتح خيار "التبديل إلى سطح المكتب" في Steam سطح مكتبك، ويعيدك تطبيق "Return to Gaming Mode" إلى اللعبة دون المرور بشاشة تسجيل الدخول. مبني على GLF-OS؛ ويدعم niri وumbriel وGNOME وKDE وHyprland وMangoWC
- Decky Loader اختياري (إضافات Steam) عبر `roudix.gaming.gamescopeSession.decky.enable`، ويُجلب من flake input الخاص بـ Jovian-NixOS (استخدم `nix flake update jovian` لتحديثه، ولا يوجد sha تحتاج إلى صيانته يدويًا)؛ لا توجد ذاكرة تخزين مؤقت ثنائية، لذا يُجمَّع محليًا عند أول إعادة بناء

## سطح المكتب (Niri)

- Niri، مُركِّب Wayland بنظام تبليط قابل للتمرير — يُوفَّر عبر [niri-flake](https://github.com/epireyn/niri-flake) (epireyn)، ويستخدم `niri-unstable` افتراضيًا، مع ضبط ذاكرة التخزين المؤقت الثنائية `niri-epireyn.cachix.org` مسبقًا
- الإعداد أصيل في Nix (`programs.niri.settings`)، مقسَّم بحسب الموضوع (general وanimations وinput وlayout وoutputs وbinds وrules) ويُتحقق منه وقت البناء عبر `niri validate` — فالإعداد المعطوب يُفشل عملية البناء بدلًا من أن يفشل المُركِّب عند تسجيل الدخول
- تُحفَظ مزامنة السمة الحية في Noctalia/DMS (ألوان مولَّدة من matugen/DMS، وalt-tab، والتمويه) بإلحاق `include` بالإعداد المولَّد بدلًا من تثبيتها بشكل ثابت
- واجهة Noctalia (الإصدار 5) الحديثة
- xdg-desktop-portal-gnome + gtk (بوابتا تسجيل الشاشة وسطح المكتب البعيد مضبوطتان)
- مؤشر Bibata Modern Ice (24 بكسل)
- adw-gtk3 + أيقونات Papirus + Papirus Folders
- Element Desktop مع gnome-libsecret / kwallet6 (يُكتشف تلقائيًا بحسب بيئة سطح المكتب)
- وكيل Polkit الخاص بـ GNOME
- DMS Greeter (greetd)

## سطح المكتب (MangoWC)

- مُركِّب Wayland من نوع MangoWC
- Noctalia / DankMaterialShell
- xdg-desktop-portal-gtk
- مؤشر Bibata Modern Ice (24 بكسل)
- وكيل Polkit الخاص بـ GNOME
- مدير العرض Ly
- adw-gtk3 + أيقونات Papirus + Papirus Folders
- حركة فتح بالتكبير + منحنيات bezier الرسمية
- تفعيل VRR + tearing على شاشة الألعاب (DP-1 1440p@240)
- لقطات الشاشة عبر grim + slurp + satty (للتعليق التوضيحي) — 3 اختصارات مفاتيح
- مبدّل نوافذ rofi (Alt+Tab)
- متغيرات بيئة XDG Desktop Portal مضبوطة مسبقًا (التقاط الشاشة عبر Pipewire وOBS وDiscord Go Live)
- force_tearing + idleinhibit_when_focus لجميع تطبيقات الألعاب (Steam وHeroic وMinecraft وLutris وBottles)
- شفافية النوافذ غير الموجَّه إليها التركيز (0.85)
- Hotarea overview (إيماءة الفأرة عند الزاوية)
- لصق عائم + سحب من بلاطة إلى أخرى
- دعم scratchpad: مجموعة عامة لأي نافذة (نقل/تبديل/استعادة)،
  إضافةً إلى scratchpad مسمّى اختياري (`roudix.mangowc.scratchpadApps`) لكل
  تطبيق من Discord/Element/Telegram/Spotify — ولكل منها مفتاح تبديل خاص به

## سطح المكتب (Umbriel)

- Umbriel، مُركِّب Wayland بنظام تبليط قابل للتمرير — هو المُركِّب الأصلي الخاص بـ Noctalia، ويُوفَّر عبر [noctalia-dev/umbriel](https://github.com/noctalia-dev/umbriel) (لـ Noctalia فقط، دون تبديل الواجهة)
- الإعداد أصيل في Nix (`programs.umbriel.settings`)، مقسَّم بحسب الموضوع (general وappearance وanimation وinput وlayout وoutputs وbinds وrules) ويُتحقق منه وقت البناء (`validateConfig = true`)
- تُحفَظ مزامنة السمة الحية في Noctalia (ألوان مولَّدة من matugen) عبر آلية `include.files` الأصلية في Umbriel، دون لقطة ألوان ثابتة
- مؤشر Bibata Modern Ice (24 بكسل)
- adw-gtk3 + أيقونات Papirus + Papirus Folders
- Hot corners (overview عند تحريك الفأرة إلى الزاوية) ونظرة عامة على مساحات العمل (Mod+O)
- دعم scratchpad (نقل/تبديل/استعادة نافذة عائمة عند الطلب)
- تخصيص التخطيط لكل مساحة عمل (مثل عدم وجود gap في مساحة عمل الألعاب)

## سطح المكتب (Hyprland)

- Hyprland، مُركِّب Wayland بتبليط ديناميكي يُشغَّل عبر UWSM
- واجهة Noctalia الحديثة
- xdg-desktop-portal-hyprland + بوابة gtk
- مؤشر Bibata Modern Ice (24 بكسل)
- وكيل Polkit الخاص بـ GNOME (يبدأ عبر خدمة مستخدم في systemd)
- خدمة خلفيات awww
- لقطات الشاشة عبر grim + slurp + satty (للتعليق التوضيحي) — 3 اختصارات مفاتيح

## سطح المكتب (GNOME)

- GNOME (يتبع فرع nixos-unstable)
- مجموعة منتقاة من الإضافات (blur وtiling وvitals وarcmenu...) — تُفعَّل عبر dconf
- ArcMenu مع شعار Roudix كأيقونة لزر القائمة
- إزالة البرمجيات الزائدة عبر `environment.gnome.excludePackages`
- سمة أيقونات Papirus-Dark
- سمة GTK من نوع adw-gtk3-dark (الوضع الداكن افتراضيًا)
- مؤشر Bibata Modern Ice (24 بكسل)
- خلفية Roudix (فاتحة/داكنة بحسب سمة النظام)
- يُطبَّق `color-scheme = prefer-dark` عبر dconf
- إعدادات الإضافات (ArcMenu وDash to Dock وDash to Panel وBlur My Shell...) مضبوطة مسبقًا عبر `modules/home/desktop/gnome/_extensions.nix`
- أضف الإضافات أو أزلها دون تعديل الملفات الأساسية عبر `roudix.gnome.extraExtensions` / `roudix.gnome.disabledExtensions`
- غيّر الخلفية والسمة والأيقونات والمؤشر في `modules/home/local.nix`

## سطح المكتب (KDE)

- KDE Plasma 6 مع plasma-login-manager (Plasma 6.6+، nixpkgs unstable)
- تفعيل KDE Connect
- xdg-desktop-portal-kde
- سمة أيقونات Papirus-Dark
- مظهر Breeze Dark ومخطط ألوانه
- خلفية Roudix Dark على شاشة تسجيل الدخول وسطح المكتب
- حزم منتقاة: partitionmanager وkcalc وdigikam وvlc...
- إزالة البرمجيات الزائدة (استبعاد Discover)
- غيّر الخلفية واللوحات وسمة الأيقونات في `modules/home/local.nix`

## الموسيقى

اختر واحدًا عبر `roudix.musicPlayer` — `"spotify"` (الافتراضي) أو `"ytmdesktop"`
أو `"sonora"` أو `"none"`.

- `"spotify"` — Spotify مُعدَّل بواسطة Spicetify. سمة محلية، "colorful" افتراضيًا
  (أو "comfy")، إضافةً إلى إضافتَي حظر الإعلانات وإخفاء البودكاست — راجع
  المفاتيح أدناه.
- `"ytmdesktop"` — YouTube Music Desktop App (عميل YouTube Music غير رسمي
  مبني على Electron).
- `"sonora"` — [Sonora](https://github.com/sonorahq/sonora)، عميل أصيل
  (Rust/GPUI) لـ Spotify وYouTube Music وApple Music وDeezer
  وSubsonic في تطبيق واحد. يحدّد الخيار الاختياري `roudix.sonora.provider`
  المزوّد الذي يبدأ منه (`"youtube"` = YouTube Music). وهو لا يتجاوز
  الاشتراكات: إذا كانت خدمة ما تتطلب اشتراكًا فإن Sonora يتطلبه أيضًا.

## التطبيقات المشتركة الاختيارية

تأتي GIMP وInkscape وSongRec وEasyEffects (+ rnnoise-plugin) افتراضيًا، لكن
يمكن تعطيل كلٍّ منها على حدة عبر `roudix.apps.<name>.enable` (`gimp`
و`inkscape` و`songrec` و`easyeffects`).

لا يوجد لدى Signal وZapZap (عميل سطح مكتب غير رسمي لـ WhatsApp بمظهر أصيل)
بديل حقيقي للتبديل بينهما، فهما مجرد قيم منطقية اختيارية (opt-in)،
معطّلة افتراضيًا: `roudix.apps.signal.enable` و`roudix.apps.zapzap.enable`.

أما Fluxer، وهو بديل لـ Discord يمكن استضافته ذاتيًا، فهو من النوع نفسه من القيم
المنطقية الاختيارية: `roudix.apps.fluxer.enable`. وهو غير موجود في nixpkgs بعد، لذا
يُجلب مباشرةً من الحزمة المُجمَّعة مسبقًا `fluxer-desktop` في flake input
المسمى `nix-gaming-edge`. وهو مستقل عمدًا عن `roudix.discord`
و`roudix.gaming.enable` — فلا شيء يمنعك من أن تريد Discord
وFluxer معًا، أو Fluxer دون أي إعداد ألعاب.

يتوفر أيضًا عميل بريد ومدير كلمات مرور، بشكل اختياري (معطّلان
افتراضيًا): `roudix.mailClient` — `"thunderbird"` (كامل الميزات)
أو `"betterbird"` (نسخة متفرعة مضبوطة بدقة من Thunderbird، تُجلب من flake
input المسمى [betterbird-nix](https://github.com/TheAnachronism/betterbird-nix) — وهي
غير موجودة في nixpkgs بعد) أو `"geary"` (عميل GNOME خفيف)؛
`roudix.passwordManager` —
`"bitwarden"` (مزامنة سحابية) أو `"keepassxc"` (خزنة محلية دون اتصال) أو
`"protonpass"` (مزامنة سحابية، حساب Proton).

ويتوفر أيضًا، بشكل اختياري (معطّل افتراضيًا): عميل تورنت عبر
`roudix.torrentClient` — `"qbittorrent"` (غني بالميزات، مبني على Qt)
أو `"fragments"` (عميل GNOME/libadwaita بسيط) أو `"deluge"` (قائم على الإضافات) أو
`"none"` (الافتراضي).

## Spicetify

- السمة: `roudix.spicetify.theme` — `"colorful"` (الافتراضية، sanoojes/spicetify-colorful) أو `"comfy"` (سمة Comfy المضمَّنة)
- مخطط الألوان: `roudix.spicetify.colorScheme` — القيمة `null` (الافتراضية) تستخدم المخطط الافتراضي للسمة نفسها ("noctalia" لـ colorful، و"Comfy" لـ comfy)
- يمكن تفعيل الإضافات كلٌّ على حدة: `roudix.spicetify.extensions.adblock.enable` و`roudix.spicetify.extensions.hidePodcasts.enable` (كلتاهما `true` افتراضيًا)
- تطبيق Marketplace المخصّص: `roudix.spicetify.marketplace.enable` (`true` افتراضيًا)

## المتصفح

- قائمة متصفحات قابلة للضبط عبر الخيار `roudix.browsers`
- يدعم `brave` و`helium` (عبر x13-me/helium-nix، ويتضمن رقعة DRM — يُوصَّل تشغيل Widevine تلقائيًا عبر `modules/home/apps/browser/helium-widevine.nix` عند اختيار `helium`) و`vivaldi` (مع ترميزات ffmpeg) و`firefox` و`librewolf` و`chromium`، أو `[]` لعدم تثبيت أي متصفح
- Zen Browser متاح بشكل منفصل عبر `roudix.zen.enable = true` (معطّل افتراضيًا)؛ ويمكن اختيار القناة عبر `roudix.zen.variant` — `"twilight"` (الافتراضية) أو `"beta"`

## أخرى

- يمكن اختيار Discord عبر `roudix.discord` — `"vencord"` (عميل مُعدَّل، الافتراضي) أو `"vanilla"` (دون تعديل) أو `"none"` (غير مثبَّت)
- يمكن اختيار Telegram عبر `roudix.telegram` — `"telegram"` (Telegram Desktop الرسمي) أو `"ayugram"` (نسخة متفرعة غير رسمية: وضع الشبح، منع الاسترجاع، سجل رسائل محلي...) أو `"none"` (الافتراضي، غير مثبَّت)
- يمكن اختيار محرر الأكواد عبر `roudix.editor` — `"zed"` (الافتراضي) أو `"vscode"` أو `"neovim"` أو `"none"` (أدِر محررك بنفسك، مثل AppImage/Flatpak)
- تخطيط لوحة المفاتيح الرسومي (Wayland) عبر `roudix.keyboardLayout` / `roudix.keyboardVariant` (XKB، مثل `"be"` / `"intl"`) — مستقل عن `console.keyMap` الذي يغطي TTY فقط قبل بدء الجلسة الرسومية؛ ولا أثر له على GNOME/KDE اللذين يديران تخطيطهما بنفسيهما
- حزمة keyring + xdg-desktop-portal للمُركِّبات "العارية" (Niri وHyprland وMangoWC وUmbriel) تُختار عبر `roudix.desktopIntegration` — `"gnome"` (gnome-keyring + xdg-desktop-portal-gtk/-gnome، الافتراضي) أو `"kde"` (KWallet + xdg-desktop-portal-kde + polkit-kde-agent، مع استبدال تطبيقات GNOME بـ Kate / Gwenview / KDE Partition Manager / Dolphin؛ وتبقى adw-gtk3 وnwg-look وqt6ct وgvfs كي تحتفظ تطبيقات GTK بسمتها)؛ ولا أثر له على جلسات GNOME/KDE التي تحتفظ بحزمتها الأصلية
- تفعيل `nix-ld` على مستوى النظام — شغّل الملفات الثنائية الديناميكية غير المعدَّلة دون بيئة FHS (مضبوط مسبقًا بمكتبات شائعة: glibc وopenssl وzlib وlibGL وX11 وlibxkbcommon وdbus وglib وغيرها)
- OBS Studio، يمكن تفعيله على حدة عبر `roudix.contentCreation.obs.enable` (`true` افتراضيًا)، وتُفعَّل الإضافات واحدة تلو الأخرى عبر `roudix.contentCreation.obs.plugins.<name>.enable` (`vkcapture` + `pipewireAudioCapture` مفعَّلتان افتراضيًا؛ ويتوفر أيضًا: `backgroundRemoval` و`moveTransition` و`aitumMultistream` و`gstreamer` و`compositeBlur` و`advancedSceneSwitcher` و`inputOverlay` و`waveform`)
- يمكن اختيار محرر الفيديو عبر `roudix.contentCreation.videoEditor` — `"kdenlive"` (الافتراضي) أو `"davinci-resolve"` (مجاني) أو `"davinci-resolve-studio"` (مدفوع، يحتاج إلى ترخيص) أو `"shotcut"` أو `"none"`؛ ويحصل DaVinci Resolve تلقائيًا على AMD OpenCL ICD عندما يكون `hardware.myGpu = "amd"`
- كاميرا افتراضية `v4l2loopback` تُضبط تلقائيًا لـ OBS/DaVinci (`roudix.contentCreation.virtualCamera.enable`، `true` افتراضيًا)
- Chatterino2، عميل دردشة Twitch، اختياري عبر `roudix.contentCreation.streaming.chatterino.enable`
- يمكن تفعيل/تعطيل مجموعة إنشاء المحتوى بأكملها عبر `roudix.contentCreation.enable`
- GPU Screen Recorder
- خيار Mesa Git لـ AMD — فعّل Mesa التجريبي/الأحدث عبر `roudix.mesa.useGit = true` في `local.nix` (الافتراضي: Mesa المستقر من nixpkgs) — ⚠️ **تجريبي**، وقد يفشل البناء بحسب حالة nixpkgs
- تُطبَّق تلقائيًا معاملات نواة لاستقرار معالجات AMD الرسومية (`mem_sleep_default=deep` و`amdgpu.gpu_recovery=1` و`amdgpu.lockup_timeout=1000` و`amdgpu.runpm=0` و`amdgpu.sg_display=0`) — تعالج التجمّد العشوائي ومشكلات الاستيقاظ من السكون على RDNA2/RDNA3
- يمكن اختيار متحكم RGB عبر `roudix.rgb` — `openlinkhub` (Corsair iCUE Link / Commander، يُحدَّث تلقائيًا عبر CI) أو `openrgb` (متعدد الشركات: Razer وASUS وMSI…) أو `none`
- واجهة OpenLinkHub على الويب متاحة على [http://127.0.0.1:27003](http://127.0.0.1:27003) بمجرد تشغيل الخدمة
- التحكم في إضاءة RGB لذاكرة DDR4/DDR5 عبر OpenLinkHub — فعّله بـ `roudix.memory.enable = true`، واضبط `roudix.memory.type` و`roudix.memory.smBus` و`roudix.memory.sku` (راجع `installation.ar.md`)
- PipeWire مع كتم ضجيج ستيريو عبر rnnoise (nofail، توافق LADSPA_PATH مع 26.05/26.11)
- Flatpak مع مستودع Flathub البعيد + تحديث تلقائي يومي (عبر nix-flatpak)
- مدير البلوتوث Blueman
- عميل Matrix — قابل للضبط عبر `roudix.matrixClient` (`element` أو `cinny` أو `none`) — يختار Element تلقائيًا kwallet6 على KDE وgnome-libsecret في غيره
- يمكن اختيار مشغّل الفيديو عبر `roudix.videoPlayer` — `"vlc"` (أوسع دعم للصيغ، الافتراضي) أو `"clapper"` (مشغّل حديث بواجهة GTK4) أو `"mpv"` (+ yt-dlp، بسيط/للبث) أو `"celluloid"` (واجهة GTK لـ mpv) أو `"none"`؛ ويسري على كل بيئات سطح المكتب (كان سابقًا Clapper مثبَّتًا على المُركِّبات العارية فقط، إضافةً إلى مفتاح mpv منفصل مستقل عن بيئة سطح المكتب)
- تفعيل دعم AppImage عبر `appimage.nix`
- Waydroid (حاوية Android) — اختياري، `roudix.waydroid.enable = true`
- QEMU/KVM + Virt-Manager (اختياري، `roudix.virtualization.enable`)
- vm-curator (اختياري، `roudix.virtualization.vmCurator.enable`) — بديل بواجهة TUI مكتوب بـ Rust عن virt-manager، يتحكم في QEMU مباشرةً (دون libvirt)، مع تسريع ثلاثي الأبعاد ودعم تمرير GPU؛ ويمكن تفعيله بشكل مستقل أو إلى جانب حزمة libvirt
- وحدة تحسينات ضيف الآلة الافتراضية (مشاركة الحافظة، تغيير الحجم تلقائيًا، وكيل QEMU، Spice)
