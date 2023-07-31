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
    # cryptsetup
    cryptsetup
  ];
  postVenvCreation = ''
    unset SOURCE_DATE_EPOCH
    pip3 install --upgrade pip3
    pip3 install -r requirements.txt
  '';
    # for generic: nixpkgs - libm
  postShellHook = ''
    unset SOURCE_DATE_EPOCH
    export LD_LIBRARY_PATH="${lib.makeLibraryPath [ stdenv.cc.cc.lib ]}"
  '';
}
