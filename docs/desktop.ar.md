[English](desktop.md) · [Français](desktop.fr.md) · [Español](desktop.es.md) · [Português (Brasil)](desktop.pt_BR.md) · [Русский](desktop.ru.md) · [简体中文](desktop.zh_CN.md) · [हिन्दी](desktop.hi.md) · **العربية**

# بيئات سطح المكتب

بدّل سطح المكتب في أي وقت باستخدام `roudix-switch <de>` أو عبر الواجهة الرسومية **Roudix Customizer** (الحزمة `roudix-switcher`) — دون الحاجة إلى مضيف (host) منفصل. لم تعد هذه الواجهة تقتصر على تبديل سطح المكتب: فهي تغطي الآن في تطبيق واحد سطح المكتب، والألعاب (مفاتيح تبديل لكل تطبيق)، والمحرّر، والطرفية، والمتصفح، وصدفة تسجيل الدخول، ومدير الملفات، وعميل الدردشة (Discord/Matrix)، والتكامل (حزمة keyring/portal).

| القيمة | سطح المكتب | ملاحظات |
|--------|------------|---------|
| `niri` | Niri + (Noctalia, DMS) | الافتراضي — Wayland بتبليط قابل للتمرير (scrollable tiling) |
| `hyprland` | Hyprland + (Noctalia, DMS, Caelestia) | Wayland بتبليط ديناميكي — يُشغَّل عبر UWSM |
| `mangowc` | MangoWC + (Noctalia, DMS) | مُركِّب Wayland |
| `umbriel` | Umbriel + Noctalia | تبليط قابل للتمرير — المُركِّب الأصلي الخاص بـ Noctalia، مع Noctalia فقط (دون تبديل الصدفة) |
| `gnome` | GNOME | |
| `kde` | KDE Plasma 6 | plasma-login-manager، KDE Connect |
| `cinnamon` | Cinnamon | جلسة X11 + LightDM — سطح مكتب كلاسيكي، مناسب للعتاد القديم (GNOME 49 يعمل على Wayland فقط) |
| `cosmic` | COSMIC | سطح مكتب Wayland من System76 (cosmic-comp)، وcosmic-greeter |

للتغيير بشكل دائم، عدّل `hosts/roudix/local.nix`:

```nix
roudix.desktop.type = "niri"; # "niri" أو "hyprland" أو "mangowc" أو "gnome" أو "kde" أو "cinnamon" أو "cosmic"
```

أو استخدم دالة fish — فهي تعدّل الإعدادات وتعيد البناء في خطوة واحدة:

```fish
roudix-switch kde
```

> **ملاحظة:** يستخدم `roudix-switch` الأمر `nh os boot` — تُطبَّق التغييرات عند إعادة التشغيل التالية.

---

## الصدفات الرسومية (Niri وHyprland وMangoWC فقط)

بالنسبة لمُركِّبات Wayland (Niri وHyprland وMangoWC) يمكنك تبديل حزمة الصدفة/الشريط بشكل مستقل عن المُركِّب. وفي Hyprland، **شجرة إعدادات واحدة** (`dotfiles/hyprland/`) تحتوي على اختصارات لوحة المفاتيح المشتركة وتختار الصدفة بحسب `roudix.desktop.shell`.

| القيمة | الصدفة | Hyprland |
|--------|--------|----------|
| `noctalia` | Noctalia | `dotfiles/hyprland/` |
| `dms` | Dux Shell | `dotfiles/hyprland/` |
| `caelestia` | Caelestia | `dotfiles/hyprland/` |

**ملاحظة:** Caelestia متاحة على Hyprland فقط. تُحقَن الصدفة في الجلسة عبر `ROUDIX_HYPR_SHELL`، لذا لا توجد أشجار منفصلة `hyprland-dms/` أو `hyprland-caelestia/` تحتاج إلى إبقائها متزامنة.

### التشغيل التلقائي للصدفة

يعتمد التشغيل على الصدفة والمُركِّب المختارين، مع آلية تشغيل واحدة فقط لكل صدفة:

- **Hyprland + Noctalia:** تشغيل `noctalia` من خطّاف Lua ‏`hyprland.start`.
- **Hyprland + Caelestia:** تشغيل `caelestia-shell` من خطّاف Lua ‏`hyprland.start`.
- **Hyprland + DMS:** خدمة systemd للمستخدم الخاصة بـ DMS؛ ويصدّر Hyprland بيئة الجلسة إلى systemd عند البدء.
- **MangoWC + Noctalia:** تشغيل `noctalia` من `autostart_sh` في MangoWC.
- **MangoWC + DMS:** خدمة systemd للمستخدم الخاصة بـ DMS، تُفعَّل عبر `mango-session.target`؛ ولذلك لا ينفّذ MangoWC الأمر `dms run`.

