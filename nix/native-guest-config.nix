{
  pkgs
, lib
}:
let
  linux = pkgs.callPackage ./deps/cvm_io_linux.nix {};
  linuxPackages = pkgs.recurseIntoAttrs (pkgs.linuxPackagesFor linux);
in
{
  imports =
  [
    # ({ config, ...}: {})
    # ./modules/encrypt.nix
    ./modules/fio-runner.nix
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
  system.stateVersion = "23.05";

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
  ];

  # set kernel
  boot.kernelPackages = lib.mkForce linuxPackages;

  programs.fio-runner =
  {
    enable = false;
    encrypted-run = true;
    bounce-buffer = true;
  };

}
