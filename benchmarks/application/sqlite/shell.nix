let
  nixpkgs = fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-23.11";
  pkgs = import nixpkgs { config = { }; overlays = [ ]; };
  kvtest = pkgs.stdenv.mkDerivation {
    name = "kvtest";
    src = pkgs.fetchFromGitHub {
      owner = "sqlite";
      repo = "sqlite";
      # Version 3.45.1
      rev = "189e44dfecdc7868bb860dfb5d98eab371318c37";
      sha256 = "sha256-4xfggk6pnfX0Kogo4+3Q8Wh3vrw8jcTdRCqaUDxCPZk=";
    };
    nativeBuildInputs = [ pkgs.tcl ];
    # SQLITE_DIRECT_OVERFLOW_READ
    # > When this option is present, content contained in overflow pages of
    # the database file is read directly from disk, bypassing the page cache,
    # during read transactions.
    buildPhase = ''
      ./configure
      make sqlite3.c
      $CC -O2 -o kvtest -I. -DSQLITE_DIRECT_OVERFLOW_READ \
        sqlite3.c test/kvtest.c
    '';
    installPhase = ''
      mkdir -p $out/bin
      cp kvtest $out/bin/
    '';
  };
in
pkgs.mkShell {
  packages = [
    kvtest
    pkgs.just
    pkgs.numactl
  ];
  # nix-shell ./path/to/shell.nix automatically cd's into the directory
  shellHook = ''cd "${toString ./.}"'';
}
