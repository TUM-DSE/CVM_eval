{ pkgs }:

with pkgs;
qemu_full.overrideAttrs (new: old: {
  src = fetchFromGitHub {
    owner = "gierens";
    repo = "qemu-tdx-canonical";
    # branch: master
    rev = "1d4b179dc86bf1695f80175b2ea92d99bf2137b8";
    sha256 = "sha256-eRKGiqK95jAzAYYk+oSS0vJ1UiMeN5FVTwDscMM1Ieg=";
    fetchSubmodules = true;
    postFetch = ''
      cd "$out"
      (
        for p in subprojects/*.wrap; do
            ${pkgs.meson}/bin/meson subprojects download "$(basename "$p" .wrap)"
            rm -rf subprojects/$(basename "$p" .wrap/.git)
        done
      )
      find subprojects -type d -name .git -prune -execdir rm -r {} +
    '';
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

  # NOTE: The compiled binary is wrapped. (gtkSupport=false does not prevent wrapping. why?)
  # The actual binary is ./result/bin/.qemu-system-x86_64-wrapped
})
