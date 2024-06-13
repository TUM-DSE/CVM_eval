{ pkgs }:

with pkgs;
OVMF.fd.overrideAttrs (old: {
  src = fetchFromGitHub {
    owner = "coconut-svsm";
    repo = "edk2";
    # branch "svsm"
    rev = "d965a1bd3d331e4b422526368e832f3d327fd0da";
    sha256 = "sha256-IccWhaVJBSupaO6iBTyno9vx9XbAssBOxkejlg6X6Dc=";
    fetchSubmodules = true;
  };
  patches = (old.patches or [ ]) ++ [
    # to record boot events
    ./patches/ovmf-event-record.patch
  ];
})
