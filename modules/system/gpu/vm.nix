{ config, lib, ... }:

lib.mkIf (config.hardware.myGpu == "vm") {
  hardware.graphics.enable = true;
  hardware.graphics.enable32Bit = true;
  # virtio-gpu / QXL / VMware SVGA — no vendor-specific drivers needed
}
