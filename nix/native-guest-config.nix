{ pkgs
, lib
}:
let
  linuxPackages = pkgs.linuxPackages_6_4;
in
{
  imports =
  [
    ({ config, ...}: {})
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
  ];

  # set kernel
  boot.kernelPackages = lib.mkForce linuxPackages;

  # execute upon start up
  # TODO: parameterize w/ io_uring
  # TODO: change for polling ; creates log file right away, not only after completion
  # issue for polling
  systemd.services.fio-runner =
  {
    description = "execute fio benchmark";
    script =
    ''
      /run/current-system/sw/bin/fio /mnt/blk-bm.fio \
        --output=/mnt/bm-result.log
    '';
    wantedBy = [ "multi-user.target" ]; # starts after login
  };

  # for bounce buffer test
  boot.kernelParams = [ "swiotlb=force" ];
}
