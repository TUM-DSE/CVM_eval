{ pkgs }:

with pkgs;
OVMF.fd.overrideAttrs (old: {
  src = fetchFromGitHub {
    owner = "tianocore";
    repo = "edk2";
    # tag "edk2-stable202508
    rev = "d46aa46c8361194521391aa581593e556c707c6e";
    sha256 = "sha256-YZcjPGPkUQ9CeJS9JxdHBmpdHsAj7T0ifSZWZKyNPMk=";
    fetchSubmodules = true;
  };
  version = "202508";
  patches = (old.patches or [ ]) ++ [
    # to record boot events
    ./patches/ovmf-event-record.patch
  ];
  env.NIX_CFLAGS_COMPILE = "-Wno-return-type" + " -Wno-error=implicit-function-declaration";
})
