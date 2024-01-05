{
  description = "CVM-IO - a storage-IO performance enhancing CVM method";

  inputs =
  {
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixpkgs-stable.url = "github:NixOS/nixpkgs/nixos-23.05";
    nixpkgs-2311.url = "github:NixOS/nixpkgs/nixos-23.11";
    nixpkgs-mic92.url = "github:mic92/nixpkgs/spdk";
    flake-utils.url = "github:numtide/flake-utils";
    # debug build inputs
    kernelSrc.url = "path:/home/robert/repos/github.com/TUM_DSE/CVM_eval/src/linux";
    kernelSrc.flake = false;
  };

  outputs = 
  {
    self
    , nixpkgs-unstable
    , nixpkgs-stable
    , nixpkgs-2311
    , nixpkgs-mic92
    , flake-utils
    , kernelSrc
  }:
  (
    flake-utils.lib.eachSystem ["x86_64-linux"]
    (
      system:
      let
        nixpkgs-direct = nixpkgs-unstable;
        pkgs = nixpkgs-unstable.legacyPackages.${system};
        stablepkgs = nixpkgs-stable.legacyPackages.${system};
        pkgs-2311 = nixpkgs-2311.legacyPackages.${system};
        mic92pkgs = nixpkgs-mic92.legacyPackages.${system};
        make-disk-image = import (pkgs.path + "/nixos/lib/make-disk-image.nix");
        selfpkgs = self.packages.x86_64-linux;
        python3 = nixpkgs-unstable.legacyPackages.${system}.python3;
      in
      rec {
        packages =
        {
          # SSD preconditioning
          spdk = let pkgs = mic92pkgs; in pkgs.callPackage ./nix/spdk.nix { inherit pkgs; };

          qemu-amd-sev-snp = let pkgs = stablepkgs; in pkgs.callPackage ./nix/qemu-amd-sev-snp.nix { inherit pkgs; };
          ovmf-amd-sev-snp = pkgs.callPackage ./nix/ovmf-amd-sev-snp.nix { inherit pkgs; };
          guest-image = make-disk-image
          {
            config = self.nixosConfigurations.native-guest.config;
            inherit (pkgs) lib;
            inherit pkgs;
            format = "qcow2";
            partitionTableType = "efi";
            installBootLoader = true;
            diskSize = 8192;
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

          # debug kernel
          # inv uilts.py:nixos-image
          nixos-image = pkgs.callPackage ./nix/nixos-image.nix { };
          lib.nixpkgsRev = nixpkgs-direct.shortRev;
          # build config from prebuilt kernel
        };

        devShells = {
          default = pkgs.mkShell
          {
            name = "benchmark-devshell";
            buildInputs =
            let
              count-vm-exits = pkgs.callPackage ./nix/bin/count_vm_exits.nix { inherit pkgs; };
            in
            with pkgs;
            [
              python3
              python3.pkgs.invoke
              just
              fzf
              # add again once upstreamed
              # spdk # for nvme_mange -> SSD precondition
              fio
              cryptsetup
              bpftrace
              linux.dev
              gdb
            ] ++ 
            (
              with self.packages.${system};
              [
                qemu-amd-sev-snp # patched amd-sev-snp qemu
                spdk # nvme SSD formatting
              ]
            ) ++
            (
              [
                count-vm-exits
              ]
            );
          };
          linux = pkgs-2311.linux.dev;
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
              inherit kernelSrc;
            }
          )
          ./nix/nixos-generators-qcow.nix
        ];
      };
    };
  };
}
