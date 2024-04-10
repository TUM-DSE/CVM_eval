{ pkgs }:

with pkgs;
OVMF.fd.overrideAttrs (old: {
  # src = fetchFromGitHub
  # {
  #   owner = "AMDESE";
  #   repo = "ovmf";
  #   rev = "80318fcdf1bccf5d503197825d62a157efd27c4b";
  #   sha256 = "sha256-L/X1uESu6m8a+8ir+E2HkxiazA9iyfcfeySxRJkt+2s=";
  #   fetchSubmodules = true;
  # };
  src = fetchFromGitHub {
    owner = "mmisono";
    repo = "edk2";
    rev = "80318fcdf1bccf5d503197825d62a157efd27c4b";
    sha256 = "sha256-L/X1uESu6m8a+8ir+E2HkxiazA9iyfcfeySxRJkt+2s=";
    fetchSubmodules = true;
  };
})
