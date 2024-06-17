let
  # 23.11
  #nixpkgs = fetchTarball "https://github.com/NixOS/nixpkgs/archive/9ddcaffecdf098822d944d4147dd8da30b4e6843.tar.gz";
  nixpkgs = builtins.fetchGit {
    name = "23.11";
    url = "https://github.com/NixOS/nixpkgs";
    ref = "refs/heads/nixos-23.11";
    rev = "9ddcaffecdf098822d944d4147dd8da30b4e6843";
  };
  pkgs = import nixpkgs { config = { }; overlays = [ ]; };
  memcached_ktls = pkgs.memcached.overrideAttrs (new: old: {
    nameSuffix = "-ktls";
    buildInputs = old.buildInputs ++ [
      pkgs.openssl
    ];
    configureFlags = old.configureFlags ++ [
      "--enable-tls"
      "--enable-ktls"
    ];
  });
in
pkgs.mkShell {
  buildInputs = [
    memcached_ktls
    pkgs.memtier-benchmark
    pkgs.redis
    pkgs.nginx
    pkgs.wrk
    pkgs.just
  ];
  # nix-shell ./path/to/shell.nix automatically cd's into the directory
  shellHook = ''cd "${toString ./.}"'';
}
