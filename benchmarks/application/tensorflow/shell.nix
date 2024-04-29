let
  nixpkgs = fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-23.11";
  pkgs = import nixpkgs { config = {}; overlays = []; };
in pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (pypkgs: [
      pypkgs.tensorflow
      pypkgs.keras
    ]))
    pkgs.wget
    pkgs.unzip
    pkgs.just
    pkgs.git
    pkgs.numactl
  ];
  shellHook = ''cd "${toString ./.}"'';
}