يجب ألا يُشغَّل DMS من systemd ومن المُركِّب معًا: إذ توصي وثائقه الرسمية بإزالة `dms run` عند استخدام خدمة systemd.

للتغيير، عدّل `hosts/roudix/local.nix`:

```nix
roudix.desktop.shell = "noctalia"; # "noctalia" أو "dms" أو "caelestia"
```

ثم أعد البناء:

```fish
rebuild
```

أو استخدم دالة fish (متاحة على Niri وHyprland وMangoWC فقط) — فهي تعدّل الإعدادات وتعيد البناء في خطوة واحدة:

```fish
roudix-shell-switch dms
```

> **ملاحظة:** يستخدم `roudix-shell-switch` الأمر `nh os boot` — تُطبَّق التغييرات عند إعادة التشغيل التالية.

---

## نسخة nixpkgs أو أحدث نسخة (flake)

يأتي Niri وMangoWC وUmbriel دائمًا من flake الخاص بكل منها. أما بالنسبة للصدفة (ومعها الـ greeter المرافق لها)، فيستخدم Roudix افتراضيًا نسخة **nixpkgs**. وللحصول على أحدث نسخة، المبنية من flake المشروع نفسه، فعّلها لكل مكوّن في `local.nix` — أو من `roudix-switcher` / المثبّت، حيث لا يظهر المفتاح إلا للصدفة التي اخترتها:

```nix
roudix.desktop.latest.noctalia  = true;  # Noctalia (+ noctalia-greeter)
roudix.desktop.latest.dms       = true;  # Dux Shell (+ dms-greeter)
roudix.desktop.latest.caelestia = true;  # Caelestia (يتبعها greeter الخاص بـ DMS)
```

ليس لـ Hyprland نسخة flake في Roudix: فهو يأتي دائمًا من nixpkgs.

> **تنبيه:** إعدادات Roudix تُكتب **أولًا لنسخ flake (الأحدث)**. وعلى نسخ nixpkgs، يُعدّ ظهور خطأ في الإعدادات يفيد بأن خيارًا أو إعدادًا أو مفتاح إعداد *غير موجود* أمرًا **طبيعيًا**: فقد أُضيف بعد النسخة التي يوفّرها nixpkgs. انتظر حتى يلحق nixpkgs بالركب، أو اضبط المكوّن على `true`.

> إذا لم تكشف وحدة flake عن خيار `package` (وهذا ممكن مع DMS وMangoWC والـ greeter الخاص بـ DMS)، فلا يمكن تطبيق نسخة nixpkgs: يبقى Roudix على نسخة flake ويطبع تحذيرًا أثناء البناء.

---

## تخصيصات المُركِّب الشخصية (Overrides)

يُضبط Niri وUmbriel أصليًا في Nix ‏(`programs.niri.settings` / `programs.umbriel.settings`) — وهما attrsets حقيقية ومُنمَّطة، لا ملف نصي مُولَّد. وهذا يعني أن التخصيصات ليست سوى Nix: أضف مفتاحًا غير موجود بعد فيندمج تلقائيًا؛ أما إن لمستَ مفتاحًا يضبطه المستودع أصلًا (المخرج نفسه، الاختصار نفسه) فستحتاج إلى `lib.mkForce`، وإلا سيرفض Nix البناء مع خطأ «conflicting definitions».

يبقى MangoWC وHyprland نصيَّين (انظر أدناه).

يمكنك وضع التخصيصات مباشرة في `modules/home/local.nix`، لكن إن كنت تخصّص مُركِّبًا واحدًا كثيرًا فإن ملفًا مخصصًا يُبقي الأمور أكثر ترتيبًا — إذ يستورد `modules/home/local.nix` تلقائيًا الملفات `modules/home/niri-custom.nix` و`modules/home/umbriel-custom.nix` و`modules/home/mango-custom.nix` إن وُجدت (انسخ ملف `*.example` المقابل للبدء؛ وهي مستثناة في gitignore مثل `local.nix`).

**Niri**

