{ pkgs ? import <nixpkgs> { } }:
let
  python = pkgs.python3.withPackages (pypkgs: [
    pypkgs.tensorflow
    pypkgs.keras
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
