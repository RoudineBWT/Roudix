[English](autoupdate.md) · [Français](autoupdate.fr.md) · [Español](autoupdate.es.md) · [Português (Brasil)](autoupdate.pt_BR.md) · [Русский](autoupdate.ru.md) · [简体中文](autoupdate.zh_CN.md) · **हिन्दी** · [العربية](autoupdate.ar.md)

# ऑटो-अपडेट

जब `roudix.autoupdate.enable = true` होता है, सिस्टम हर घंटे GitHub जाँचता है (और बूट के 5 मिनट बाद भी)।
अगर फ़ॉलो की जा रही ब्रांच (डिफ़ॉल्ट रूप से `main`) पर नए कमिट मिलते हैं, तो वह pull करता है और `nh os boot path:...` चलाता है — नया कॉन्फ़िगरेशन अगले रीबूट पर लागू होता है।
आपकी `local.nix`, `username.nix`, `hardware-configuration.nix` फ़ाइलें, वैकल्पिक `home/niri-custom.nix` / `home/umbriel-custom.nix` / `home/mango-custom.nix` और `dotfiles/perso/` के अंदर की हर चीज़ gitignore में हैं और pull उन्हें कभी नहीं छूता।

अंतराल या ब्रांच बदलने के लिए `local.nix` में ओवरराइड करें:

```nix
{ ... }:
{
  roudix.autoupdate.enable   = true;  # अगर यहाँ false कर दें, तो config.roudix.autoupdate अपडेट का काम संभाल लेगा, लेकिन git pull के बिना
  roudix.autoupdate.interval = "6h";   # हर 1 घंटे के बजाय हर 6 घंटे में जाँचें
  roudix.autoupdate.branch   = "main"; # फ़ॉलो की जाने वाली ब्रांच: "main" (स्थिर), "testing" या "dev" — इंस्टॉलर तय करता है
}
```

ब्रांच इंस्टॉलर में चुनी जाती है (स्क्रिप्ट और ग्राफ़िकल ISO इंस्टॉलर दोनों में)। बाद में आप इसे **Roudix Switcher → System → Update branch** से बदल सकते हैं, जो रीबिल्ड से पहले आपके लोकल `~/.config/roudix` चेकआउट को भी उसी ब्रांच पर ले जाता है।

ऑटो-अपडेट केवल fast-forward करता है: अगर आपकी मशीन पर ऐसे लोकल कमिट हैं जो GitHub पर नहीं हैं (या ब्रांच अलग हो गई है), तो वह उन्हें नहीं छूता और इसके बजाय आपको सूचना भेजता है।

आख़िरी रन देखें:

```bash
systemctl status roudix-autoupdate
journalctl -u roudix-autoupdate -n 20
```

किसी भी समय हाथ से अपडेट चलाने के लिए:

```fish
update
```

यह वही pull करता है (वही ब्रांच, fast-forward-only का वही नियम, वही लॉक — इसलिए यह चल रहे ऑटो-अपडेट से कभी नहीं टकराता), फिर रीबिल्ड करता है और आपके Flatpak अपडेट करता है। इसके विकल्पों के लिए [`update`](aliases.hi.md#update) देखें।

systemd के हार मान लेने से पहले बिल्ड में 2 घंटे तक लग सकते हैं। अगर रन बीच में मार दिया जाए या अचानक रुक जाए (टाइमआउट, क्रैश), तो सूचना भेजी जाती है; साधारण त्रुटि अपने आप सूचना देती है। ऑटो-अपडेट के बाद `update --changes` दिखाता है कि अगले बूट पर क्या लागू होगा।
