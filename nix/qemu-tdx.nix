{ pkgs }:

with pkgs;
qemu_full.overrideAttrs (new: old: {
  src = fetchFromGitHub {
    owner = "qemu";
    repo = "qemu";
    # tag: v10.1.0
    rev = "f8b2f64e2336a28bf0d50b6ef8a7d8c013e9bcf3";
    sha256 = "sha256-z9+bjpQDTQPN/Uv36hRmwS6mJlcmjuswvy/FMiAHQUw=";
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
  version = "10.1.0";
  dontStrip = true;
  gtkSupport = false;
  dontWrapGapps = true;
  enableDocs = false;
  configureFlags = old.configureFlags ++ [
    "--disable-strip"
    "--disable-gtk"
    "--target-list=x86_64-softmmu"
    "--disable-docs"
    # "--enable-debug"
    # requires libblkio build
    # "--enable-blkio"
  ];
  outputs = [ "out" "ga" ];

  # no patch
  patches = [ ];

  # NOTE: The compiled binary is wrapped. (gtkSupport=false does not prevent wrapping. why?)
  # The actual binary is ./result/bin/.qemu-system-x86_64-wrapped
})
