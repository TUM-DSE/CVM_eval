{ linuxManualConfig, buildPackages, src, buildRoot, version, kernelVersion, ...}:
let
  modDirVersion = kernelVersion;
in
(linuxManualConfig {
  inherit src version modDirVersion;
  configfile = "${buildRoot}/.config";
  allowImportFromDerivation = true;
}).overrideAttrs (attrs: attrs // {
  dontStrip = true;
  phases = [ "buildPhase" "installPhase"] ;
  nativeBuildInputs = [ buildPackages.kmod ] ++ attrs.nativeBuildInputs;

  buildPhase = ''
      export buildRoot="$(pwd)/build"
      cp -r ${buildRoot} $buildRoot
      chmod +rw -R $buildRoot
      rm $buildRoot/Makefile
      echo "include ${src}/Makefile" > $buildRoot/Makefile
      actualModDirVersion="$(cat $buildRoot/include/config/kernel.release)"
      if [ "$actualModDirVersion" != "${modDirVersion}" ]; then
        echo "Error: modDirVersion ${modDirVersion} specified in the Nix expression is wrong, it should be: $actualModDirVersion"
        exit 1
      fi
      cd $buildRoot
    '';
  postInstall =
  ''
    if [ -z "''${dontStrip-}" ]; then
      installFlagsArray+=("INSTALL_MOD_STRIP=1")
    fi
    make modules_install $makeFlags "''${makeFlagsArray[@]}" \
      $installFlags "''${installFlagsArray[@]}"
    unlink $out/lib/modules/${modDirVersion}/build
    rm -rf $out/lib/modules/${modDirVersion}/source
    '';
  outputs = [ "out" ];
})
