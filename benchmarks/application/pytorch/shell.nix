{ pkgs ? import <nixpkgs> { } }:
let
  python = pkgs.python3.withPackages (pypkgs: [
    pypkgs.torch
    pypkgs.torchvision
    pypkgs.pillow
  ]);
  mypython = pkgs.stdenv.mkDerivation rec {
    name = "python-pytorch";
    buildInputs = [ python ];
    buildCommand = ''
      mkdir -p $out/bin
      ln -s ${python.interpreter} $out/bin/${name}
    '';
  };
in
pkgs.mkShell {
  packages = [
    mypython
    pkgs.wget
    pkgs.unzip
    pkgs.just
    pkgs.git
    pkgs.numactl
  ];
}
