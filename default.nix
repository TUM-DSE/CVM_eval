with import <nixpkgs> { };
let
  libraries = [ libslirp pixman zlib zstd glib libpng snappy libuuid ];
in
mkShell {
  buildInputs = libraries;
  nativeBuildInputs = [
    # needed to compile qemu 
    ninja
    gnumake
    flex
    bison
    # needed to build ovmf
    pkg-config
    nasm
    acpica-tools
    # needed for the first demo
    gdb
    # needed to run cpuid
    cpuid
    # benchmarking and visualization
    fio
    jupyter
    python310Packages.seaborn
  ];
  LD_LIBRARY_PATH = lib.makeLibraryPath libraries;
}
