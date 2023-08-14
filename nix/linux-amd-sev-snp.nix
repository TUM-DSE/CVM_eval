{ 
  fetchFromGitHub
, buildLinux
, ...
}@args:

let
  snp_latest =
  {
    owner = "AMDESE";
    repo = "linux";
    rev = "ad9c0bf475ecde466a065af44fc94918f109c4c9";
    sha256 = "sha256-cAgiVA7bKuFteF/GaklTm1M6SkDN61LpPBNhflN1M1o=";
    version = "6.5";
    modDirVersion = "6.5.0-rc2";
    extraPatches = [ ];
  };
  snp_kernel = snp_latest;
in
with snp_kernel;
buildLinux
(
  args // rec
  {
    inherit version;
    inherit modDirVersion;

    src = fetchFromGitHub { inherit owner repo rev sha256; };
    kernelPatches = [
    {
      name = "amd_sme-config";
      patch = null;
      extraConfig = ''
        AMD_MEM_ENCRYPT y
        CRYPTO_DEV_CCP y
        CRYPTO_DEV_CCP_DD m
        CRYPTO_DEV_SP_PSP y
        KVM_AMD_SEV y
        MEMORY_FAILURE y
        EXPERT y
      '';
    }
  ] ++ extraPatches;
  extraMeta.branch = version;
  ignoreConfigErrors = true;

  } // (args.argsOverride or { })
)
