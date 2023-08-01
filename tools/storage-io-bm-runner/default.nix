with import <nixpkgs> {};

let
  pythonPackages = python310Packages;
in pkgs.mkShell rec {
  name = "ioPythonEnv";
  buildInputs = [
    pythonPackages.python
    pythonPackages.click
    # benchmarking
    fio
    # man pages
    man
    # cryptsetup
    cryptsetup
  ];
}
