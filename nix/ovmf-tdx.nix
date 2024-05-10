{ pkgs }:

with pkgs;
OVMF.fd.overrideAttrs (old: {
  src = fetchFromGitHub {
    owner = "tianocore";
    repo = "edk2-staging";
    # branch "TDVF"
    rev = "c229fca09ebc3ed300845e5346d59e196461c498";
    sha256 = "sha256-LqeGrdor6t3aH6HwEPgOqyyd6UsFRjU8EwwN1MHsreo=";
    fetchSubmodules = true;
  };
  patches = (old.patches or [ ]) ++ [
    # to record boot events
    ./patches/ovmf-event-record.patch
  ];
})
