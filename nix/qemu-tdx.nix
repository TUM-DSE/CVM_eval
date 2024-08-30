{ pkgs }:

with pkgs;
qemu_full.overrideAttrs (new: old: {
  src = fetchFromGitHub {
    owner = "intel-staging";
    repo = "qemu-tdx";
    # branch: tdx-qemu-upstream
    #rev = "97d7eee4450ca607d36acd2bb1d6137d193687cc";
    #sha256 = "sha256-XecX9ZpJCVCYjUwGAXuoJJl3bAVsG+a91hwugzWCrQI=";
    # branch: tdx-qemu-next
    rev = "7a97b8940d938d0d5740c0513c9acf0053c6cb85";
    sha256 = "sha256-GoxklxWLuXXG60y6Z6UunV+S+0PH4RBJht4vJ740CEY=";
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

  # NOTE: The compiled binary is wrapped. (gtkSuppor=false does not prevent wrapping. why?)
  # The actual binary is ./result/bin/.qemu-system-x86_64-wrapped
})
