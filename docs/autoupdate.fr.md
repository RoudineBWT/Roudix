*[English version](autoupdate.md)*

# Mise à jour automatique

Quand `roudix.autoupdate.enable = true`, le système vérifie GitHub toutes les heures (et 5 min après le démarrage).
Si de nouveaux commits sont détectés sur la branche suivie (`main` par défaut), il fait un pull et lance `nh os boot path:...` — la nouvelle config s'applique au prochain redémarrage.
Vos fichiers `local.nix`, `username.nix`, `hardware-configuration.nix`, les fichiers optionnels `home/niri-custom.nix` / `home/umbriel-custom.nix` / `home/mango-custom.nix` et tout ce qui se trouve sous `dotfiles/perso/` sont ignorés par git et jamais touchés par le pull.

Pour configurer l'intervalle ou la branche, surchargez dans `local.nix` :

```nix
{ ... }:
{
  roudix.autoupdate.enable   = true;  # si vous mettez false ici, config.roudix.autoupdate prendra le relai pour mettre à jour mais sans git pull
  roudix.autoupdate.interval = "6h";   # vérifier toutes les 6 heures au lieu de 1h
  roudix.autoupdate.branch   = "main"; # branche à suivre : "main" (stable), "testing" ou "dev" — définie par l'installateur
}
```

La branche se choisit dans l'installateur (script et installateur graphique de l'ISO). Tu peux la changer plus tard depuis **Roudix Switcher → Système → Branche de mise à jour**, qui bascule aussi ton dépôt local `~/.config/roudix` sur cette branche avant la reconstruction.

Vérifier la dernière exécution :

```bash
systemctl status roudix-autoupdate
journalctl -u roudix-autoupdate -n 20
```

Pour déclencher une mise à jour manuellement à tout moment :

```fish
update
```
