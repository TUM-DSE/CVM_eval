{ lib, buildLinux, ... }@args:
let
  buildKernel = { url, ref ? "master", rev, version, modDirVersion, extraPatches ? [ ] }:
    buildLinux
      (args // rec
      {
        inherit version modDirVersion;
        src = builtins.fetchGit { inherit url ref rev; };

        extraConfig =
        ''
          CVM_IO y
        '';
        extraMeta.branch = version;
        ignoreConfigErrors = true;
        kernelPatches = [ ] ++ extraPatches;
      } // (args.argsOverride or { }));

  linux_gitlab_lrz = "git@gitlab.lrz.de:robert/linux.git";

  cvm_io_6_7_rc4 =
  {
    url = linux_gitlab_lrz;
    ref = "cvm-io-dev";
    rev = "7fba07434e21e79107785edaded9d389edaeb6a1";
    version = "6.7";
    modDirVersion = "6.7.0-rc4";
  };
in
buildKernel cvm_io_6_7_rc4
