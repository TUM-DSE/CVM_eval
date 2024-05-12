# XXX: WIP

{ pkgs }:

with pkgs;
qemu_full.overrideAttrs (new: old: {
  src = fetchFromGitHub {
    owner = "intel-staging";
    repo = "qemu-tdx";
    # branch: tdx-qemu-upstream
    rev = "97d7eee4450ca607d36acd2bb1d6137d193687cc";
    sha256 = "sha256-XecX9ZpJCVCYjUwGAXuoJJl3bAVsG+a91hwugzWCrQI=";
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

  # no patch
  patches = [ ];

  dontUseMesonConfigure = true;

  # NOTE: The compiled binary is wrapped. (gtkSuppor=false does not prevent wrapping. why?)
  # The actual binary is ./result/bin/.qemu-system-x86_64-wrapped
})
