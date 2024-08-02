{ pkgs }:

with pkgs;
OVMF.fd.overrideAttrs (old: {
  # use fetchFromGitHub to specify the exact commit
  ## src = fetchFromGitHub
  ## {
  ##   owner = "AMDESE";
  ##   repo = "ovmf";
  ##   rev = "80318fcdf1bccf5d503197825d62a157efd27c4b";
  ##   sha256 = "sha256-L/X1uESu6m8a+8ir+E2HkxiazA9iyfcfeySxRJkt+2s=";
  ##   fetchSubmodules = true;
  ## };
  # we use a forked version as sometimes AMDESE's version is foce-pushed and
  # it's hard to track the changes in that case
  src = fetchFromGitHub {
    owner = "tianocore";
    repo = "edk2";
    # branch edk2-stable202302
    rev = "f80f052277c88a67c55e107b550f504eeea947d3";
    sha256 = "sha256-KZ5bTdaStO2M1hLPx9LsUSMl9NEiZeYMmFiShxCJqJM=";
    fetchSubmodules = true;
  };
  patches = (old.patches or [ ]) ++ [
    # to record boot events
    ./patches/ovmf-event-record.patch
  ];
})
