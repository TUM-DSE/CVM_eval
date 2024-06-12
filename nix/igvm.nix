{ pkgs, ... }: pkgs.rustPlatform.buildRustPackage rec {
  name = "igvm";
  src = pkgs.fetchFromGitHub {
    owner = "Sabanic-P";
    repo = "igvm";
    rev = "ced26aaf2666dcb1efa1e2f60da6c36f6cde3f9d";
    sha256 = "sha256-oyOMS7kkbxBi04QIM/rZ7IKwtC8B7OYA4nIf9ms84Iw=";
  };

  cargoLock = {
    lockFile = src + "/Cargo.lock";
  };

  nativeBuildInputs = with pkgs; [
    rust-cbindgen
  ];
  buildInputs = with pkgs; [
    cunit
  ];

  buildPhase = ''
    make -f igvm_c/Makefile
  '';
  installPhase = ''
    PREFIX="" DESTDIR=$out make -f igvm_c/Makefile install
  '';
}
