{ pkgs }:

with pkgs;
OVMF.fd.overrideAttrs (old: {
  src = fetchFromGitHub {
    owner = "AMDESE";
    repo = "ovmf";
    # branch "snp-latest"
    rev = "fbe0805b2091393406952e84724188f8c1941837";
    sha256 = "sha256-iobC0CeWSylS9sLuXOqAmL36hl/tY+IedT/I3xQ80Ag=";
    fetchSubmodules = true;
  };
  patches = (old.patches or [ ]) ++ [
    # to record boot events
    ./patches/ovmf-event-record.patch
  ];
  env.NIX_CFLAGS_COMPILE = "-Wno-return-type" + " -Wno-error=implicit-function-declaration";
})
