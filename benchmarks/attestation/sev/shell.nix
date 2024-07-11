{ pkgs ? import <nixpkgs> { } }:
let
  pythonEnv = pkgs.python3.withPackages (ps: [
    ps.pandas
    ps.pexpect
    ps.matplotlib
    ps.pyopenssl
  ]);
  fenix = pkgs.callPackage
    (pkgs.fetchFromGitHub {
      owner = "nix-community";
      repo = "fenix";
      # commit from: 2024-07-03
      rev = "aec88e528fb93a3b6381905a3d54ce89d07b6df9";
      hash = "sha256-RKKOQ5LxhSh6VCuLr5HsLUF2JWQqFeiPiQ3zSkEtBXg=";
    })
    { };
  libraries = [ pkgs.zlib pkgs.glib ];
in
pkgs.mkShell {
  buildInputs = libraries;
  nativeBuildInputs = [
    pkgs.pkg-config
    pkgs.openssl
    pkgs.git
    pkgs.gnumake

    #for the snpguest -- rust nightly is required
    # cargo
    # rustup
    # Note: to use stable, just replace `default` with `stable`
    fenix.default.toolchain
  ];

  # make install strips valueable libraries from our rpath
  LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath libraries;
  shellHook = ''
    export PATH=${pythonEnv}/bin:$PATH
  '';

  # Set Environment Variables
  RUST_BACKTRACE = 1;
}
