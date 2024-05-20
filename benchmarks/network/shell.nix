with import <nixpkgs> { };

mkShell {
  buildInputs = [
    nginx
    wrk
    just
    memtier-benchmark
    redis
    memcached
  ];
  # nix-shell ./path/to/shell.nix automatically cd's into the directory
  shellHook = ''cd "${toString ./.}"'';
}
