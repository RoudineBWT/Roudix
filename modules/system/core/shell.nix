{lib, ...}:
{
options.roudix.shell = lib.mkOption {
  type = lib.types.enum [ "fish" "bash" ];
  default = "fish";
 };
}
