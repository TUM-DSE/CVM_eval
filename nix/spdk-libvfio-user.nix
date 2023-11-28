{ 
  pkgs
}:

with pkgs;
spdk.overrideAttrs
(
  new: old:
  {
    name = "spdk-libvfio-user";
    sourceRoot = "${old.src.name}/libvfio-user";
    configureFlags = [];
    patches = [];

    buildInputs = old.buildInputs ++
    [
      json_c
      cmocka
      meson
      ninja
    ];
  }

)
