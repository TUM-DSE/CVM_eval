{ pkgs }:

with pkgs;
qemu_full.overrideAttrs
(
  new: old:
  {
    src = fetchFromGitHub
    {
      owner = "AMDESE";
      repo = "qemu";
      rev = "94bec6ae7a81872ca0df2655dac18b2dea8c3090";
      sha256 = "inX1Di5vP4c14E7nuQG8KigAZ2WyGQdud7+K83R4rrg=";
      fetchSubmodules = true;
    };
  }
)
