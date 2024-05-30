{ pkgs ? import <nixpkgs> { } }:
pkgs.mkShell {
  packages = [
    pkgs.blender
    pkgs.wget
    pkgs.unzip
    pkgs.just
    pkgs.git
    pkgs.numactl
  ];
}
