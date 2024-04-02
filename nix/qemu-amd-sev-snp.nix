{ pkgs }:

with pkgs;
qemu_full.overrideAttrs
(
  new: old:
  {
    # src = builtins.fetchGit
    # {
    #   # url = "git@gitlab.lrz.de:robert/qemu.git";
    #   # ref = "snp-latest";
    #   rev = "fe4c9e8e7e7ddac4b19c4366c1f105ffc4a78482";
    #   submodules = true;
    # };
    src = fetchFromGitHub
    {
      owner = "mmisono";
      repo = "qemu";
      # branch: snp-latest-20231110
      rev = "fe4c9e8e7e7ddac4b19c4366c1f105ffc4a78482";
      sha256 = "sha256-51BEYF7P5GteCrWOp7nKPjUDxXFq8KDxMAC5f5TNO2I=";
      fetchSubmodules = true;
    };
    configureFlags = old.configureFlags ++
    [
      # "--enable-debug"
      # requires libblkio build
      # "--enable-blkio"
      # too new for current version?
      # "--enable-download"
    ];
  }

)
