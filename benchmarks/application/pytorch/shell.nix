{ pkgs ? import <nixpkgs> { }, mypython ? null}:
let
  pyPackages = [
    "torch"
    "torchvision"
    "pillow"
  ];
  pyPackages' = (pypkgs: 
    (pkgs.lib.forEach pyPackages (package:
      pypkgs.${package}
    ))
  );
  mypython' = if mypython != null then mypython else pkgs.python3.withPackages pyPackages';
in
pkgs.mkShell {
  # keep function to generate the list of python packages available in this shells python
  inherit pyPackages;

  packages = [
    mypython'
    pkgs.wget
    pkgs.unzip
    pkgs.just
    pkgs.git
    pkgs.numactl
  ];
}
