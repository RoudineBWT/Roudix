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

# AMD Zen4 — Ryzen 7000/8000 desktop, 7040/8040 mobile, EPYC 9004/9005
ZEN4_MODEL_HINTS = (
    "ryzen 9 7", "ryzen 7 7", "ryzen 5 7", "ryzen 3 7",
    "ryzen 9 8", "ryzen 7 8", "ryzen 5 8", "ryzen 3 8",
    "ryzen threadripper 7", "epyc 9",
)

def detect_cpu_microarch():
    """
    Détermine la meilleure variante CachyOS selon le CPU :
        'zen4'  : AMD Zen4 (Ryzen 7000/8000, EPYC 9004/9005)
        'v4'    : CPU supportant AVX-512 (x86-64-v4)
        'v3'    : CPU supportant AVX2 (x86-64-v3) — fallback le plus courant
    On lit /proc/cpuinfo pour les flags et le modèle exact.
    """
    try:
        with open('/proc/cpuinfo', 'r') as f:
            content = f.read()
    except Exception:
        return 'v3'

    content_lower = content.lower()

    # Zen4 — basé sur le nom de modèle (le plus fiable pour ces gammes)
    if any(hint in content_lower for hint in ZEN4_MODEL_HINTS):
        return 'zen4'

    # x86-64-v4 nécessite AVX-512 (entre autres) — on vérifie les flags
    flags_line = next(
        (line for line in content.splitlines() if line.lower().startswith("flags")),
        ""
    )
    flags = set(flags_line.split(":")[-1].split()) if ":" in flags_line else set()

    v4_required = {"avx512f", "avx512bw", "avx512cd", "avx512dq", "avx512vl"}
    if v4_required.issubset(flags):
        return 'v4'

    # x86-64-v3 (AVX2) — fallback par défaut pour le matériel post-2013
    return 'v3'

# ── Templates local.nix ───────────────────────────────────────────────────────