```nix
# تغيير شاشة يضبطها niri-flake أصلًا (يتطلب lib.mkForce)
# — شغّل `niri msg outputs` داخل الجلسة لمعرفة اسم الموصّل الحقيقي
programs.niri.settings.outputs."Lenovo Group Limited Legion 27Q-10 UNA07260".mode =
  lib.mkForce { width = 3840; height = 2160; refresh = 144.0; };

# إعادة ربط اختصار يعرّفه المستودع أصلًا (يتطلب lib.mkForce)
programs.niri.settings.binds."Mod+T" = lib.mkForce {
  action.spawn = [ "alacritty" ];
};

# إضافة اختصار غير موجود بعد (لا حاجة إلى mkForce)
programs.niri.settings.binds."Mod+Shift+V".action.spawn = [ "pavucontrol" ];

# إضافة قاعدة نافذة — القوائم تُدمج (CONCATENATE) عبر الملفات، لذا تُضاف هذه
# فوق قواعد المستودع ببساطة، دون حاجة إلى mkForce
programs.niri.settings.window-rules = [
  { matches = [ { app-id = "mpv"; } ]; open-floating = true; }
];
```

**Umbriel**

```nix
# تغيير مخرج (يتطلب lib.mkForce — شغّل `umbriel outputs` لمعرفة الاسم الحقيقي)
programs.umbriel.settings.output."DP-1".mode = lib.mkForce "3840x2160@144";

# إعادة ربط اختصار يعرّفه المستودع أصلًا
programs.umbriel.settings.keybinds."Mod+C" = lib.mkForce "spawn:some-command";

# إضافة اختصار غير موجود بعد
programs.umbriel.settings.keybinds."Mod+Shift+V" = "spawn:pavucontrol";

# إضافة قاعدة نافذة
programs.umbriel.settings.window_rule = [
  { match.app_id = "^mpv$"; default_floating = true; }
];
```

**MangoWC** ما زال يحمّل في آخر إعداداته ملف تخصيص شخصي يولّده home-manager — **لا يمسّه `git pull` أبدًا** — لأنه عمليًا لا يملك مخطط Nix مُنمَّطًا:

- MangoWC ← `~/.config/mango/user.conf`

```nix
xdg.configFile."mango/user.conf".text = lib.mkForce ''
  monitorrule=name:DP-1,width:2560,height:1440,refresh:144,x:0,y:0,scale:1,vrr:1,rr:0,tearing:1
'';
```

وبما أنه كتلة نصية كبيرة وليس بضعة أسطر من Nix، فمكانه الأنسب ملف خاص به — انظر `modules/home/mango-custom.nix.example`.

**يستخدم Hyprland الآن إعدادات Lua المعيارية في `dotfiles/hyprland/`.** نقطة الدخول هي `dotfiles/hyprland/hyprland.lua`، التي تحمّل وحدات `config/` الخاصة بالشاشات والتخطيطات والرسوم المتحركة والاختصارات وقواعد النوافذ وتكاملات الصدفة. وينسخ Nix هذه الشجرة كما هي إلى `~/.config/hypr/`.

يستهدف الإعداد الحالي Hyprland 0.55 فما فوق، ويستخدم التخطيطات الأصلية `dwindle` و`master` و`scrolling`. وتولّد وحدة Nix محمِّلًا صغيرًا `config/nix-plugins.lua` قبل نقطة الدخول؛ و`borders-plus-plus` مضمَّن مع Roudix. أما كتلة `dynamic_cursors` فتبقى اختيارية ولا تُطبَّق إلا عند وجود تلك الإضافة.

### تخصيص Hyprland

القيم الخاصة بالجهاز (مخرجات `DP-1`/`DP-3`، والشاشة الرئيسية، والتطبيقات الافتراضية، ولوحة المفاتيح، إلخ) موجودة ضمن `dotfiles/hyprland/config/`. عدّلها مباشرة إن كنت تحتفظ بإعداد Hyprland في مستودع Roudix.

وللتخصيصات الشخصية دون تعديل الملفات المتتبَّعة، استخدم `modules/home/local.nix` مع `xdg.configFile."hypr/..."` و`lib.mkForce`.

> بعد تغيير إعدادات Lua، شغّل `rebuild`. وقد يلزم إعادة تشغيل الجلسة عند تغيير الصدفة أو البيئة.

> انظر `modules/home/niri-custom.nix.example` و`modules/home/umbriel-custom.nix.example` و`modules/home/mango-custom.nix.example` و`modules/home/local.nix.example` للاطلاع على القائمة الكاملة للأمثلة.

---

## تخصيصات GNOME

عند استخدام `roudix.desktop.type = "gnome"`، تكون إدارة الإضافات في `hosts/roudix/local.nix` وتخصيصات المظهر في `modules/home/local.nix`.

