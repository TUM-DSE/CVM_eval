{ pkgs, igvm }:

with pkgs;

qemu_full.overrideAttrs (new: old: {
  src = builtins.fetchurl {
    url =
      "https://github.com/Sabanic-P/qemu/releases/download/v8.2.0-igvm/qemu8.2.0.tar.gz";
    sha256 =
      "sha256:15cmwlkiwd001hhbv8rcvdnsdgr092x2jvy15m9c3k4s7g36a7yh";
  };
  version = "8.2.0";
  buildInputs = old.buildInputs ++ [ igvm ];
  igvm = igvm;
  configureFlags = old.configureFlags ++ [
    "--target-list=x86_64-softmmu"
    "--disable-gtk"
    "--disable-sdl"
    "--disable-sdl-image"
    "--enable-igvm"
  ];
})
#qemu_full.overrideAttrs (new: old: {
#  src = fetchFromGitHub {
#    owner = "mmisono";
#    repo = "qemu";
#    # branch: snp-latest-20231110
#    rev = "fe4c9e8e7e7ddac4b19c4366c1f105ffc4a78482";
#    sha256 = "sha256-51BEYF7P5GteCrWOp7nKPjUDxXFq8KDxMAC5f5TNO2I=";
#    fetchSubmodules = true;
#  };
#  dontStrip = true;
#  gtkSupport = false;
#  dontWrapGapps = true;
#  configureFlags = old.configureFlags ++ [
#    "--disable-strip"
#    "--disable-gtk"
#    "--target-list=x86_64-softmmu"
#    # "--enable-debug"
#    # requires libblkio build
#    # "--enable-blkio"
#  ];
#
#  # NOTE: The compiled binary is wrapped. (gtkSuppor=false does not prevent wrapping. why?)
#  # The actual binary is ./result/bin/.qemu-system-x86_64-wrapped
#})
