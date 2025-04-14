{ pkgs }:

with pkgs;
qemu_full.overrideAttrs (new: old: {
  src = fetchFromGitHub {
    owner = "THS-on";
    repo = "qemu";
    # branch: snp-latest-fixed
    rev = "f4438fbfa88297e65427f529bcb95f463aa9b058";
    sha256 = "sha256-nLG8inAsftwOdg8azZv9gxkNlQionXllAENCZM4mhWU";
    # branch: snp-latest-20231110
    #rev = "fe4c9e8e7e7ddac4b19c4366c1f105ffc4a78482";
    #sha256 = "sha256-51BEYF7P5GteCrWOp7nKPjUDxXFq8KDxMAC5f5TNO2I=";
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
  patches = [];
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