**إضافة إضافات فوق الإضافات الافتراضية** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [
  pop-shell
];
```

**تعطيل إضافة افتراضية عبر UUID** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.disabledExtensions = [
  "arcmenu@arcmenu.com"
];
```

**الجمع بين الاثنين — مثلًا استبدال ArcMenu بمشغّل تطبيقات آخر** (`hosts/roudix/local.nix`)
```nix
roudix.gnome.extraExtensions = with pkgs.gnomeExtensions; [ pop-shell ];
roudix.gnome.disabledExtensions = [ "arcmenu@arcmenu.com" ];
```

**تغيير المظهر يدويًا (موصى به)**

يوفّر Roudix مظهر GNOME (الخلفية، والسمة الداكنة، والأيقونات، والمؤشر، وإعدادات الإضافات) بوصفه *قيمًا افتراضية*. غيّر أي شيء من الإعدادات أو Tweaks أو تفضيلات إحدى الإضافات فيصبح ملكك: لا تُرجعه إعادة البناء أبدًا. وتغيّر تحديثات Roudix القيم الافتراضية للإعدادات التي لم تلمسها فقط.

**فرض قيمة من إعداداتك** (`modules/home/local.nix`)

إن كنت تفضّل تثبيت قيمة بشكل تصريحي، فاضبطها عبر home-manager. وخلافًا للطريقة اليدوية أعلاه، تُعاد هذه القيمة في **كل** عملية إعادة بناء وتتغلب على ما تغيّره في الواجهة:
```nix
dconf.settings."org/gnome/desktop/background".picture-uri =
  "file:///home/youruser/Pictures/my-wallpaper.png";
dconf.settings."org/gnome/desktop/background".picture-uri-dark =
  "file:///home/youruser/Pictures/my-wallpaper-dark.png";
dconf.settings."org/gnome/desktop/interface".color-scheme = "prefer-light"; # أو "prefer-dark"
dconf.settings."org/gnome/desktop/interface".icon-theme = "Papirus";
dconf.settings."org/gnome/desktop/interface".cursor-theme = "capitaine-cursors";
dconf.settings."org/gnome/desktop/interface".cursor-size = 32;
```
لا حاجة إلى `lib.mkForce`: فلم يعد home-manager يعرّف هذه المفاتيح.

**استعادة القيم الافتراضية لـ Roudix** لإعداد معيّن (أو لقسم كامل)
```sh
dconf reset /org/gnome/desktop/interface/icon-theme
dconf reset -f /org/gnome/shell/extensions/dash-to-panel/
```

> انظر `hosts/roudix/local.nix.example` و`modules/home/local.nix.example` لجميع خيارات تخصيص GNOME المتاحة.

---

## تخصيصات KDE Plasma

عند استخدام `roudix.desktop.type = "kde"`:

يطبّق Roudix مظهر KDE الخاص به **مرة واحدة فقط**، وليس في كل إعادة بناء، لذا يبقى كل ما تغيّره في إعدادات النظام:

- **السمة الداكنة والأيقونات والمؤشر**: تُطبَّق عند أول تسجيل دخول فقط، وتحرسها الملف `~/.local/state/roudix/kde-theme-seeded`. لاستعادة مظهر Roudix عمدًا: `rm ~/.local/state/roudix/kde-theme-seeded` ثم سجّل الخروج والدخول.
- **NumLock عند بدء التشغيل وخلفية شاشة القفل**: قيم KConfig افتراضية عادية في `/etc/xdg`، تقع أدنى من `~/.config` الخاص بك ولا تتغلب عليه أبدًا.
- **الخلفية واللوحة**: يطبّقهما plasma-manager عند أول تسجيل دخول، ثم لا يعيد تشغيلهما إلا إذا غيّر Roudix نفسه تعريفهما في تحديث.

**تثبيت القيم من إعداداتك** (`modules/home/local.nix`)

كل ما تضبطه عبر plasma-manager يُعاد تطبيقه في **كل** عملية إعادة بناء، لذا استخدمه فقط لما تريده تصريحيًا:

**الخلفية**
```nix
programs.plasma.workspace.wallpaper = lib.mkForce "/home/youruser/Pictures/wallpaper.jpg";
```

**مخطط الألوان / الأيقونات / المؤشر**
```nix
programs.plasma.workspace.colorScheme = "BreezeDark";
programs.plasma.workspace.iconTheme = "Papirus-Dark";
programs.plasma.workspace.cursor.theme = "capitaine-cursors-white";
```

**شريط المهام / اللوحات**
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

