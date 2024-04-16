{ pkgs, ... }:
pkgs.stdenv.mkDerivation {
  name = "outb";

  src = ../../benchmarks/boottime/outb;

  buildPhase = ''
    $CC outb.c -o outb
  '';

  installPhase = ''
    mkdir -p $out/bin
    cp outb  $out/bin/outb
  '';
}

