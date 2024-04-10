# taken from nixos-generators (but commended a bit)
{ config, lib, pkgs, modulesPath, ... }:
{
  # for virtio kernel drivers
  imports = [
    "${toString modulesPath}/profiles/qemu-guest.nix"
  ];

  fileSystems."/" = {
    device = "/dev/disk/by-label/nixos";
    autoResize = true;
    fsType = "ext4";
  };

  fileSystems."/share" = {
    device = "share";
    fsType = "9p";
    options = [ "trans=virtio" "nofail" "msize=104857600" ];
  };

  boot.growPartition = true;
  boot.kernelParams = [ "console=ttyS0" ];
  boot.loader.grub.device = "nodev"; # if (pkgs.stdenv.system == "x86_64-linux") then
    # (lib.mkDefault "/dev/vda")
  # else
   #  (lib.mkDefault "nodev");

  boot.loader.grub.efiSupport = true;
  boot.loader.grub.efiInstallAsRemovable = true;
  boot.loader.timeout = 0;
}

