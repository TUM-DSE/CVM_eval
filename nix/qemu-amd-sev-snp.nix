{ pkgs }:

with pkgs;
qemu_full.overrideAttrs (new: old: {
  src = fetchFromGitHub {
    owner = "AMDESE";
    repo = "qemu";
    # branch: snp-v3
    rev = "3b6a2b6b7466f6dea53243900b7516c3f29027b7";
    sha256 = "sha256-g93Q5mEcgNsWuxqXYyH5ipogXWBjtUDV/UZZLaBVGeU=";
    fetchSubmodules = true;
  };
  dontStrip = true;
  gtkSupport = false;
  dontWrapGapps = true;
  configureFlags = old.configureFlags ++ [
    "--disable-strip"
    "--disable-gtk"
    "--target-list=x86_64-softmmu"
    # "--enable-debug"
    # requires libblkio build
    # "--enable-blkio"
  ];

  # NOTE: The compiled binary is wrapped. (gtkSuppor=false does not prevent wrapping. why?)
  # The actual binary is ./result/bin/.qemu-system-x86_64-wrapped
})
