#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Roudix Calamares installer module
#   Adapted from GLF-OS nixos.py
#   SPDX-License-Identifier: GPL-3.0-or-later

import libcalamares
import os
import subprocess
import re

import gettext

_ = gettext.translation(
    "calamares-python",
    localedir=libcalamares.utils.gettext_path(),
    languages=libcalamares.utils.gettext_languages(),
    fallback=True,
).gettext

# ── Helpers ───────────────────────────────────────────────────────────────────

def pretty_name():
    return _("Installing Roudix.")

status = pretty_name()

def pretty_status_message():
    return status

def catenate(d, key, *values):
    if [v for v in values if v is None]:
        return
    d[key] = "".join(values)

# ── GPU detection (repris de GLF-OS, adapté pour les modules Roudix) ─────────

def get_vga_devices():
    result = subprocess.run(['lspci'], stdout=subprocess.PIPE, text=True)
    lines = result.stdout.strip().splitlines()
    vga_devices = []
    keywords = [' VGA compatible controller: ', ' 3D controller: ']
    for line in lines:
        for k in keywords:
            if k in line:
                address, description = line.split(k, 1)
                vga_devices.append((address.strip(), description.strip()))
                break
    return vga_devices

def detect_gpu(vga_devices):
    """Retourne 'amd', 'nvidia', 'intel' ou 'vm'"""
    for _, desc in vga_devices:
        d = desc.lower()
        if any(k in d for k in ['qxl', 'virtio', 'vmware', 'bochs', 'virtualbox']):
            return 'vm'
    for _, desc in vga_devices:
        d = desc.lower()
        if 'nvidia' in d:
            return 'nvidia'
    for _, desc in vga_devices:
        d = desc.lower()
        if 'amd' in d or 'ati ' in d:
            return 'amd'
    return 'intel'