> لا حاجة إلى `lib.mkForce` إلا مع `wallpaper` و`panels`، فهما ما زالا معرَّفين في `modules/home/desktop/kde/default.nix`.

## الإعدادات الافتراضية لـ Cinnamon

يأتي Cinnamon افتراضيًا بخلفية Roudix Kitsune، على سطح المكتب وعلى شاشة تسجيل الدخول في LightDM، ويستخدم شعار Roudix أيقونةً للقائمة، ويثبّت في اللوحة المتصفح الافتراضي (أول عنصر في `roudix.browsers`) وRoudix Store والإعدادات. وتتبع تطبيقات GTK4 / libadwaita السمة الداكنة. هذه كلها قيم افتراضية: لا تُطبَّق إلا على ما لم يغيّره المستخدم. وعناصر اللوحة المثبّتة (المتصفح، وNemo، وRoudix Store، والإعدادات) وأيقونة القائمة هي قيم افتراضية للـ applets، تُوفَّر كنسخ مُعدَّلة (patched) من applet-ين: لا يُعاد بناء أي شيء من Cinnamon.

ليس لشاشة تسجيل الدخول (slick-greeter) تطبيق إعدادات. غيّر خلفيتها بما يلي:

```bash
roudix-lightdm-wallpaper ~/Pictures/wallpaper.jpg   # لا حاجة إلى إعادة بناء
roudix-lightdm-wallpaper --reset                    # العودة إلى Kitsune
```

تجاوز التطبيقات المثبّتة في `hosts/roudix/local.nix`:

```nix
roudix.desktop.cinnamon.pinnedApps = [ "firefox.desktop" "io.roudix.store.desktop" "cinnamon-settings.desktop" ];
```

## الإعدادات الافتراضية لـ COSMIC

يأتي COSMIC افتراضيًا بخلفية Roudix Kitsune وبتخطيط لوحة المفاتيح المحدد في `roudix.keyboardLayout` / `roudix.keyboardVariant` / `roudix.keyboardOptions`. ويثبّت الـ dock المتصفح (أو المتصفحات) المختار في Roudix (وZen إن كان مفعّلًا)، وCOSMIC Files، وطرفيتك، وRoudix Store، وCOSMIC Settings — بنفس فكرة الـ dash في GNOME ومدير المهام في Plasma. وفي مكتبة التطبيقات، تُجمَّع كل تطبيقات Roudix (Store وCustomizer وKernel Switcher وScheduler وHardware Sync وConfig وWelcome) في مجلد **Roudix** ولا تُدرَج بعد الآن ضمن النظام / الأدوات المساعدة. ولا يُثبَّت COSMIC Store: إذ يحلّ Roudix Store محلّه.

هذه قيم افتراضية، تُوفَّر كملفات cosmic-config على مستوى النظام: لا تُطبَّق إلا على ما لم يغيّره المستخدم، ولا تُرجع إعادة البناء أبدًا خيارًا اتخذته في COSMIC Settings.

تستخدم تطبيقات COSMIC ولوحته الخاصة مخطط ألوان Roudix افتراضيًا (`assets/cosmic/`، المولَّد من `assets/palette/Roudix.json`، والمثبَّت كقيم افتراضية للنظام بواسطة `modules/system/desktop/cosmic.nix`، دون تدخل من Home Manager). واختيار سمة أو لون تمييز آخر من الإعدادات > المظهر يتغلب عليه، ولا تمسّ إعادة البناء اختيارك أبدًا. والخيار «تطبيق السمة الحالية على تطبيقات GNOME» (الإعدادات > سطح المكتب > المظهر > الأيقونات وتنسيق أدوات الواجهة) مفعّل افتراضيًا: فـ COSMIC نفسه يصدّر سمته، فتحصل تطبيقات GTK (المتصفحات وتطبيقات Roudix...) على ألوان Roudix فوق adw-gtk3، دون أي CSS يكتبه Roudix. والأيقونات هي Papirus-Roudix (انظر `roudix.iconTheme`)، وتحصل طرفيتك على مخطط ألوان Roudix كما في كل سطح مكتب آخر.

أما `system76-scheduler`، الذي تفعّله وحدة COSMIC في nixpkgs، فهو معطَّل افتراضيًا لأن لدى Roudix حزمة جدولة خاصة به (SCX). وللإبقاء عليه:

```nix
services.system76-scheduler.enable = true;
```

ولتغيير التطبيقات المثبّتة، ما عليك إلا تثبيتها / إلغاء تثبيتها من الـ dock: اختيارك يتغلب على القيمة الافتراضية.
