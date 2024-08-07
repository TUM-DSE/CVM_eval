{ pkgs ? import <nixpkgs> { } }:

pkgs.mkShell {
  packages = with pkgs; [
    nodejs-slim_20
    (python3.withPackages (python-pkgs: with python-pkgs; [
      django
    ]))
    (ruby.withPackages (ruby-pkgs: with ruby-pkgs; [
      sinatra
    ]))
    primesieve
  ];
}
