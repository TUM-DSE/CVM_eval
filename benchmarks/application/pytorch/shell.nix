{ pkgs ? import <nixpkgs> { } }:
let
  python = pkgs.python3.withPackages (pypkgs: [
    pypkgs.torch
    pypkgs.torchvision
    pypkgs.pillow
  ]);
in
pkgs.mkShell {
  packages = [
    python
    pkgs.wget
    pkgs.unzip
    pkgs.just
    pkgs.git
    pkgs.numactl
  ];
}
