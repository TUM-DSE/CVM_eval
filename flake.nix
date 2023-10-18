{
  description = "CVM-IO - a storage-IO performance enhancing CVM method";

  inputs =
  {
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixpkgs-stable.url = "github:NixOS/nixpkgs/nixos-23.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = 
  {
    self
    , nixpkgs-unstable
    , nixpkgs-stable
    , flake-utils
  }:
  (
    flake-utils.lib.eachSystem ["x86_64-linux"]
    (
      system:
      let
        pkgs = nixpkgs-unstable.legacyPackages.${system};
        stablepkgs = nixpkgs-stable.legacyPackages.${system};
        make-disk-image = import (pkgs.path + "/nixos/lib/make-disk-image.nix");
        selfpkgs = self.packages.x86_64-linux;
      in
      rec {
        packages =
        {
          # SSD preconditioning
          spdk = pkgs.callPackage ./nix/spdk.nix { inherit pkgs; };
          spdkPython = pkgs.callPackage ./nix/spdk-python.nix { inherit pkgs; };

          qemu-amd-sev-snp = let pkgs = stablepkgs; in pkgs.callPackage ./nix/qemu-amd-sev-snp.nix { inherit pkgs; };
          # only need AMD kernel fork on host, not in guest
          # linux-amd-sev-snp = pkgs.callPackage ./nix/linux-amd-sev-snp.nix { inherit pkgs; };
          ovmf-amd-sev-snp = pkgs.callPackage ./nix/ovmf-amd-sev-snp.nix { inherit pkgs; };
          guest-image = make-disk-image
          {
            config = self.nixosConfigurations.native-guest.config;
            inherit (pkgs) lib;
            inherit pkgs;
            format = "qcow2";
            partitionTableType = "efi";
            installBootLoader = true;
            diskSize = 4096;
            OVMF = selfpkgs.ovmf-amd-sev-snp.fd;
            touchEFIVars = true;
            contents =
            [
              {
                source = ./bm/blk-bm.fio;
                target = "/mnt/blk-bm.fio";
              }
              {
                source = ./bm/io_uring-bm.fio;
                target = "/mnt/io_uring-bm.fio";
              }
            ];
          };
        };

        devShells.default = pkgs.mkShell
        {
          name = "benchmark-devshell";
          buildInputs = with pkgs;
          [
            just
            fzf
            # spdk # for nvme_mange -> SSD precondition
            fio
          ] ++ 
          (
            with self.packages.${system};
            [
              qemu-amd-sev-snp # patched amd-sev-snp qemu
              spdk # nvme SSD formatting
              spdkPython
            ]
          );
        };
      }
    )
  ) //
  {
    nixosConfigurations = let
      pkgs = nixpkgs-unstable.legacyPackages.x86_64-linux;
    in
    {
      native-guest = nixpkgs-unstable.lib.nixosSystem
      {
        system = "x86_64-linux";
        modules =
        [
          (
            import ./nix/native-guest-config.nix
            {
              inherit pkgs;
              inherit (nixpkgs-unstable) lib;
            }
          )
          ./nix/nixos-generators-qcow.nix
        ];
      };
    };
  };
}
