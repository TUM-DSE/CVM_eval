let
  # 23.11
  #nixpkgs = fetchTarball "https://github.com/NixOS/nixpkgs/archive/9ddcaffecdf098822d944d4147dd8da30b4e6843.tar.gz";
  nixpkgs = builtins.fetchGit {
    name = "23.11";
    url = "https://github.com/NixOS/nixpkgs";
    rev = "9ddcaffecdf098822d944d4147dd8da30b4e6843";
    ref = "refs/heads/nixos-23.11";
  };
  pkgs = import nixpkgs { config = { }; overlays = [ ]; };
in
pkgs.mkShell {
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
