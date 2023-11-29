{
  description = "CVM-IO - a storage-IO performance enhancing CVM method";

  inputs =
  {
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixpkgs-stable.url = "github:NixOS/nixpkgs/nixos-23.05";
    nixpkgs-mic92.url = "github:mic92/nixpkgs/spdk";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = 
  {
    self
    , nixpkgs-unstable
    , nixpkgs-stable
    , nixpkgs-mic92
    , flake-utils
  }:
  (
    flake-utils.lib.eachSystem ["x86_64-linux"]
    (
      system:
      let
        pkgs = nixpkgs-unstable.legacyPackages.${system};
        stablepkgs = nixpkgs-stable.legacyPackages.${system};
        mic92pkgs = nixpkgs-mic92.legacyPackages.${system};
        make-disk-image = import (pkgs.path + "/nixos/lib/make-disk-image.nix");
        selfpkgs = self.packages.x86_64-linux;
        python3 = nixpkgs-unstable.legacyPackages.${system}.python3;
      in
      rec {
        packages =
        {
          # SSD preconditioning
          spdk-libvfio-user = let pkgs = mic92pkgs; in pkgs.callPackage ./nix/spdk-libvfio-user.nix { inherit pkgs; };
          spdk = let pkgs = mic92pkgs; spdk-libvfio-user = selfpkgs.spdk-libvfio-user; in pkgs.callPackage ./nix/spdk.nix { inherit pkgs; inherit spdk-libvfio-user; };

          #qemu-amd-sev-snp = let pkgs = stablepkgs; in pkgs.callPackage ./nix/qemu-amd-sev-snp.nix { inherit pkgs; };
          qemu-amd-sev-snp = pkgs.callPackage ./nix/qemu-amd-sev-snp.nix { inherit pkgs; };
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
            ];
          };
        };

        devShells.default = pkgs.mkShell
        {
          name = "benchmark-devshell";
          buildInputs = with pkgs;
          [
            python3
            just
            fzf
            # add again once upstreamed
            # spdk # for nvme_mange -> SSD precondition
            fio
            cryptsetup
            bpftrace
          ] ++ 
          (
            with self.packages.${system};
            [
              qemu-amd-sev-snp # patched amd-sev-snp qemu
              spdk-libvfio-user
              spdk # nvme SSD formatting
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
