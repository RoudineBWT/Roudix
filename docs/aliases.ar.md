[English](aliases.md) · [Français](aliases.fr.md) · [Español](aliases.es.md) · [Português (Brasil)](aliases.pt_BR.md) · [Русский](aliases.ru.md) · [简体中文](aliases.zh_CN.md) · [हिन्दी](aliases.hi.md) · **العربية**

# الأسماء المستعارة والدوال

## متاحة في كل مكان

| الاسم المستعار | الإجراء |
|-------|--------|
| `rebuild` | تطبيق الإعدادات فورًا |
| `update` | جلب الإعدادات (pull) وإعادة البناء + switch وتحديث Flatpak (انظر [أدناه](#update)) |
| `cleanup` | حذف الأجيال القديمة + جمع المهملات |
| `noctalia-reload` | إعادة تشغيل Noctalia دون تسجيل الخروج |
| `dms-reload` | إعادة تشغيل Quickshell دون تسجيل الخروج |
| `caelestia-reload` | إعادة تشغيل Quickshell دون تسجيل الخروج |
| `roudix-switch <de>` | تبديل بيئة سطح المكتب (تُطبَّق عند إعادة التشغيل التالية) |
| `roudix-kernel-switch <kernel>` | تبديل نسخة النواة (تُطبَّق عند إعادة التشغيل التالية) |

### `update`

النظير اليدوي لـ[التحديث التلقائي](autoupdate.ar.md): المستودع نفسه، والفرع المتتبَّع نفسه، وقاعدة fast-forward فقط نفسها (لا تُمَسّ التزاماتك المحلية أبدًا). يعمل بمستخدمك العادي ولا يستخدم `sudo` إلا عند الحاجة.

1. `git pull --ff-only` للفرع المتتبَّع (يُتخطى إذا كنت على فرع آخر، مثل فرع ميزة)
2. `nh os switch` (أو `nh os boot` مع `--boot`)
3. تحديث Flatpak للمستخدم والنظام، ثم إزالة بيئات التشغيل غير المستخدمة (لا يُعدّ فشلها خطأً قاتلًا)

ملف `flake.lock` الذي تحصل عليه من git هو الذي بنته CI وتحققت منه بالفعل، لذا فإن `update` العادي **لا** يرفع مدخلات flake.

| الخيار | التأثير |
|--------|--------|
| `-i`, `--inputs [name…]` | يرفع أيضًا مدخلات flake محليًا (جميعها، أو المحددة فقط). إذا فشل البناء يُستعاد `flake.lock` |
| `-b`, `--boot` | التطبيق عند الإقلاع التالي بدلًا من switch الآن |
| `-c`, `--check` | الإبلاغ فقط عمّا إذا كانت هناك التزامات جديدة |
| `-n`, `--dry` | تشغيل تجريبي (`nh --dry`): لا يُجلب ولا يُرفع ولا يُفعَّل ولا يُحدَّث أي شيء |
| `--changes` | يعرض ما يختلف في نظام الإقلاع التالي عن النظام العامل (مفيد بعد تحديث تلقائي) |
| `--log` | يعرض سجل آخر تشغيل (محفوظ في `~/.local/state/roudix/update.log`) |
| `--no-inputs` | تخطي رفع المدخلات (مفيد مع `roudix.update.bumpInputs = true`) |
| `--no-pull` / `--no-flatpak` | تخطي الـ pull / تحديث Flatpak |

```fish
update                    # pull + إعادة بناء + switch
update --inputs           # رفع كل المدخلات ثم إعادة البناء
update --inputs nixpkgs   # رفع nixpkgs فقط
```

على جهاز يتتبّع `dev` ويريد دائمًا مدخلات حديثة، اضبط `roudix.update.bumpInputs = true;` في `local.nix`: عندها يتصرف `update` العادي مثل `update --inputs`.

> بعد `update --inputs`، يصبح `flake.lock` تعديلًا محليًا: نفّذ commit وpush له (أو `git checkout flake.lock`)، وإلا فقد يرفض pull التحديث التلقائي التالي العمل إذا لمست CI ملف lock في هذه الأثناء.

## Niri وHyprland وMangoWC فقط

| الاسم المستعار | الإجراء |
|-------|--------|
| `roudix-shell-switch <shell>` | تبديل الواجهة الرسومية (تُطبَّق عند إعادة التشغيل التالية) |

### الاستخدام

```fish
# تبديل بيئة سطح المكتب
roudix-switch niri
roudix-switch hyprland
roudix-switch mangowc
roudix-switch umbriel
roudix-switch gnome
roudix-switch kde
roudix-switch cinnamon
roudix-switch cosmic

# تبديل نسخة النواة — تعتمد القائمة على hardware.myGpu، انظر docs/installation.md
# AMD/Intel (xddxdd):
roudix-kernel-switch cachyos-latest-v3
roudix-kernel-switch cachyos-lts-lto-v3
roudix-kernel-switch cachyos-bore
# Nvidia (Chaotic-Nyx — مجموعة أصغر، لازمة لذاكرة nvidia_cachyos الثنائية المؤقتة):
roudix-kernel-switch cachyos
roudix-kernel-switch cachyos-lts
# نوى nixpkgs العادية — متاحة في مساري GPU كليهما، خارج overlay الخاصة بـ CachyOS
# (على Nvidia تعود إلى وحدة Nvidia معاد بناؤها محليًا، دون ذاكرة nvidia_cachyos المؤقتة):
roudix-kernel-switch zen
roudix-kernel-switch nixpkgs-lts
roudix-kernel-switch nixpkgs-latest
roudix-kernel-switch nixpkgs-testing
roudix-kernel-switch xanmod-lts
roudix-kernel-switch xanmod-latest

# تبديل الواجهة الرسومية (Niri وHyprland وMangoWC فقط)
roudix-shell-switch noctalia
roudix-shell-switch dms
roudix-shell-switch caelestia # لـ hyprland فقط
```

الأوامر الثلاثة تعدّل `hosts/roudix/local.nix` تلقائيًا وتشغّل `nh os boot` — لا حاجة لإعادة البناء يدويًا. تُطبَّق التغييرات عند إعادة التشغيل التالية.

> **ملاحظة:** يكتب `roudix-kernel-switch` تلقائيًا في `hardware.myKernel` أو `hardware.myKernelChaotic` حسب `hardware.myGpu` الحالي لديك — مرّر اسم النسخة المطابق لقائمة بطاقتك الرسومية (انظر الجدول أعلاه).
