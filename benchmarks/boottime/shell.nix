{ pkgs ? import <nixpkgs> { } }:
with pkgs;
pkgs.mkShell {
  buildInputs = [
    pylyzer
    python311
    python311Packages.numpy
    python311Packages.tqdm
    python311Packages.python-lsp-server
    python311Packages.matplotlib
  ];
}

