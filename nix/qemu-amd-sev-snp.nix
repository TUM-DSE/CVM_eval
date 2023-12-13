{ pkgs }:

with pkgs;
qemu_full.overrideAttrs
(
  new: old:
  {
    src = builtins.fetchGit
    {
      url = "git@gitlab.lrz.de:robert/qemu.git";
      ref = "snp-latest";
      rev = "16109896d9a5f96de695ff7ebc8bbe9719c9901d";
      submodules = true;
    };
    configureFlags = old.configureFlags ++
    [
      "--enable-debug"
    ];
  }

)
