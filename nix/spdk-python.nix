{
  pkgs
  , lib
  , stdenv
  , fetchFromGitHub
  , fetchurl
}:

let
  pythonPackages = pkgs.python310Packages;
in
pythonPackages.buildPythonPackage rec
{
  name = "spdk-python";
  version = "23.09";
  src = fetchFromGitHub
  {
    owner = "spdk";
    repo = "spdk";
    rev = "v${version}";
    sha256 = "sha256-P10NDa+MIEY8B3bu34Dq2keyuv2a24XV5Wf+Ah701b8=";
    fetchSubmodules = true;
  };
  propagatedBuildInputs = with pythonPackages;
  [
    setuptools
  ];
  sourceRoot = "${src.name}/python";
  doCheck = false;
}
