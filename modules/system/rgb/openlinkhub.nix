{ config, pkgs, lib, inputs, ... }:

let
  openlinkhub-bin = inputs.roudix-caches.packages.x86_64-linux.openlinkhub;
  cfg = config.roudix.memory;
in {
  options.roudix.memory = {
    enable = lib.mkOption {
      type    = lib.types.bool;
      default = false;
      description = "Activer le contrôle RGB de la RAM via OpenLinkHub";
    };
    type = lib.mkOption {
      type    = lib.types.enum [ "ddr4" "ddr5" ];
      default = "ddr5";
      description = "Type de RAM : ddr4 ou ddr5";
    };
    smBus = lib.mkOption {
      type    = lib.types.str;
      default = "i2c-0";
      description = "Bus SMBus de la RAM (trouvé via i2cdetect -l)";
    };
    sku = lib.mkOption {
        type    = lib.types.str;
        default = "";
        description = "Part number exact de la RAM (ex: CMH64GX5M2B5200C40). Trouvé via: sudo dmidecode -t memory | grep 'Part Number'";
      };
  };

  config = lib.mkIf (config.roudix.rgb == "openlinkhub") {
    hardware.i2c.enable = true;
    environment.systemPackages = [ pkgs.i2c-tools ];

    # ── SMBus / RAM (conditionnel) ────────────────────────────────────────
    boot.kernelParams = lib.mkIf cfg.enable [ "acpi_enforce_resources=lax" ];

    # spd5118 = DDR5, ee1004 = DDR4
    boot.blacklistedKernelModules = lib.mkIf cfg.enable (
      if cfg.type == "ddr5" then [ "spd5118" ]
      else [ "ee1004" ]
    );

    services.udev.extraRules = ''
      SUBSYSTEM=="usb", ATTRS{idVendor}=="1b1c", MODE="0660", GROUP="openlinkhub"
    '' + lib.optionalString cfg.enable ''
      KERNEL=="i2c-[0-9]*", GROUP="openlinkhub", MODE="0660"
    '';

    users.groups.openlinkhub = {};

    systemd.services.openlinkhub = {
      description = "OpenLinkHub";
      wantedBy    = [ "multi-user.target" ];
      after       = [ "network.target" ];
      serviceConfig = {
        ExecStartPre     = "${openlinkhub-bin}/lib/systemd/openlinkhub-setup";
        ExecStart        = "${openlinkhub-bin}/bin/OpenLinkHub";
        Restart          = "on-failure";
        WorkingDirectory = "/var/lib/openlinkhub";
        StateDirectory   = "openlinkhub";
      };
    };

    system.activationScripts.openlinkhubMemory = lib.mkIf cfg.enable {
      deps = [ "var" ];
      text = ''
        CONFIG=/var/lib/openlinkhub/config.json
        if [ -f "$CONFIG" ]; then
          ${pkgs.jq}/bin/jq \
            --arg sku "${cfg.sku}" \
            --argjson type ${if cfg.type == "ddr5" then "5" else "4"} \
            '.memory = true | .memorySmBus = "${cfg.smBus}" | .memoryType = $type | .decodeMemorySku = false | .memorySku = $sku' \
            "$CONFIG" > "$CONFIG.tmp" && mv "$CONFIG.tmp" "$CONFIG"
        fi
      '';
    };
  };
}
