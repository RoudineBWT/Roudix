"""
Renders the roudix.* option block that gets dropped into the target
system's configuration.nix (or host flake module). This is the direct
port of the config-writing half of roudix-installer.sh — same option
names, same shape, just fed by GUI state instead of `read -p`.
"""
from roudix_installer.state import InstallState


def _nix_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    return f'"{v}"'


def generate(state: InstallState) -> str:
    opts = state.as_nix_options()
    lines = ["{ config, pkgs, ... }:", "", "{"]
    for key, value in opts.items():
        lines.append(f"  {key} = {_nix_value(value)};")
    lines.append("")
    lines.append(f"  users.users.{state.username} = {{")
    lines.append("    isNormalUser = true;")
    lines.append('    extraGroups = [ "wheel" "networkmanager" "video" "audio" ];')
    if state.password_hash:
        lines.append(f'    hashedPassword = "{state.password_hash}";')
    lines.append("  };")
    lines.append("}")
    return "\n".join(lines) + "\n"