def detect_cpu():
    """Retourne 'intel' ou 'amd'"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            content = f.read().lower()
        if 'amd' in content:
            return 'amd'
    except Exception:
        pass
    return 'intel'

# ── Templates local.nix ───────────────────────────────────────────────────────

local_nix_template = """{{ lib, ... }}:
{{
  # ── Desktop & shell ──────────────────────────────────────────────────────
  roudix.desktop.type  = "{desktop_type}";
  roudix.desktop.shell = "{desktop_shell}";

  # ── Hardware ─────────────────────────────────────────────────────────────
  hardware.myGpu    = "{gpu}";
  hardware.myCpu    = "{cpu}";
  hardware.myKernel = "{kernel}";

  # ── Boot ─────────────────────────────────────────────────────────────────
  roudix.boot.bootloader = "{bootloader}";

  # ── Software ─────────────────────────────────────────────────────────────
  roudix.browsers     = [ {browsers} ];
  roudix.zen.enable   = false;
  roudix.rgb          = "none";
  roudix.mesa.useGit  = false;
  roudix.matrixClient = "none";

  # ── Locale ───────────────────────────────────────────────────────────────
  time.timeZone                   = "{timezone}";
  environment.sessionVariables.TZ = "{timezone}";
  i18n.defaultLocale              = "{locale}";
  console.keyMap                  = "{keymap}";

  # ── Modules optionnels ───────────────────────────────────────────────────
  roudix.gaming.enable      = true;
  roudix.flatpak.enable     = true;
  roudix.fstrim.enable      = true;
  roudix.virtualization.enable = false;
  roudix.vmGuest.enable     = {vm_guest};
}}
"""

home_local_nix = """{{ pkgs, lib, osConfig, ... }}:
{{
  # Personnalisation home-manager — ajoutez vos packages ici après l'install
  # home.packages = with pkgs; [ vlc telegram-desktop ];
}}
"""

boot_local_nix = """{{
  extraEntries = "";
}}
"""

username_nix_template = '"{username}"'

# ── Run ───────────────────────────────────────────────────────────────────────

def run():
    global status

    status = _("Détection du matériel")
    libcalamares.job.setprogress(0.05)

    gs = libcalamares.globalstorage
    root_mount_point = gs.value("rootMountPoint")

    # ── Détection GPU / CPU ──────────────────────────────────────────────────
    vga_devices = get_vga_devices()
    gpu = detect_gpu(vga_devices)
    cpu = detect_cpu()
    is_vm = (gpu == 'vm')
    if is_vm:
        gpu = 'intel'  # fallback pour les VMs

    libcalamares.utils.debug(f"Roudix: GPU détecté = {gpu}, CPU = {cpu}, VM = {is_vm}")

    # ── Récupération des choix Calamares ────────────────────────────────────
    desktop_type  = gs.value("packagechooser_desktop") or "niri"
    desktop_shell = gs.value("packagechooser_shell")   or "noctalia"
    kernel        = gs.value("packagechooser_kernel")  or "cachyos-lts-lto-v3"
    browser_raw   = gs.value("packagechooser_browser") or "helium"
    # Calamares renvoie une string — on la transforme en liste Nix
    browsers_nix  = " ".join([f'"{b}"' for b in browser_raw.split()])

    # Bootloader selon firmware
    fw_type    = gs.value("firmwareType")
    bootloader = "limine" if fw_type == "efi" else "limine"  # Roudix supporte les deux

    # Timezone
    region   = gs.value("locationRegion") or "Europe"
    zone     = gs.value("locationZone")   or "Brussels"
    timezone = f"{region}/{zone}"

    # Locale
    locale_conf = gs.value("localeConf") or {}
    locale = locale_conf.get("LANG", "en_US.UTF-8").split("/")[0]
    locale = locale.replace(".utf8", ".UTF-8").replace(".UTF8", ".UTF-8")

    # Clavier
    kb_layout  = gs.value("keyboardLayout")  or "be"
    kb_variant = gs.value("keyboardVariant") or ""
    # Convertir layout XKB → console keymap (approximatif)
    keymap_map = {
        "be": "be-latin1",
        "fr": "fr",
        "us": "us",
        "de": "de",
        "uk": "uk",
        "es": "es",
        "nl": "nl",
    }
    keymap = keymap_map.get(kb_layout, kb_layout)

    # Username
    username = gs.value("username") or "user"
    fullname = gs.value("fullname") or username

    # ── Génération hardware-configuration.nix ────────────────────────────────
    status = _("Génération de la configuration matérielle")
    libcalamares.job.setprogress(0.15)

    try:
        subprocess.check_output(
            ["pkexec", "nixos-generate-config", "--root", root_mount_point],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        return (_("nixos-generate-config a échoué"), _(e.output.decode("utf8")))

    # ── Copie du flake Roudix ────────────────────────────────────────────────
    status = _("Copie de la configuration Roudix")
    libcalamares.job.setprogress(0.20)

    iso_cfg_src = "/iso/iso-cfg"
    nixos_dest  = os.path.join(root_mount_point, "etc/nixos")

    # Backup hardware-configuration.nix avant écrasement
    hw_cfg_dest = os.path.join(nixos_dest, "hardware-configuration.nix")
    hw_backup = ""
    try:
        with open(hw_cfg_dest, "r") as f:
            hw_backup = f.read()
    except Exception as e:
        return ("Impossible de lire hardware-configuration.nix", str(e))

    # Copie récursive du flake Roudix
    try:
        subprocess.run(
            ["sudo", "cp", "-r", iso_cfg_src + "/.", nixos_dest + "/"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        return ("Échec de la copie du flake Roudix", str(e))

    # Restaurer hardware-configuration.nix (la copie l'a peut-être écrasé)
    try:
        libcalamares.utils.host_env_process_output(
            ["cp", "/dev/stdin", hw_cfg_dest], None, hw_backup
        )
        subprocess.run(["sudo", "chmod", "644", hw_cfg_dest], check=True)
    except Exception as e:
        libcalamares.utils.warning(f"Impossible de restaurer hardware-configuration.nix: {e}")

    # ── Génération des fichiers gitignorés ───────────────────────────────────
    status = _("Génération de la configuration personnalisée")
    libcalamares.job.setprogress(0.25)

    # username.nix
    username_nix_path = os.path.join(nixos_dest, "hosts/roudix/username.nix")
    libcalamares.utils.host_env_process_output(
        ["cp", "/dev/stdin", username_nix_path],
        None,
        username_nix_template.format(username=username)
    )

    # hosts/roudix/local.nix
    local_nix_content = local_nix_template.format(
        desktop_type  = desktop_type,
        desktop_shell = desktop_shell,
        gpu           = gpu,
        cpu           = cpu,
        kernel        = kernel,
        bootloader    = bootloader,
        browsers      = browsers_nix,
        timezone      = timezone,
        locale        = locale,
        keymap        = keymap,
        vm_guest      = "true" if is_vm else "false",
    )
    local_nix_path = os.path.join(nixos_dest, "hosts/roudix/local.nix")
    libcalamares.utils.host_env_process_output(
        ["cp", "/dev/stdin", local_nix_path], None, local_nix_content
    )

    # home/local.nix
    home_local_path = os.path.join(nixos_dest, "home/local.nix")
    libcalamares.utils.host_env_process_output(
        ["cp", "/dev/stdin", home_local_path], None, home_local_nix
    )

    # modules/system/boot.local.nix
    boot_local_path = os.path.join(nixos_dest, "modules/system/boot.local.nix")
    libcalamares.utils.host_env_process_output(
        ["cp", "/dev/stdin", boot_local_path], None, boot_local_nix
    )

    # ── Mot de passe root ────────────────────────────────────────────────────
    # nixos-install --no-root-passwd — le mot de passe user est géré par
    # le module users de Calamares après l'install

    # ── Sécurisation des dossiers Nix ────────────────────────────────────────
    status = _("Préparation de l'installation")
    libcalamares.job.setprogress(0.28)

    for nix_dir in [
        os.path.join(root_mount_point, "nix"),
        os.path.join(root_mount_point, "nix/var"),
        os.path.join(root_mount_point, "nix/var/nix"),
        os.path.join(root_mount_point, "nix/var/nix/builds"),
    ]:
        try:
            libcalamares.utils.host_env_process_output(["mkdir", "-p", nix_dir], None)
            libcalamares.utils.host_env_process_output(["chmod", "0755", nix_dir], None)
            libcalamares.utils.host_env_process_output(["chown", "root:root", nix_dir], None)
        except Exception as e:
            libcalamares.utils.warning(f"Permissions {nix_dir}: {e}")

    # ── nixos-install ────────────────────────────────────────────────────────
    status = _("Installation de Roudix (peut prendre du temps...)")
    libcalamares.job.setprogress(0.30)

    secure_tmpdir = os.path.join(root_mount_point, "var/tmp/nix-installer")
    try:
        libcalamares.utils.host_env_process_output(["mkdir", "-p", secure_tmpdir], None)
        libcalamares.utils.host_env_process_output(["chmod", "0700", secure_tmpdir], None)
    except Exception:
        pass

    install_cmd = [
        "pkexec",
        "nixos-install",
        "--no-root-passwd",
        "--option", "sandbox", "false",
        "--option", "build-users-group", "",
        "--flake", f"{nixos_dest}#roudix",
        "--root", root_mount_point,
    ]

    install_env = os.environ.copy()
    install_env['TMPDIR'] = secure_tmpdir

    try:
        output = ""
        proc = subprocess.Popen(
            install_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=install_env,
        )
        while True:
            line = proc.stdout.readline().decode("utf-8")
            output += line
            libcalamares.utils.debug(f"nixos-install: {line.strip()}")
            if not line:
                break
        if proc.wait() != 0:
            return (_("nixos-install a échoué"), _(output))
    except Exception:
        return (_("nixos-install a échoué"), _("L'installation n'a pas pu se terminer."))

    # ── XDG user dirs ────────────────────────────────────────────────────────
    status = _("Création des dossiers utilisateur")
    libcalamares.job.setprogress(0.95)
    try:
        subprocess.run(
            ["sudo", "chroot", root_mount_point,
             "su", "-", username, "-c", "xdg-user-dirs-update"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        libcalamares.utils.warning(f"xdg-user-dirs-update: {e}")

    # ── Copie du flake dans ~/.config/roudix (pour NH_FLAKE) ─────────────────
    # common.nix définit NH_FLAKE = "/home/<user>/.config/roudix"
    # donc nh os switch ne fonctionnera qu'une fois le flake là.
    status = _("Configuration de l'environnement utilisateur")
    libcalamares.job.setprogress(0.97)
    try:
        config_dir = os.path.join(root_mount_point, f"home/{username}/.config/roudix")
        libcalamares.utils.host_env_process_output(["mkdir", "-p", config_dir], None)
        subprocess.run(
            ["sudo", "cp", "-r", "/iso/iso-cfg/.", config_dir + "/"],
            check=True
        )
        # Trouver l'UID de l'utilisateur dans le système installé
        try:
            import pwd
            uid = pwd.getpwnam(username).pw_uid if username in [p.pw_name for p in pwd.getpwall()] else 1000
        except Exception:
            uid = 1000
        subprocess.run(
            ["sudo", "chown", "-R", f"{uid}:{uid}", config_dir],
            check=True
        )
        libcalamares.utils.debug(f"Flake Roudix copié dans {config_dir}")
    except Exception as e:
        # Non bloquant — l'utilisateur pourra cloner le repo manuellement
        libcalamares.utils.warning(f"Impossible de copier le flake dans ~/.config/roudix: {e}")

    libcalamares.job.setprogress(1.0)
    return None
