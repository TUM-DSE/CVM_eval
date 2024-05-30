{ pkgs ? import <nixpkgs> { } }:
let
  memcached = pkgs.memcached.overrideAttrs (new: old: {
    buildInputs = old.buildInputs ++ [
      pkgs.openssl
    ];
    configureFlags = old.configureFlags ++ [
      "--enable-tls"
    ];
  });
in
pkgs.mkShell {
  packages = [
    memcached
    pkgs.memtier-benchmark
    pkgs.redis
    pkgs.nginx
    pkgs.wrk
    pkgs.just
  ];
}
