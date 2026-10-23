[English](autoupdate.md) · [Français](autoupdate.fr.md) · [Español](autoupdate.es.md) · [Português (Brasil)](autoupdate.pt_BR.md) · [Русский](autoupdate.ru.md) · [简体中文](autoupdate.zh_CN.md) · [हिन्दी](autoupdate.hi.md) · **العربية**

# التحديث التلقائي

عندما يكون `roudix.autoupdate.enable = true`، يفحص النظام GitHub كل ساعة (وبعد 5 دقائق من الإقلاع).
إذا اكتُشفت التزامات (commits) جديدة في الفرع المتتبَّع (`main` افتراضيًا)، يقوم بعملية pull ويشغّل `nh os boot path:...` — وتُطبَّق الإعدادات الجديدة عند إعادة التشغيل التالية.
ملفاتك `local.nix` و`username.nix` و`hardware-configuration.nix` والملفات الاختيارية `home/niri-custom.nix` / `home/umbriel-custom.nix` / `home/mango-custom.nix` وكل ما في `dotfiles/perso/` مُدرجة في gitignore ولا يمسّها الـ pull أبدًا.

لضبط الفاصل الزمني أو الفرع، أعِد تعريفهما في `local.nix`:

```nix
{ ... }:
{
  roudix.autoupdate.enable   = true;  # إذا ضبطتها على false هنا، فسيتولى config.roudix.autoupdate التحديث لكن دون git pull
  roudix.autoupdate.interval = "6h";   # الفحص كل 6 ساعات بدلًا من ساعة واحدة
  roudix.autoupdate.branch   = "main"; # الفرع المراد تتبّعه: "main" (مستقر) أو "testing" أو "dev" — يحدده المثبّت
}
```

يُختار الفرع في المثبّت (سواء السكربت أو المثبّت الرسومي في ISO). ويمكنك تغييره لاحقًا من **Roudix Switcher → System → Update branch**، الذي ينقل أيضًا نسختك المحلية `~/.config/roudix` إلى ذلك الفرع قبل إعادة البناء.

التحديث التلقائي يقوم بـ fast-forward فقط: إذا كان في جهازك التزامات محلية غير موجودة على GitHub (أو تباعد الفرع)، فلن يمسّها وسيُرسل لك إشعارًا بدلًا من ذلك.

لعرض آخر تشغيل:

```bash
systemctl status roudix-autoupdate
journalctl -u roudix-autoupdate -n 20
```

لتشغيل تحديث يدويًا في أي وقت:

```fish
update
```

يقوم بالـ pull نفسه (الفرع نفسه، وقاعدة fast-forward فقط نفسها، والقفل نفسه فلا يتداخل أبدًا مع تحديث تلقائي قيد التشغيل)، ثم يعيد البناء ويحدّث تطبيقات Flatpak لديك. راجع [`update`](aliases.ar.md#update) لمعرفة خياراته.

قد يستغرق البناء حتى ساعتين قبل أن يستسلم systemd. وإذا أُنهي التشغيل أو توقف بشكل غير متوقع (انتهاء المهلة، تعطّل)، يُرسَل إشعار؛ أما الخطأ العادي فيُشعِر من تلقاء نفسه. بعد تحديث تلقائي، يعرض `update --changes` ما سيُطبَّق عند الإقلاع التالي.
