{
  pkgs
  , lib
  , kernelSrc
  , selfpkgs
  , ...
}:
let
  src = kernelSrc;
  buildRoot = kernelSrc;
in
let
  kernelVersion =
    let s = lib.removeSuffix "\n"
            (builtins.readFile "${buildRoot}/include/config/kernel.release");
    in builtins.trace "kernelVersion: ${s}" s;
  version = lib.concatStringsSep "."
  [
    (lib.versions.majorMinor kernelVersion)
    (lib.versions.patch kernelVersion)
  ];
in
let
  # linux = pkgs.callPackage ./deps/cvm_io_linux.nix {};
  # linuxPackages = pkgs.recurseIntoAttrs (pkgs.linuxPackagesFor linux);
  prebuiltKernel = pkgs.callPackage ./deps/kernel_install.nix { inherit src buildRoot version kernelVersion; };
  prebuiltLinuxPackages = pkgs.linuxPackagesFor prebuiltKernel;
in
{
  imports =
  [
    # ({ config, ...}: {})
    # ./modules/encrypt.nix
    # ./modules/fio-runner.nix
  ];

  services.sshd.enable = true;
  programs.direnv.enable = true;

  networking.hostName = "native-guest";
  networking.firewall.enable = false;
  # networking.firewall.allowedTCPPorts = [22];

  users.users.root.password = "password";
  services.openssh.settings.PermitRootLogin = lib.mkDefault "yes";
  users.users.root.openssh.authorizedKeys.keys =
  [
    (builtins.readFile ./ssh_key.pub)
  ];
  services.getty.autologinUser = lib.mkDefault "root";
  time.timeZone = "Europe/Berlin";
  i18n.defaultLocale = "en_US.UTF-8";
  console = {
    font = "Lat2-Terminus16";
    keyMap = "us";
  };
  system.stateVersion = "23.11";

  nix.extraOptions =
  ''
    experimental-features = nix-command flakes
  '';
  nix.package = pkgs.nixFlakes;
  environment.systemPackages = with pkgs;
  [
    git
    fio
    cryptsetup
    trace-cmd
    bpftrace
    blktrace
    vim
    tmux
    fzf
    xterm # for `resize`, if vim messes up serial console size
  ] ++
  ( with selfpkgs;
    [
      bm-cpuid
    ]
  );

  # set kernel
  boot.kernelPackages = lib.mkForce prebuiltLinuxPackages;
  # if non-prebuilt ; TODO: make option
  # boot.kernelPackages = lib.mkForce linuxPackages;


  # boot.kernelParams = [ "virtio_blk.cvm_io_driver_name=virtio2" ];
  # boot.kernelParams = [ "swiotlb=force" ];

#  programs.fio-runner =
#  {
#    enable = true;
#    encrypted-run = true;
#    bounce-buffer = false;
#  };

}
