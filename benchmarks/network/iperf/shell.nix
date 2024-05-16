with import <nixpkgs> { };

mkShell {
  buildInputs = [
    htop
    just
  ];
  # nix-shell ./path/to/shell.nix automatically cd's into the directory
  shellHook = ''cd "${toString ./.}"'';
}
