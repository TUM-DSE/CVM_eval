{ pkgs, lib }:

import (pkgs.path + "/nixos/lib/make-disk-image.nix") {
  config = (import (pkgs.path + "/nixos/lib/eval-config.nix") {
    inherit (pkgs) system;
    modules = [{
      imports = [ ./modules/configuration.nix ];
    }];
  }).config;
  inherit pkgs;
  inherit (pkgs) lib;
  diskSize = 32768;
  format = "qcow2";
  partitionTableType = "efi";
  installBootLoader = true;
  OVMF = pkgs.OVMF.fd;
  touchEFIVars = true;
}
