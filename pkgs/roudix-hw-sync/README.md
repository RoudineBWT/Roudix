<p align="center"><img src="roudix-hw-sync.svg" width="96" alt="Roudix Hardware Sync"></p>

# roudix-hw-sync

Changed PC, GPU or CPU? This re-detects your hardware and updates
`~/.config/roudix/hosts/<host>/local.nix` to match. Two ways to use it:

- **App**: *Roudix Hardware Sync* in the app menu (`roudix-hw-sync-gui`).
  It shows what it detected (you can correct it), previews the changes, then
  **Apply** (only edits `local.nix`) or **Apply & Rebuild** (also runs `nh os boot`, reboot after).
- **Terminal**: `roudix-hw-sync` (`-n` = preview only, nothing written).

## What it touches in `local.nix`

| Option | Rule |
|--------|------|
| `hardware.myCpu` | `amd` / `intel` from `/proc/cpuinfo` |
| `hardware.myGpu` | `nvidia` > `amd` > `intel` from PCI display devices; an existing `amd-igpu` / `amd-legacy` is kept |
| `hardware.nvidiaLaptop` | `true` only for NVIDIA + an Intel/AMD iGPU (Optimus) |
| `roudix.nvidia_config.*BusId` | filled (decimal `PCI:b:d:f`) on Optimus, `null` otherwise — only if the lines exist |
| `hardware.myKernel` / `myKernelChaotic` | the right one is uncommented (nvidia → Chaotic) — only if both lines exist |
| `roudix.undervolt.only-amd.enable` | forced to `false` on a non-AMD GPU, left alone on `amd` / `amd-legacy` |

Lines absent from your `local.nix` are never added. A `local.nix.bak` is written before each change.

## CLI options

`--gpu amd|amd-igpu|amd-legacy|nvidia|intel`, `--cpu amd|intel`, `--laptop true|false`
override the detection; `-f FILE` targets another file; `--detect` prints
`key=value` lines (used by the GUI). `ROUDIX_HOST` and `NH_FLAKE` are honoured like in the other Roudix apps.
