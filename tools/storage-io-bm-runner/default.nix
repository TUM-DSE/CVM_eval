with import <nixpkgs> {};

let
  pythonPackages = python310Packages;
in pkgs.mkShell rec {
  name = "ioPythonEnv";
  venvDir = "./.venv";
  buildInputs = [
    pythonPackages.python
    pythonPackages.venvShellHook
    # benchmarking
    fio
    # man pages
    man
  ];
  postVenvCreation = ''
    unset SOURCE_DATE_EPOCH
    pip3 install --upgrade pip3
    pip3 install -r requirements.txt
  '';
  postShellHook = ''
    unset SOURCE_DATE_EPOCH
  '';
}
