{ pkgs ? (import <nixpkgs> {
    config.allowUnfree = true;
  })
, ...
}:
pkgs.mkShell {
  packages = [
    pkgs.steam-run
  ];
}
