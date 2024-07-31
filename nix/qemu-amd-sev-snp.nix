{ pkgs }:

with pkgs;
qemu_full.overrideAttrs (new: old: {
  src = fetchFromGitHub {
    owner = "mmisono";
    repo = "qemu";
    # branch: snp-latest-20240515
    #rev = "fb924a5139bff1d31520e007ef97b616af1e22a1";
    #sha256 = "sha256-U8OnhfPa3vV5fbLMZBiBw4GJSZRVnZbmFV6gYntpdk0=";
    # branch: snp-latest-20240221
    rev = "f246dd2ad51d2c6c3ce9a588a8ce9c6a2d8c20e1";
    sha256 = "sha256-LxJ/utvWne/yDxJnJhw5Un5kH5eEPUoxt32fZOOoWLk=";
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
  patches = [ ];
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
