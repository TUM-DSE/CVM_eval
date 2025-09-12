{ buildFHSEnv
, lib
, getopt
, elfutils
, ncurses
, openssl
, zlib
, flex
, bison
, binutils
, gcc
, gnumake
, bc
, perl
, hostname
, cpio
, pkg-config
, pahole
, inotify-tools
, cloc
, tokei
, newt
, slang
, libtraceevent
, libunwind
, numactl
, python3
, babeltrace
, runScript ? ''bash -c''
}:
buildFHSEnv {
  name = "linux-kernel-build";
  targetPkgs = pkgs: ([
    getopt
    flex
    bison
    binutils
    gcc
    gnumake
    bc
    perl
    hostname
    cpio
    pkg-config
    pahole # BTF
    inotify-tools
    cloc
    tokei
  ] ++ map lib.getDev [
    elfutils
    ncurses
    openssl
    zlib
    newt
    slang
    libtraceevent
    libunwind
    numactl
    python3
    perl
    babeltrace
  ]);
  hardeningDisable = [ "all" ];
  profile = ''
    export hardeningDisable=all
  '';

  inherit runScript;
}
