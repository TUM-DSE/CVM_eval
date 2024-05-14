with import <nixpkgs> { };

mkShell {
  buildInputs = [
    memtier-benchmark
    redis
    memcached
    htop
    just
  ];
  # nix-shell ./path/to/shell.nix automatically cd's into the directory
  shellHook = ''cd "${toString ./.}"'';
}
