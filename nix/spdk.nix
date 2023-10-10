{
  pkgs
  , lib
  , stdenv
  , fetchFromGitHub
  , fetchurl
}:

let
  dpdk' = pkgs.dpdk.overrideAttrs
  ( old: rec
    {
      version = "23.07";
      dpdkVersion = "23.07";
      src = fetchurl
      {
        url = "https://fast.dpdk.org/rel/dpdk-${dpdkVersion}.tar.xz";
        sha256 = "sha256-4IYU6K65KUB9c9cWmZKJpE70A0NSJx8JOX7vkysjs9Y=";
      };
    }
  );
in
stdenv.mkDerivation rec
{
  pname = "spdk";
  version = "23.09";

  src = fetchFromGitHub
  {
    owner = "spdk";
    repo = "spdk";
    rev = "v${version}";
    sha256 = "sha256-P10NDa+MIEY8B3bu34Dq2keyuv2a24XV5Wf+Ah701b8=";
    fetchSubmodules = true;
  };

  buildInputs = with pkgs;
  [
    cunit
    libaio
    libbsd
    libuuid
    numactl
    openssl
    ncurses
    pkg-config
    zlib
    libpcap
    libnl
    libelf
    jansson
    # meson # including meson breaks the build
    ps
  ];

  nativeBuildInputs = with pkgs;
  [
    (python310Full.withPackages (p: with p ; [ setuptools ]))
  ];

  patches =
  [
    # building python breaks the install
    # instead, build via buildPythonPackage in nix/spdk-python.nix
    ./0001-no-python-in-makefile.patch
  ];

  postPatch =
  ''
    patchShebangs . # $(ls | tr -d "python|scripts" | xargs)

    # glibc-2.36 adds arc4random, so we don't need the custom implementation
    # here anymore. Fixed upstream in https://github.com/spdk/spdk/commit/43a3984c6c8fde7201d6c8dfe1b680cb88237269,
    # but the patch doesn't apply here.
    sed -i -e '1i #define HAVE_ARC4RANDOM 1' lib/iscsi/iscsi.c
  '';

  enableParallelBuilding = true;

  configureFlags = with pkgs;
  [
    "--with-dpdk=${dpdk'}"
    "--disable-tests"
    "--disable-unit-tests"
  ];

  env.NIX_CFLAGS_COMPILE = "-mssse3"; # Necessary to compile.
  # otherwise does not find strncpy when compiling
  NIX_LDFLAGS = "-lbsd";

  meta = with lib; {
    description = "Set of libraries for fast user-mode storage";
    homepage = "https://spdk.io/";
    license = licenses.bsd3;
    platforms =  [ "x86_64-linux" ];
    maintainers = with maintainers; [ orivej ];
  };

  # include setup.sh for spdk setup (e.g. hugepage allocation)
  # include nvme_manage for SSD preconditioning
  # as in: https://ci.spdk.io/download/events/2017-summit/08_-_Day_2_-_Kariuki_Verma_and_Sudarikov_-_SPDK_Performance_Testing_and_Tuning_rev5_0.pdf
  postInstall =
  ''
    cp ./build/examples/nvme_manage $out/bin/.
    cp ./build/examples/perf $out/bin/.
    cp ./scripts/setup.sh $out/bin/spdk-setup.sh
    # setup dependencies
    mkdir -p $out/scripts
    cp ./scripts/common.sh $out/scripts/common.sh
    cp ./scripts/spdk-gpt.py $out/scripts/spdk-gpt.py
    cp ./scripts/rpc.py $out/bin/.
  '';
}
