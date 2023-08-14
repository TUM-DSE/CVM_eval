with import <nixpkgs> {};

let
  pythonPackages = python310Packages;
in pkgs.mkShell rec {
  name = "ioPythonEnv";
  buildInputs = [
    pythonPackages.python
    pythonPackages.click
    python310Packages.seaborn
    python310Packages.pandas
    python310Packages.binary
  ];
}
