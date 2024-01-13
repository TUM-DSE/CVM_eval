{ pkgs }:
pkgs.stdenv.mkDerivation {
    name = "vm-benchmarks";

    src = ./.;

    buildPhase = ''
      $CC cpuid.c -o bm-cpuid
      $CC msr_user.c -o bm-msr-usr
      $CC intel_hypercall.c -o bm-intel-hypercall
    '';

    installPhase = ''
      mkdir -p $out/bin
      cp bm-cpuid $out/bin/bm-cpuid
      cp bm-msr-usr $out/bin/bm-msr-usr
      cp bm-intel-hypercall $out/bin/bm-intel-hypercall
      cp cpuid.sh $out/bin/bm-cpuid.sh
    '';
  }