local_nix_template = """{{ lib, ... }}:
{{
  # ── Desktop & shell ──────────────────────────────────────────────────────
  roudix.desktop.type  = "{desktop_type}";
  roudix.desktop.shell = "{desktop_shell}";
  roudix.shell          = "{shell_default}";

  # ── Hardware ─────────────────────────────────────────────────────────────
  hardware.myGpu        = "{gpu}";
  hardware.nvidiaLaptop = {nvidia_laptop};
  hardware.myCpu        = "{cpu}";
  hardware.myKernel     = "{kernel}";

  # ── Boot ─────────────────────────────────────────────────────────────────
  roudix.boot.bootloader = "{bootloader}";

  # ── Software ─────────────────────────────────────────────────────────────
  roudix.browsers     = [ {browsers} ];
  roudix.zen.enable   = {zen};
  roudix.rgb          = "{rgb}";
  roudix.mesa.useGit  = false;
  roudix.matrixClient = "{matrix_client}";

  # ── Locale ───────────────────────────────────────────────────────────────
  time.timeZone                   = "{timezone}";
  environment.sessionVariables.TZ = "{timezone}";
  i18n.defaultLocale              = "{locale}";
  console.keyMap                  = "{keymap}";

  # ── Modules optionnels ───────────────────────────────────────────────────
  roudix.gaming.enable          = {gaming};
  roudix.flatpak.enable         = {flatpak};
  roudix.fstrim.enable          = true;
  roudix.virtualization.enable  = {virtualization};
  roudix.vmGuest.enable         = {vm_guest};
  roudix.hosts.gtaFix.enable    = {gta_fix};
  roudix.autoupdate.enable      = {autoupdate};
  roudix.autoupdate.interval    = "{autoupdate_interval}";
  roudix.waydroid.enable        = {waydroid};
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
    cpu_microarch = detect_cpu_microarch()
    is_vm = (gpu == 'vm')
    if is_vm:
        gpu = 'intel'  # fallback pour les VMs

    libcalamares.utils.debug(
        f"Roudix: GPU détecté = {gpu}, CPU = {cpu}, microarch = {cpu_microarch}, VM = {is_vm}"
    )

    # ── Récupération des choix Calamares (instances packagechooser) ─────────
    # Chaque instance packagechooser stocke son choix dans globalstorage sous
    # la clé "packagechooser_<id>" (id défini dans settings.conf > instances).

    # GPU/CPU : le choix de l'utilisateur (pages packagechooser) prévaut sur
    # la détection automatique lspci/cpuinfo faite plus haut, qui sert de
    # valeur par défaut affichée mais peut être corrigée par l'utilisateur.
    gpu            = gs.value("packagechooser_gpu") or gpu
    nvidia_laptop  = gs.value("packagechooser_nvidialaptop") or "false"
    cpu            = gs.value("packagechooser_cpu") or cpu
    vm_choice      = gs.value("packagechooser_vmguest")
    is_vm          = (vm_choice == "true") if vm_choice is not None else is_vm

    desktop_type  = gs.value("packagechooser_desktop")  or "niri"
    desktop_shell = gs.value("packagechooser_shell")    or "noctalia"
    shell_default = gs.value("packagechooser_shelldefault") or "fish"
    gaming        = gs.value("packagechooser_gaming")   or "true"

    # Browser — si "brave" est choisi, la variante précise vient de
    # l'instance packagechooser_bravevariant (sinon ignorée).
    browser_choice = gs.value("packagechooser_browser") or "brave"
    if browser_choice == "brave":
        browser_choice = gs.value("packagechooser_bravevariant") or "brave"
    zen = gs.value("packagechooser_zen") or "false"
    browsers_nix = f'"{browser_choice}"' if browser_choice != "none" else ""

    rgb                 = "none"  # page RGB pas encore implémentée
    gta_fix             = gs.value("packagechooser_gtafix")         or "false"
    flatpak             = gs.value("packagechooser_flatpak")        or "false"
    virtualization      = gs.value("packagechooser_virtualization") or "false"
    autoupdate          = gs.value("packagechooser_autoupdate")     or "true"
    autoupdate_interval = gs.value("packagechooser_autoupdateinterval") or "1h"
    matrix_client       = gs.value("packagechooser_matrix")         or "none"
    waydroid            = gs.value("packagechooser_waydroid")       or "false"

    kernel     = gs.value("packagechooser_kernel")    or "cachyos-latest"
    bootloader = gs.value("packagechooser_bootloader") or "limine"

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

    # Backup hardware-configuration.nix générée par nixos-generate-config
    # avant que la copie du flake n'écrase /etc/nixos/
    hw_cfg_generated = os.path.join(nixos_dest, "hardware-configuration.nix")
    hw_backup = ""
    try:
        with open(hw_cfg_generated, "r") as f:
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

    # Écrire hardware-configuration.nix là où le flake l'attend :
    # hosts/roudix/hardware-configuration.nix (pas /etc/nixos/ racine)
    hw_cfg_dest = os.path.join(nixos_dest, "hosts/roudix/hardware-configuration.nix")
    try:
        libcalamares.utils.host_env_process_output(
            ["mkdir", "-p", os.path.dirname(hw_cfg_dest)], None
        )
        libcalamares.utils.host_env_process_output(
            ["cp", "/dev/stdin", hw_cfg_dest], None, hw_backup
        )
        subprocess.run(["sudo", "chmod", "644", hw_cfg_dest], check=True)
    except Exception as e:
        return ("Impossible d'écrire hardware-configuration.nix", str(e))

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
        desktop_type        = desktop_type,
        desktop_shell       = desktop_shell,
        shell_default       = shell_default,
        gpu                 = gpu,
        nvidia_laptop       = nvidia_laptop,
        cpu                 = cpu,
        kernel              = kernel,
        bootloader          = bootloader,
        browsers            = browsers_nix,
        zen                 = zen,
        rgb                 = rgb,
        matrix_client       = matrix_client,
        timezone            = timezone,
        locale              = locale,
        keymap              = keymap,
        gaming              = gaming,
        flatpak             = flatpak,
        virtualization      = virtualization,
        vm_guest            = "true" if is_vm else "false",
        gta_fix             = gta_fix,
        autoupdate          = autoupdate,
        autoupdate_interval = autoupdate_interval,
        waydroid            = waydroid,
    )
    local_nix_path = os.path.join(nixos_dest, "hosts/roudix/local.nix")
    libcalamares.utils.host_env_process_output(
        ["cp", "/dev/stdin", local_nix_path], None, local_nix_content
    )

    # home/local.nix
    home_local_path = os.path.join(nixos_dest, "home/local.nix")
    libcalamares.utils.host_env_process_output(
        ["cp", "/dev/stdin", home_local_path], None, home_local_nix.format()
    )

    # modules/system/boot.local.nix
    boot_local_path = os.path.join(nixos_dest, "modules/system/boot.local.nix")
    libcalamares.utils.host_env_process_output(
        ["cp", "/dev/stdin", boot_local_path], None, boot_local_nix.format()
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
