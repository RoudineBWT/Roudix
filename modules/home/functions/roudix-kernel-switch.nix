{ ... }: {
  fish = ''
    set kernel $argv[1]
    set config_file "$NH_FLAKE/hosts/roudix/local.nix"
    set gpu (grep -oP 'hardware\.myGpu\s*=\s*"\K[^"]+' $config_file 2>/dev/null)

    if test "$gpu" = "nvidia"
      set key "myKernelChaotic"
    else
      set key "myKernel"
    end

    if test -z "$kernel"
      echo "Usage: roudix-kernel-switch [variant]"
      echo ""
      if test "$key" = "myKernelChaotic"
        echo "GPU: nvidia — variants come from Chaotic-Nyx (hardware.myKernelChaotic)"
        echo "  ── Chaotic-Nyx ─────────────────────────────────────────────"
        echo "  cachyos                    Default — LTO + BORE, ships nvidia_cachyos"
        echo "  cachyos-lts                Long-term support"
        echo "  cachyos-server             Server optimized — no desktop tuning"
        echo "  cachyos-hardened           Security hardened"
        echo "  ── Zen (nixpkgs) ───────────────────────────────────────────"
        echo "  zen                        linux-zen — nvidia module cached only with the open driver"
      else
        echo "GPU: non-nvidia — variants come from xddxdd (hardware.myKernel)"
        echo "  ── Latest ──────────────────────────────────────────────────"
        echo "  cachyos-latest             Standard latest"
        echo "  cachyos-latest-v3          x86_64-v3 (recommended modern CPUs)"
        echo "  cachyos-latest-v4          x86_64-v4 (AVX-512)"
        echo "  cachyos-latest-zen4        AMD Zen 4"
        echo "  cachyos-latest-lto         LTO"
        echo "  cachyos-latest-lto-v3      LTO + v3 (best perf, modern CPUs)"
        echo "  cachyos-latest-lto-v4      LTO + v4"
        echo "  cachyos-latest-lto-zen4    LTO + Zen 4"
        echo "  ── LTS ─────────────────────────────────────────────────────"
        echo "  cachyos-lts                Long-term support"
        echo "  cachyos-lts-v3             LTS + v3"
        echo "  cachyos-lts-v4             LTS + v4"
        echo "  cachyos-lts-zen4           LTS + Zen 4"
        echo "  cachyos-lts-lto            LTS + LTO"
        echo "  cachyos-lts-lto-v3         LTS + LTO + v3 (stable + perf)"
        echo "  cachyos-lts-lto-v4         LTS + LTO + v4"
        echo "  cachyos-lts-lto-zen4       LTS + LTO + Zen 4"
        echo "  ── Variants ────────────────────────────────────────────────"
        echo "  cachyos-bore               BORE scheduler"
        echo "  cachyos-bore-lto           BORE + LTO"
        echo "  cachyos-bmq                BMQ scheduler"
        echo "  cachyos-bmq-lto            BMQ + LTO"
        echo "  cachyos-eevdf              EEVDF scheduler"
        echo "  cachyos-eevdf-lto          EEVDF + LTO"
        echo "  cachyos-hardened           Security hardened"
        echo "  cachyos-hardened-lto       Hardened + LTO"
        echo "  cachyos-rt-bore            Real-time + BORE"
        echo "  cachyos-rt-bore-lto        Real-time + BORE + LTO"
        echo "  cachyos-deckify            Steam Deck optimized"
        echo "  cachyos-deckify-lto        Steam Deck + LTO"
        echo "  cachyos-server             Server optimized"
        echo "  cachyos-server-lto         Server + LTO"
        echo "  cachyos-rc                 Release candidate (unstable)"
        echo "  cachyos-rc-lto             RC + LTO"
        echo "  ── Zen (nixpkgs) ───────────────────────────────────────────"
        echo "  zen                        linux-zen, cached on cache.nixos.org"
      end
      return 1
    end

    if test "$key" = "myKernelChaotic"
      set valid cachyos cachyos-lts cachyos-server cachyos-hardened zen
    else
      set valid \
        cachyos-latest cachyos-latest-v2 cachyos-latest-v3 cachyos-latest-v4 cachyos-latest-zen4 \
        cachyos-latest-lto cachyos-latest-lto-v2 cachyos-latest-lto-v3 cachyos-latest-lto-v4 cachyos-latest-lto-zen4 \
        cachyos-lts cachyos-lts-v2 cachyos-lts-v3 cachyos-lts-v4 cachyos-lts-zen4 \
        cachyos-lts-lto cachyos-lts-lto-v2 cachyos-lts-lto-v3 cachyos-lts-lto-v4 cachyos-lts-lto-zen4 \
        cachyos-bmq cachyos-bmq-lto cachyos-bore cachyos-bore-lto \
        cachyos-deckify cachyos-deckify-lto cachyos-eevdf cachyos-eevdf-lto \
        cachyos-hardened cachyos-hardened-lto cachyos-rc cachyos-rc-lto \
        cachyos-rt-bore cachyos-rt-bore-lto cachyos-server cachyos-server-lto \
        zen
    end

    if not contains $kernel $valid
      echo "Unknown kernel variant: $kernel"
      echo "Run roudix-kernel-switch without arguments to see all variants."
      return 1
    end

    echo "Switching kernel to: $kernel (hardware.$key)"
    sed -i "s/hardware\.$key = \"[^\"]*\"/hardware.$key = \"$kernel\"/" $config_file

    echo "Rebuilding configuration (boot)..."
    nh os boot --accept-flake-config path:$NH_FLAKE

    echo "Done — reboot to apply the new kernel."
  '';

  bash = ''
    roudix-kernel-switch() {
      local kernel="$1"
      local config_file="$NH_FLAKE/hosts/roudix/local.nix"
      local gpu key
      gpu=$(grep -oP 'hardware\.myGpu\s*=\s*"\K[^"]+' "$config_file" 2>/dev/null)
      key="myKernel"
      [[ "$gpu" == "nvidia" ]] && key="myKernelChaotic"

      if [[ -z "$kernel" ]]; then
        echo "Usage: roudix-kernel-switch [variant]"
        echo ""
        if [[ "$key" == "myKernelChaotic" ]]; then
          echo "GPU: nvidia — variants come from Chaotic-Nyx (hardware.myKernelChaotic)"
          echo "  ── Chaotic-Nyx ─────────────────────────────────────────────"
          echo "  cachyos                    Default — LTO + BORE, ships nvidia_cachyos"
          echo "  cachyos-lts                Long-term support"
          echo "  cachyos-server             Server optimized — no desktop tuning"
          echo "  cachyos-hardened           Security hardened"
          echo "  ── Zen (nixpkgs) ───────────────────────────────────────────"
          echo "  zen                        linux-zen — nvidia module cached only with the open driver"
        else
          echo "GPU: non-nvidia — variants come from xddxdd (hardware.myKernel)"
          echo "  ── Latest ──────────────────────────────────────────────────"
          echo "  cachyos-latest             Standard latest"
          echo "  cachyos-latest-v3          x86_64-v3 (recommended modern CPUs)"
          echo "  cachyos-latest-v4          x86_64-v4 (AVX-512)"
          echo "  cachyos-latest-zen4        AMD Zen 4"
          echo "  cachyos-latest-lto         LTO"
          echo "  cachyos-latest-lto-v3      LTO + v3 (best perf, modern CPUs)"
          echo "  cachyos-latest-lto-v4      LTO + v4"
          echo "  cachyos-latest-lto-zen4    LTO + Zen 4"
          echo "  ── LTS ─────────────────────────────────────────────────────"
          echo "  cachyos-lts                Long-term support"
          echo "  cachyos-lts-v3             LTS + v3"
          echo "  cachyos-lts-v4             LTS + v4"
          echo "  cachyos-lts-zen4           LTS + Zen 4"
          echo "  cachyos-lts-lto            LTS + LTO"
          echo "  cachyos-lts-lto-v3         LTS + LTO + v3 (stable + perf)"
          echo "  cachyos-lts-lto-v4         LTS + LTO + v4"
          echo "  cachyos-lts-lto-zen4       LTS + LTO + Zen 4"
          echo "  ── Variants ────────────────────────────────────────────────"
          echo "  cachyos-bore               BORE scheduler"
          echo "  cachyos-bore-lto           BORE + LTO"
          echo "  cachyos-bmq                BMQ scheduler"
          echo "  cachyos-bmq-lto            BMQ + LTO"
          echo "  cachyos-eevdf              EEVDF scheduler"
          echo "  cachyos-eevdf-lto          EEVDF + LTO"
          echo "  cachyos-hardened           Security hardened"
          echo "  cachyos-hardened-lto       Hardened + LTO"
          echo "  cachyos-rt-bore            Real-time + BORE"
          echo "  cachyos-rt-bore-lto        Real-time + BORE + LTO"
          echo "  cachyos-deckify            Steam Deck optimized"
          echo "  cachyos-deckify-lto        Steam Deck + LTO"
          echo "  cachyos-server             Server optimized"
          echo "  cachyos-server-lto         Server + LTO"
          echo "  cachyos-rc                 Release candidate (unstable)"
          echo "  cachyos-rc-lto             RC + LTO"
          echo "  ── Zen (nixpkgs) ───────────────────────────────────────────"
          echo "  zen                        linux-zen, cached on cache.nixos.org"
        fi
        return 1
      fi

      if [[ "$key" == "myKernelChaotic" ]]; then
        case "$kernel" in
          cachyos|cachyos-lts|cachyos-server|cachyos-hardened|zen) ;;
          *)
            echo "Unknown kernel variant: $kernel"
            echo "Run roudix-kernel-switch without arguments to see all variants."
            return 1
            ;;
        esac
      else
        case "$kernel" in
          cachyos-latest|cachyos-latest-v2|cachyos-latest-v3|cachyos-latest-v4|cachyos-latest-zen4|\
          cachyos-latest-lto|cachyos-latest-lto-v2|cachyos-latest-lto-v3|cachyos-latest-lto-v4|cachyos-latest-lto-zen4|\
          cachyos-lts|cachyos-lts-v2|cachyos-lts-v3|cachyos-lts-v4|cachyos-lts-zen4|\
          cachyos-lts-lto|cachyos-lts-lto-v2|cachyos-lts-lto-v3|cachyos-lts-lto-v4|cachyos-lts-lto-zen4|\
          cachyos-bmq|cachyos-bmq-lto|cachyos-bore|cachyos-bore-lto|\
          cachyos-deckify|cachyos-deckify-lto|cachyos-eevdf|cachyos-eevdf-lto|\
          cachyos-hardened|cachyos-hardened-lto|cachyos-rc|cachyos-rc-lto|\
          cachyos-rt-bore|cachyos-rt-bore-lto|cachyos-server|cachyos-server-lto|\
          zen) ;;
          *)
            echo "Unknown kernel variant: $kernel"
            echo "Run roudix-kernel-switch without arguments to see all variants."
            return 1
            ;;
        esac
      fi

      echo "Switching kernel to: $kernel (hardware.$key)"
      sed -i "s/hardware\.$key = \"[^\"]*\"/hardware.$key = \"$kernel\"/" "$config_file"

      echo "Rebuilding configuration (boot)..."
      nh os boot --accept-flake-config path:"$NH_FLAKE"

      echo "Done — reboot to apply the new kernel."
    }
  '';
}
