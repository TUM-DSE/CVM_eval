{ pkgs }:

with pkgs;
OVMF.fd.overrideAttrs (old: {
  src = fetchFromGitHub {
    owner = "gierens";
    repo = "edk2-staging";
    # branch "tdvf-upddate-subhook"
    rev = "97a91317bd5a16ee418307c3bef13c66addfc42d";
    sha256 = "sha256-InJjSqggLhVJnY17RqxapXWqNcvnk7tR2HP2bPdv2Ec=";
    fetchSubmodules = true;
  };
  patches = (old.patches or [ ]) ++ [
    # to record boot events
    ./patches/ovmf-event-record.patch
  ];
  env.NIX_CFLAGS_COMPILE = "-Wno-return-type" + " -Wno-error=implicit-function-declaration";
})
