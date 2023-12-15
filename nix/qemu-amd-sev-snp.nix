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
      rev = "fe4c9e8e7e7ddac4b19c4366c1f105ffc4a78482";
      submodules = true;
    };
    configureFlags = old.configureFlags ++
    [
      "--enable-debug"
    ];
  }

)
